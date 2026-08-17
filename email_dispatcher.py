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

# How many new approval requests may be staged into the workbook per run.
# Two reasons for a cap. A human one: 136 rows dumped into the Approval Queue is
# not a decision list, it is a wall, and the important rows get buried. And a
# mechanical one: each candidate costs a DNS lookup and up to two SMTP probes,
# so an uncapped run could spend twenty minutes on deliverability alone and hit
# the per-step timeout. A daily trickle is reviewable and bounded.
STAGING_LIMIT = 10
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


def _open_ledger(ledger_file, dnc_file):
    """
    The durable send/suppression record.

    Under Cloud Run the local files cannot survive the execution, so Firestore
    is mandatory there and an unreadable ledger stops the run. Locally the files
    are still authoritative.
    """
    import outreach_ledger

    return outreach_ledger.OutreachLedger(ledger_file=ledger_file, dnc_file=dnc_file)


def load_tenant_sheet_approvals(tenant):
    """
    Read owner decisions from the tenant's Approval Queue tab (and Master if available).
    """
    try:
        import yaml

        import agency_auth
        import sheet_approvals

        with open("tenants.yaml", "r", encoding="utf-8") as handle:
            config = yaml.safe_load(handle) or {}
            tenant_config = config.get("tenants", {}).get(tenant) or {}
            master_config = config.get("master", {})
            
        spreadsheet_id = tenant_config.get("spreadsheet_id")
        master_id = master_config.get("spreadsheet_id")
        
        all_approvals = []
        
        if spreadsheet_id:
            try:
                client = agency_auth.sheets_client(probe_spreadsheet_id=spreadsheet_id)
                worksheet = client.open_by_key(spreadsheet_id).worksheet("Approval Queue")
                approvals = sheet_approvals.load_sheet_approvals(worksheet, tenant=tenant)
                print(f"  [SHEET] loaded {len(approvals)} approved row(s) from the {tenant} Approval Queue.")
                all_approvals.extend(approvals)
            except Exception as e:
                print(f"  [WARN] Could not read sheet approvals for {tenant}: {e}")
                
        if master_id:
            try:
                client = agency_auth.sheets_client(probe_spreadsheet_id=master_id)
                worksheet = client.open_by_key(master_id).worksheet("Master Approval Queue")
                approvals = sheet_approvals.load_sheet_approvals(worksheet, tenant=tenant)
                print(f"  [SHEET] loaded {len(approvals)} approved row(s) from the Master Approval Queue for {tenant}.")
                all_approvals.extend(approvals)
            except Exception as e:
                print(f"  [WARN] Could not read master sheet approvals: {e}")
                
        return all_approvals
    except Exception as exc:
        print(f"  [WARN] Could not read sheet approvals for {tenant}: {exc}")
        return []


def stage_pending_approvals(tenant, items, run_id=""):
    """Write Pending rows for messages awaiting a decision to both city and master sheets."""
    try:
        import yaml

        import agency_auth
        import sheet_approvals

        with open("tenants.yaml", "r", encoding="utf-8") as handle:
            config = yaml.safe_load(handle) or {}
            tenant_config = config.get("tenants", {}).get(tenant) or {}
            master_config = config.get("master", {})
            
        spreadsheet_id = tenant_config.get("spreadsheet_id")
        master_id = master_config.get("spreadsheet_id")
        staged_count = 0
        
        if spreadsheet_id:
            try:
                client = agency_auth.sheets_client(probe_spreadsheet_id=spreadsheet_id)
                worksheet = client.open_by_key(spreadsheet_id).worksheet("Approval Queue")
                staged_count = sheet_approvals.stage_outreach_approvals(worksheet, items, run_id=run_id, tenant=tenant)
            except Exception as e:
                print(f"  [WARN] Could not stage approval rows for {tenant}: {e}")
                
        if master_id:
            try:
                client = agency_auth.sheets_client(probe_spreadsheet_id=master_id)
                worksheet = client.open_by_key(master_id).worksheet("Master Approval Queue")
                master_staged = sheet_approvals.stage_outreach_approvals(worksheet, items, run_id=run_id, tenant=tenant)
                if not staged_count:
                    staged_count = master_staged
            except Exception as e:
                print(f"  [WARN] Could not stage approval rows in master for {tenant}: {e}")
                
        return staged_count
    except Exception as exc:
        print(f"  [WARN] Could not stage approval rows for {tenant}: {exc}")
        return 0


def _result(error=None, sent=0, blocked=0, queued=0, undeliverable=0):
    """
    Outcome of one dispatcher run.

    `error` separates "something is broken" from "nothing was approved yet".
    That distinction matters because the same program serves two purposes: the
    daily pipeline stages decisions, where blocking is the normal and expected
    state, while a manual --execute run treats a block as noteworthy. Conflating
    them would make the daily summary show a failure every single day, which is
    how a team learns to ignore its own alarms.
    """
    return {"error": error, "sent": sent, "blocked": blocked,
            "queued": queued, "undeliverable": undeliverable}


def run_dispatch(execute=False, tenant="asheville", approval_file=DEFAULT_APPROVAL_FILE,
                 dnc_file=DEFAULT_DNC_FILE, ledger_file=DEFAULT_LEDGER_FILE,
                 use_sheet_approvals=True, check_deliverability=True):
    import deliverability
    audit_file = Path(f"audit_results_{tenant}.json")
    if not audit_file.exists():
        print(f"[ERROR] {audit_file} not found. Run batch_audit_scanner.py first.")
        return _result(error=f"{audit_file} not found")

    audits = _load_json(audit_file, [])
    approvals = _load_json(Path(approval_file), [])
    if use_sheet_approvals:
        # Owner decisions made from the workbook (phone included) count too. Each
        # still has to match recipient, domain, exact message hash and expiry.
        approvals = approvals + load_tenant_sheet_approvals(tenant)

    # An unreadable ledger reads as "nobody has been contacted", which is
    # permission to send. Refuse instead.
    import outreach_ledger
    ledger = _open_ledger(Path(ledger_file), Path(dnc_file))
    try:
        dnc = ledger.suppressed()
        sent_hashes = ledger.sent_hashes()
        already_contacted = ledger.sent_recipients()
    except outreach_ledger.LedgerUnavailable as exc:
        print(f"[BLOCKED] Cannot verify who has already been contacted: {exc}")
        print("[BLOCKED] No messages will be sent. Fix the ledger backend and re-run.")
        return _result(error=f"ledger unavailable: {exc}")
    
    tenant_upper = tenant.upper()
    smtp_user = os.getenv(f"SMTP_USER_{tenant_upper}") or os.getenv("SMTP_USER")
    smtp_password = os.getenv(f"SMTP_PASSWORD_{tenant_upper}") or os.getenv("SMTP_PASSWORD")

    if execute and (not smtp_user or not smtp_password):
        print(f"[BLOCKED] Live execution requested for {tenant} but SMTP credentials are unavailable.")
        return _result(error="SMTP credentials unavailable")

    import proposal_engine
    review_required = proposal_engine.flagged_domains(tenant)
    if review_required:
        print(f"  [REVIEW] {len(review_required)} proposal(s) are flagged NEEDS REVIEW "
              "and cannot be sent until their payment links are fixed.")

    sent_count = 0
    blocked_count = 0
    awaiting = []
    undeliverable = []
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
        if domain in review_required:
            # The proposal carries a NEEDS REVIEW banner because a payment link
            # is missing. Sending it would hand a real business a dead link.
            print(f"[BLOCKED] {domain} is flagged NEEDS REVIEW; not sending.")
            blocked_count += 1
            continue
        if digest in sent_hashes:
            print(f"[SKIP] Exact message already sent to {domain}.")
            continue
        if recipient in already_contacted:
            # Not a block: a follow-up is legitimate. But it must be visible,
            # because the approver is agreeing to a second contact, not a first.
            print(f"[NOTE] {recipient} has been contacted before; this is a follow-up.")
        approved, missing = _valid_approval(approvals, recipient, domain, digest)
        if not approved:
            print(f"[BLOCKED] {domain} lacks matching, unexpired approvals: {', '.join(missing)}.")
            blocked_count += 1

            # Stop building the queue once it is full. Everything still counts as
            # blocked; it simply waits for a later run, so the owner sees a
            # reviewable batch instead of a wall.
            if len(awaiting) >= STAGING_LIMIT:
                continue

            # Do not spend one of Tom's approval decisions on an address that
            # provably cannot receive mail. A domain with no MX at all is a hard
            # fact; anything softer only earns a warning on the row.
            reachability = deliverability.check_domain(domain) if check_deliverability else {}
            if check_deliverability and deliverability.is_hard_fail(reachability):
                print(f"[SKIP] {domain} publishes no MX records; not queuing it for approval.")
                undeliverable.append(domain)
                continue
            warning = deliverability.warning_for(reachability) if check_deliverability else ""

            evidence = (f"Audited {domain}: score {audit.get('score', '?')}, "
                        f"grade {audit.get('grade', '?')}, "
                        f"{len(audit.get('issues', []))} issue(s). Proposal drafted.")
            # Queue it for the owner to decide on, so the Approval Queue shows the
            # exact message that is waiting rather than nothing at all.
            awaiting.append({
                "domain": domain,
                "recipient": recipient,
                "business": audit.get("business") or domain,
                "subject": subject,
                "message_sha256": digest,
                "evidence": evidence,
                "risk": (f"{warning} External send to a real business. No cost."
                         if warning else "External send to a real business. No cost."),
            })
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
            return _result(error=f"send outcome uncertain for {domain}: {exc}",
                           sent=sent_count, blocked=blocked_count,
                           queued=len(awaiting), undeliverable=len(undeliverable))

        try:
            ledger.record_send(recipient, domain, digest)
        except Exception as exc:
            # The message is already gone. An unrecorded send looks identical to
            # one that never happened, so stop rather than risk repeating it.
            print(f"[CRITICAL] Sent to {domain} but could not record it: {exc}")
            print("[CRITICAL] Stopping so the next run cannot send it again. "
                  "Record this send by hand before re-running.")
            return _result(error=f"unrecorded send to {domain}: {exc}",
                           sent=sent_count, blocked=blocked_count,
                           queued=len(awaiting), undeliverable=len(undeliverable))
        sent_hashes.add(digest)
        sent_count += 1
        print(f"[SENT] Approved message sent to {domain}.")

    if awaiting and use_sheet_approvals:
        staged = stage_pending_approvals(tenant, awaiting)
        if staged:
            print(f"[QUEUED] {staged} approval row(s) added to the {tenant} Approval Queue "
                  "for your decision.")

    if undeliverable:
        print(f"[SKIPPED] {len(undeliverable)} domain(s) cannot receive mail and were not "
              f"queued for approval: {', '.join(sorted(undeliverable)[:5])}"
              + (" ..." if len(undeliverable) > 5 else ""))

    if len(awaiting) >= STAGING_LIMIT:
        print(f"[QUEUE FULL] Staged the first {STAGING_LIMIT} for review; the rest wait "
              "for the next run so the Approval Queue stays reviewable.")

    print(f"[DONE] tenant={tenant} sent={sent_count} blocked={blocked_count} "
          f"queued={len(awaiting)} undeliverable={len(undeliverable)} execute={execute}")
    return _result(sent=sent_count, blocked=blocked_count,
                   queued=len(awaiting), undeliverable=len(undeliverable))


def dispatch_emails(*args, **kwargs):
    """
    Boolean view of a run: True only when nothing was blocked and nothing broke.

    This is the contract the safety tests rely on, and the right one for a
    manual --execute run. The pipeline's staging step uses run_dispatch directly
    so that "nothing is approved yet" does not read as a failure.
    """
    outcome = run_dispatch(*args, **kwargs)
    return outcome["error"] is None and outcome["blocked"] == 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="Send only exactly approved messages.")
    parser.add_argument("--tenant", default="asheville", help="Tenant ID")
    parser.add_argument("--approval-file", default=str(DEFAULT_APPROVAL_FILE))
    parser.add_argument("--dnc-file", default=str(DEFAULT_DNC_FILE))
    parser.add_argument("--ledger-file", default=str(DEFAULT_LEDGER_FILE))
    parser.add_argument("--no-sheet-approvals", action="store_true",
                        help="Ignore the workbook Approval Queue; use only the local approval file.")
    parser.add_argument("--no-deliverability-check", action="store_true",
                        help="Queue every domain for approval, even ones with no MX records.")
    parser.add_argument("--stage-only", action="store_true",
                        help="Queue decisions for the owner and never send. Succeeds when "
                             "staging worked, even though nothing is approved yet.")
    args = parser.parse_args()

    outcome = run_dispatch(
        False if args.stage_only else args.execute,
        args.tenant, args.approval_file, args.dnc_file, args.ledger_file,
        use_sheet_approvals=not args.no_sheet_approvals,
        check_deliverability=not args.no_deliverability_check,
    )
    if args.stage_only:
        # Blocked is the expected state here: it means the owner has not decided
        # yet, which is the whole point of staging.
        raise SystemExit(1 if outcome["error"] else 0)
    raise SystemExit(0 if outcome["error"] is None and outcome["blocked"] == 0 else 1)


if __name__ == "__main__":
    main()
