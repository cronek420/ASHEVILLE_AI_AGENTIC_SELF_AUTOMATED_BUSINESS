import json
import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv


DEFAULT_COMMAND_CENTER_URL = "https://docs.google.com/spreadsheets/d/1TDwiyl3Z0WGyJjDcQ7__6DqST0U1OuPGYujAxnb2JLg/edit"
DEFAULT_DRIVE_URL = "https://drive.google.com/drive/folders/14bNYctr5hoYcOhSCdWXOvPMS6qVMru10?usp=drive_link"
DEFAULT_WEBSITE_ORIGIN = "https://universal-ai-workforce.gronekthomas.chatgpt.site"
DEFAULT_APPROVER_EMAIL = "gronekthomas@gmail.com"
# Fallback gids, used only when tenants.yaml is unavailable. They must belong to
# the same workbook as DEFAULT_COMMAND_CENTER_URL or the fallback links break.
APPROVAL_QUEUE_GID = "1919393072"
PROSPECT_TRACKER_GID = "182297405"
LIVE_DASHBOARD_GID = "1965670317"


def load_tenant_links(path="tenants.yaml"):
    """
    Build per-tenant Command Center links from tenants.yaml.

    Each tenant owns a different spreadsheet, so a single shared URL + gid set
    sends every city's links to one workbook. Returns [] when the file is
    missing or unreadable so the report falls back to the single-sheet layout.
    """
    try:
        import yaml

        with open(path, "r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    except (OSError, ImportError, ValueError):
        return []

    links = []
    for name, cfg in (data.get("tenants") or {}).items():
        spreadsheet_id = (cfg or {}).get("spreadsheet_id")
        if not spreadsheet_id:
            continue
        gids = (cfg or {}).get("gids") or {}
        links.append({
            "tenant": name,
            "url": f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit",
            "live_dashboard": str(gids.get("live_dashboard", LIVE_DASHBOARD_GID)),
            "approval_queue": str(gids.get("approval_queue", APPROVAL_QUEUE_GID)),
            "prospect_tracker": str(gids.get("prospect_tracker", PROSPECT_TRACKER_GID)),
        })
    return links


def _read_json_list(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return []
    return data if isinstance(data, list) else []


RUN_START_MARKER = "Run started:"


def _scan_run_errors(log_path="agency_cron.log", marker=RUN_START_MARKER):
    """
    Count errors from the MOST RECENT pipeline run only.

    The log is append-only across every run ever made, so scanning the whole
    file reports failures that were fixed days ago and the count can only grow.
    Errors are collected from the last run-start banner onward; if no banner is
    found (log truncated or rotated) the whole file is used as a fallback.
    """
    if not os.path.exists(log_path):
        return 0, []

    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as handle:
            lines = handle.readlines()
    except OSError:
        return 0, []

    start = 0
    for index in range(len(lines) - 1, -1, -1):
        if marker in lines[index]:
            start = index
            break

    errors = [
        line.strip()
        for line in lines[start:]
        if "[ERROR]" in line or "Traceback" in line
    ]
    # Keep the LAST three: when a run fails, the newest errors are the useful ones.
    return len(errors), errors[-3:]


def _load_daily_stats(tenant=None):
    suffix = f"_{tenant}" if tenant else ""
    scraped_leads = _read_json_list(f"scraped_leads{suffix}.json")
    audits = _read_json_list(f"audit_results{suffix}.json")
    proposals_generated = 0
    if os.path.exists(f"proposals{suffix}"):
        proposals_generated = len([name for name in os.listdir(f"proposals{suffix}") if name.endswith(".txt")])

    error_count, recent_errors = _scan_run_errors()

    return {
        "scraped_leads": len(scraped_leads),
        "audits": len(audits),
        "proposals_generated": proposals_generated,
        "error_count": error_count,
        "recent_errors": recent_errors,
    }


def load_sync_health(path="tenants.yaml"):
    """
    What the sheet sync and the inbox pass actually did on the last run.

    Counting leads and proposals only proves files were written on disk. For
    three days in August 2026 every cloud run produced those files and wrote
    nothing to the Command Center, because a read-only token mount silently
    aborted the sync while the pipeline still reported success. These numbers
    are the ones that would have exposed it.
    """
    import inbox_monitor
    import live_sheets_sync

    tenants = [link["tenant"] for link in load_tenant_links(path)]
    syncs = []
    for name in tenants:
        result = live_sheets_sync.read_sync_result(name) or {}
        syncs.append({
            "tenant": name,
            "recorded": bool(result),
            "ok": bool(result.get("ok")),
            "appended": int(result.get("appended") or 0),
            "updated": int(result.get("updated") or 0),
            "error": result.get("error", ""),
        })

    inbox = inbox_monitor.read_result() or {}
    return {
        "syncs": syncs,
        "inbox_ok": bool(inbox.get("ok")),
        "inbox_recorded": bool(inbox),
        "unread": inbox.get("unread"),
    }


def build_sync_health_block(health):
    """A plain-language block that makes a do-nothing run impossible to miss."""
    if not health:
        return ""

    lines = []
    silent = []
    for entry in health["syncs"]:
        label = entry["tenant"].upper()
        if not entry["recorded"]:
            lines.append(f"• {label}: NO SYNC RECORDED — the step did not run.")
            silent.append(entry["tenant"])
        elif not entry["ok"]:
            detail = f" ({entry['error']})" if entry["error"] else ""
            lines.append(f"• {label}: SYNC FAILED — nothing was written{detail}.")
            silent.append(entry["tenant"])
        else:
            touched = entry["appended"] + entry["updated"]
            lines.append(
                f"• {label}: wrote {touched} row(s) — "
                f"{entry['appended']} new, {entry['updated']} updated."
            )
            if touched == 0:
                lines.append("    (connected, but no rows changed)")

    if health["inbox_recorded"] and health["inbox_ok"]:
        unread = health["unread"]
        lines.append(f"• Inbox: checked, {unread} unread message(s).")
    else:
        lines.append("• Inbox: NOT CHECKED — the mailbox could not be read.")
        silent.append("inbox")

    banner = ""
    if silent:
        banner = (
            "!! ATTENTION: part of this run did no work. "
            f"Affected: {', '.join(silent)}.\n"
            "   The counts above are the authority, not the run's pass/fail summary.\n\n"
        )
    return banner + "== DID THE WORK ACTUALLY HAPPEN? ==\n" + "\n".join(lines)


def load_tenant_stats(path="tenants.yaml"):
    """
    Per-tenant lead/audit/proposal counts.

    Each tenant writes suffixed artifacts (scraped_leads_asheville.json,
    proposals_charlotte/, ...). The unsuffixed files are legacy leftovers from
    the single-city era, so a tenant-less read reports numbers that belong to
    no current city.
    """
    tenants = [link["tenant"] for link in load_tenant_links(path)]
    stats = []
    for name in tenants:
        tenant_stats = _load_daily_stats(name)
        stats.append({
            "tenant": name,
            "scraped_leads": tenant_stats["scraped_leads"],
            "audits": tenant_stats["audits"],
            "proposals_generated": tenant_stats["proposals_generated"],
        })
    return stats


def build_report_content(config=None, stats=None, tenant=None, tenant_links=None,
                         tenant_stats=None, sync_health=None):
    config = config or {}
    stats = stats or _load_daily_stats(tenant)

    command_center_url = config.get("command_center_url") or DEFAULT_COMMAND_CENTER_URL
    drive_url = config.get("drive_url") or DEFAULT_DRIVE_URL
    website_origin = config.get("website_origin") or DEFAULT_WEBSITE_ORIGIN
    intake_public_url = (config.get("intake_public_url") or "").strip()
    approval_summary = config.get("approval_summary") or (
        "Gate B is still pending for public deployment. Once approved and deployed, "
        "the public intake link will appear here automatically."
    )

    if intake_public_url:
        intake_status = (
            f"Live intake link: {intake_public_url}\n"
            "What happens when someone submits it: the request is validated, stored privately, "
            "marked NEEDS_OWNER_REVIEW, and staged for Atlas-Orchestrator review before any business action can begin."
        )
    else:
        intake_status = (
            "Live intake link: pending Gate B deployment approval\n"
            f"Approved website origin reserved for connection: {website_origin}\n"
            "What happens once deployed: website submissions will be validated, stored privately, "
            "and held for owner review before any outreach, payment, publishing, or client access happens."
        )

    if stats["error_count"] > 0:
        action_status = (
            "Action needed today:\n"
            "- Review the recent errors listed below.\n"
            "- If the issue involves approvals, use the Gate B approval line in NEED_HUMAN_APPROVAL.\n"
            "- If the issue is operational, inspect agency_cron.log on the machine running the pipeline."
        )
    else:
        action_status = (
            "Action needed today:\n"
            "- No urgent intervention is required from the latest run.\n"
            "- Review the approval note below if you want public intake deployed."
        )

    if stats["recent_errors"]:
        recent_error_block = "Recent error samples:\n" + "\n".join(f"- {line}" for line in stats["recent_errors"])
    else:
        recent_error_block = "Recent error samples:\n- None recorded in the current log scan."

    review_expectations = (
        "Approval-ready outreach reviews now require screenshot proof that the website was checked, "
        "an issue count, the issues found, and quick-fix recommendations for each visible issue."
    )

    if tenant_stats:
        rows = []
        for entry in tenant_stats:
            rows.append(
                f"-- {entry['tenant'].upper()} --\n"
                f"• Leads: {entry['scraped_leads']}\n"
                f"• Audits: {entry['audits']}\n"
                f"• Proposals: {entry['proposals_generated']}"
            )
        rows.append(f"• Errors (last run): {stats['error_count']}")
        quick_stats_block = "\n\n".join(rows)
    else:
        quick_stats_block = (
            f"• Leads: {stats['scraped_leads']}\n"
            f"• Audits: {stats['audits']}\n"
            f"• Proposals: {stats['proposals_generated']}\n"
            f"• Errors: {stats['error_count']}"
        )

    if tenant_links:
        # One block per city — each tenant's tabs live in its own spreadsheet.
        sections = []
        for link in tenant_links:
            sections.append(
                f"-- {link['tenant'].upper()} --\n"
                f"[Tap for Live Dashboard]:\n"
                f"{link['url']}#gid={link['live_dashboard']} (Live Dashboard)\n\n"
                f"[Tap to Approve Pending Requests]:\n"
                f"{link['url']}#gid={link['approval_queue']} (Approval Queue)\n\n"
                f"[Tap to View All Prospect Data]:\n"
                f"{link['url']}#gid={link['prospect_tracker']} (Prospect Tracker)"
            )
        command_center_block = "\n\n".join(sections)
    else:
        command_center_block = (
            f"[Tap for Live Dashboard]:\n"
            f"{command_center_url}#gid={LIVE_DASHBOARD_GID} (Live Dashboard)\n\n"
            f"[Tap to Approve Pending Requests]:\n"
            f"{command_center_url}#gid={APPROVAL_QUEUE_GID} (Approval Queue)\n\n"
            f"[Tap to View All Prospect Data]:\n"
            f"{command_center_url}#gid={PROSPECT_TRACKER_GID} (Prospect Tracker)"
        )

    # The health block goes above everything else: if a step did no work, that
    # outranks every other number in the email.
    health_block = build_sync_health_block(sync_health) if sync_health else ""
    health_section = f"{health_block}\n\n" if health_block else ""

    # Mobile optimized concise layout
    tenant_header = f" [{tenant.upper()}]" if tenant else ""
    return f"""Hello Thomas,

[ASHEVILLE AI AGENCY STATUS]{tenant_header}

{health_section}== QUICK STATS ==
{quick_stats_block}

{action_status}

== MOBILE COMMAND CENTER ==
{command_center_block}

[Tap for Google Drive]:
{drive_url}

== INTAKE & SYSTEM STATUS ==
{intake_status}

Approval note:
{approval_summary}

Review standard:
{review_expectations}

{recent_error_block}

Have a great day,
Your Automated Agency
"""




def send_report():
    if os.path.exists("/secrets/env/.env"):
        load_dotenv("/secrets/env/.env")
    else:
        load_dotenv()
    email_user = os.getenv("SMTP_USER")
    email_app_password = os.getenv("SMTP_PASSWORD")

    if not email_user or not email_app_password:
        print("[WARNING] SMTP credentials not found. Cannot send daily report.")
        return False

    recipient = os.getenv("DAILY_REPORT_RECIPIENT", DEFAULT_APPROVER_EMAIL)
    config = {
        "command_center_url": os.getenv("COMMAND_CENTER_URL", DEFAULT_COMMAND_CENTER_URL),
        "drive_url": os.getenv("GOOGLE_DRIVE_FOLDER_URL", DEFAULT_DRIVE_URL),
        "website_origin": os.getenv("ALLOWED_WEBSITE_ORIGIN", DEFAULT_WEBSITE_ORIGIN),
        "intake_public_url": os.getenv("WORKFORCE_INTAKE_PUBLIC_URL", ""),
        "approval_summary": os.getenv(
            "DAILY_REPORT_APPROVAL_SUMMARY",
            "Gate B is still pending for public deployment. Approving Gate B allows Cloud Run deployment, Firestore setup, "
            "and verification of the final public intake URL before the website is connected.",
        ),
    }

    msg = EmailMessage()
    
    # Check if there are approvals pending (simplistic check from proposals)
    # Ideally we parse the sheet, but we can just use the proposals or errors as a flag
    stats = _load_daily_stats(config.get("tenant"))
    tenant_stats = load_tenant_stats()
    sync_health = load_sync_health()
    # Subject must reflect every city, not whichever artifacts happen to sit in
    # the legacy unsuffixed paths.
    total_proposals = (
        sum(entry["proposals_generated"] for entry in tenant_stats)
        if tenant_stats else stats["proposals_generated"]
    )

    # A run that silently wrote nothing must be visible from the subject line,
    # ahead of anything else, because it looks healthy by every other measure.
    silent_run = any(not entry["ok"] for entry in sync_health["syncs"]) or not sync_health["inbox_ok"]

    subject_prefix = ""
    if silent_run:
        subject_prefix = "[CHECK: a step did no work] "
    elif stats["error_count"] > 0:
        subject_prefix = f"[URGENT: {stats['error_count']} Errors] "
    elif total_proposals > 0:
        subject_prefix = f"[ACTION: {total_proposals} Approvals] "
    else:
        subject_prefix = "[All Good] "
        
    tenant_str = f" [{config.get('tenant').upper()}]" if config.get("tenant") else ""
    msg["Subject"] = f"{subject_prefix}Asheville AI Agency{tenant_str} - Daily Control Report"
    msg["From"] = email_user
    msg["To"] = recipient
    msg.set_content(build_report_content(
        config=config,
        stats=stats,
        tenant=config.get("tenant"),
        tenant_links=load_tenant_links(),
        tenant_stats=tenant_stats,
        sync_health=sync_health,
    ))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(email_user, email_app_password)
            server.send_message(msg)
        print(f"[SENT] Daily report emailed to {recipient}")
        return True
    except Exception as exc:
        print(f"[ERROR] Failed to send daily report: {exc}")
        return False


if __name__ == "__main__":
    send_report()
