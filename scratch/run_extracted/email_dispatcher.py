"""Fail-closed dispatcher for explicitly approved outreach and proposals."""

import argparse
import datetime as dt
import hashlib
import json
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv

if os.path.exists("/secrets/env/.env"):
    load_dotenv("/secrets/env/.env")
else:
    load_dotenv()

DAILY_SEND_LIMIT = 15
DEFAULT_APPROVAL_FILE = Path("approvals.local.json")
DEFAULT_DNC_FILE = Path("dnc.local.json")
DEFAULT_LEDGER_FILE = Path("sent_ledger.local.jsonl")


def _load_json(path, default):
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _message_hash(recipient, subject, body):
    payload = f"{recipient.strip().lower()}\n{subject.strip()}\n{body}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _parse_expiry(value):
    if not value:
        return None
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def _valid_approval(approvals, recipient, domain, message_hash):
    now = dt.datetime.now(dt.timezone.utc)
    required = {"G2", "G3"}
    matched = set()
    for approval in approvals:
        if approval.get("status") not in {"Approved", "Approved with Conditions"}:
            continue
        try:
            expires_at = _parse_expiry(approval.get("expires_at"))
        except (TypeError, ValueError):
            continue
        if not expires_at or expires_at <= now:
            continue
        if approval.get("recipient", "").strip().lower() != recipient.strip().lower():
            continue
        if approval.get("domain", "").strip().lower() != domain.strip().lower():
            continue
        if approval.get("message_sha256") != message_hash:
            continue
        gate = approval.get("gate_type")
        if gate in required:
            matched.add(gate)
    return required.issubset(matched), sorted(required - matched)


def _load_sent_hashes(path):
    if not path.exists():
        return set()
    hashes = set()
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                hashes.add(json.loads(line)["message_sha256"])
            except (json.JSONDecodeError, KeyError):
                continue
    return hashes


def dispatch_emails(execute=False, tenant="asheville", approval_file=DEFAULT_APPROVAL_FILE,
                    dnc_file=DEFAULT_DNC_FILE, ledger_file=DEFAULT_LEDGER_FILE):
    audit_file = Path(f"audit_results_{tenant}.json")
    if not audit_file.exists():
        print(f"[ERROR] {audit_file} not found. Run batch_audit_scanner.py first.")
        return False

    audits = _load_json(audit_file, [])
    approvals = _load_json(Path(approval_file), [])
    dnc_data = _load_json(Path(dnc_file), [])
    dnc = {str(item).strip().lower() for item in dnc_data}
    sent_hashes = _load_sent_hashes(Path(ledger_file))
    
    tenant_upper = tenant.upper()
    smtp_user = os.getenv(f"SMTP_USER_{tenant_upper}") or os.getenv("SMTP_USER")
    smtp_password = os.getenv(f"SMTP_PASSWORD_{tenant_upper}") or os.getenv("SMTP_PASSWORD")

    if execute and (not smtp_user or not smtp_password):
        print(f"[BLOCKED] Live execution requested for {tenant} but SMTP credentials are unavailable.")
        return False

    sent_count = 0
    blocked_count = 0
    for audit in audits:
        if sent_count >= DAILY_SEND_LIMIT:
            break
        if audit.get("status") != "AUDITED":
            continue
        domain = str(audit.get("domain", "")).strip().lower()
        emails = audit.get("contacts", {}).get("emails", [])
        if not domain or not emails:
            continue
        recipient = str(emails[0]).strip().lower()
        proposal_file = Path(f"proposals_{tenant}") / f"{domain.replace('.', '_')}_proposal.txt"
        if not proposal_file.exists():
            continue
        body = proposal_file.read_text(encoding="utf-8")
        subject = next((line.partition(":")[2].strip() for line in body.splitlines()
                        if line.startswith("Subject:")), "Website Optimization Proposal")
        digest = _message_hash(recipient, subject, body)

        if recipient in dnc or domain in dnc:
            print(f"[BLOCKED] DNC match for {domain}.")
            blocked_count += 1
            continue
        if digest in sent_hashes:
            print(f"[SKIP] Exact message already sent to {domain}.")
            continue
        approved, missing = _valid_approval(approvals, recipient, domain, digest)
        if not approved:
            print(f"[BLOCKED] {domain} lacks matching, unexpired approvals: {', '.join(missing)}.")
            blocked_count += 1
            continue
        if not execute:
            print(f"[DRY-RUN] Approved message would be sent to {domain}.")
            continue

        message = EmailMessage()
        message.set_content(body)
        message["Subject"] = subject
        message["From"] = smtp_user
        message["To"] = recipient
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(smtp_user, smtp_password)
                server.send_message(message)
        except Exception as exc:
            print(f"[ERROR] Send outcome uncertain for {domain}: {exc}. Do not retry automatically.")
            return False

        entry = {
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
            "recipient": recipient,
            "domain": domain,
            "message_sha256": digest,
        }
        with Path(ledger_file).open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")
        sent_hashes.add(digest)
        sent_count += 1
        print(f"[SENT] Approved message sent to {domain}.")

    print(f"[DONE] tenant={tenant} sent={sent_count} blocked={blocked_count} execute={execute}")
    return blocked_count == 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="Send only exactly approved messages.")
    parser.add_argument("--tenant", default="asheville", help="Tenant ID")
    parser.add_argument("--approval-file", default=str(DEFAULT_APPROVAL_FILE))
    parser.add_argument("--dnc-file", default=str(DEFAULT_DNC_FILE))
    parser.add_argument("--ledger-file", default=str(DEFAULT_LEDGER_FILE))
    args = parser.parse_args()
    raise SystemExit(0 if dispatch_emails(args.execute, args.tenant, args.approval_file, args.dnc_file, args.ledger_file) else 1)


if __name__ == "__main__":
    main()
