"""
Rebuild what is known of the outreach history from Gmail bounce notices.

On 2026-08-09 the sent ledger did not exist, yet bounce notices in
lexiconatlas@gmail.com proved that real outreach had gone out on 2026-08-03/04.
The system had no memory of contacting anyone. This reads the mailbox and
records what can still be proven, so the duplicate-send guard is not starting
from zero.

What it can and cannot recover
------------------------------
A bounce proves a message was sent to that address, so the recipient and the
approximate date are recoverable. The original message body is not, so the
message hash is not either. Reconstructed rows are therefore marked
`reconstructed: true` and carry no usable sha256 — they make the recipient
visible as previously-contacted without pretending to be a delivery receipt.

Addresses that hard-bounced are also suppressed: their mail servers refuse
connections, so further sends only burn reputation.

    python reconstruct_outreach_history.py              # show what it found
    python reconstruct_outreach_history.py --execute    # write it down
"""

import argparse
import base64
import re
import sys

from googleapiclient.discovery import build

import inbox_monitor
import outreach_ledger

QUERY = "from:mailer-daemon OR subject:'Delivery Status Notification'"
ADDRESS = re.compile(r"[\w.+-]+@[\w.-]+\.\w+")
IGNORED_DOMAINS = ("google.com", "gmail.com", "googlemail.com")


def text_parts(payload):
    chunks = []
    if payload.get("mimeType", "").startswith("text/plain"):
        data = payload.get("body", {}).get("data")
        if data:
            chunks.append(base64.urlsafe_b64decode(data).decode("utf-8", errors="replace"))
    for part in payload.get("parts", []) or []:
        chunks.extend(text_parts(part))
    return chunks


def failed_recipient(body):
    for candidate in ADDRESS.findall(body):
        if not any(candidate.lower().endswith(domain) for domain in IGNORED_DOMAINS):
            return candidate.lower()
    return ""


def collect():
    """Return {address: {'permanent': bool, 'first_seen': str, 'reason': str}}."""
    creds = inbox_monitor.authenticate_gmail()
    if not creds:
        raise SystemExit("[ERROR] could not authenticate to the agency mailbox")

    service = build("gmail", "v1", credentials=creds)
    listed = service.users().messages().list(userId="me", q=QUERY, maxResults=100).execute()

    found = {}
    for entry in listed.get("messages", []):
        message = service.users().messages().get(
            userId="me", id=entry["id"], format="full").execute()
        headers = {h["name"].lower(): h["value"] for h in message["payload"]["headers"]}
        body = "\n".join(text_parts(message["payload"]))
        address = failed_recipient(body)
        if not address:
            continue

        permanent = "Failure" in headers.get("subject", "")
        reason = next((line.strip()[:160] for line in body.splitlines()
                       if "did not accept" in line or "does not exist" in line
                       or "rejected" in line), "")
        record = found.setdefault(address, {
            "permanent": False,
            "first_seen": headers.get("date", ""),
            "reason": reason,
        })
        record["permanent"] = record["permanent"] or permanent
        if reason and not record["reason"]:
            record["reason"] = reason
    return found


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true",
                        help="Write the records. Without this, nothing is stored.")
    args = parser.parse_args()

    found = collect()
    if not found:
        print("No bounce notices found; nothing to reconstruct.")
        return 0

    # Firestore is requested explicitly here: the whole point of reconstructing
    # is to land the history where a cloud run can still see it. record_send
    # also appends to the local file, so both environments end up knowing.
    ledger = outreach_ledger.OutreachLedger(use_firestore=True, require_durable=False)
    backend = "Firestore + local files" if ledger.client() else "local files only"
    mode = "EXECUTE" if args.execute else "DRY RUN — nothing will be written"
    print(f"Backend: {backend}")
    print(f"Mode:    {mode}\n")

    for address, detail in sorted(found.items()):
        kind = "hard bounce" if detail["permanent"] else "delayed only"
        print(f"  {address}")
        print(f"    {kind}, first notice {detail['first_seen'][:22]}")
        if detail["reason"]:
            print(f"    reason: {detail['reason'][:100]}")

        if not args.execute:
            print("    [WOULD RECORD] previously contacted"
                  + (" + suppress" if detail["permanent"] else ""))
            continue

        # A bounce proves contact but not content, so there is no real message
        # hash. Use a stable synthetic id so re-running cannot duplicate a row.
        ledger.record_send(
            recipient=address,
            domain=address.split("@")[-1],
            message_sha256=f"reconstructed:{address}",
            timestamp=detail["first_seen"],
            note="Reconstructed from a bounce notice; original message body unknown.",
        )
        print("    [RECORDED] previously contacted")
        if detail["permanent"]:
            ledger.suppress(
                address,
                reason=f"Hard bounce. {detail['reason']}".strip(),
                source="reconstruct_outreach_history.py",
            )
            print("    [SUPPRESSED] hard bounce")

    print()
    if not args.execute:
        print("Re-run with --execute to write these records.")
    else:
        print("Done. Verify with: python email_dispatcher.py --tenant asheville")
    return 0


if __name__ == "__main__":
    sys.exit(main())
