import json
import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv


DEFAULT_COMMAND_CENTER_URL = "https://docs.google.com/spreadsheets/d/1sq1xtu50uiNHm97db9c5-doqgatOpYkl8IQroscVCCY/edit"
DEFAULT_DRIVE_URL = "https://drive.google.com/drive/folders/1GlPw9gqABltrWVcsZda5iI1WDVifPqYH?usp=drive_link"
DEFAULT_WEBSITE_ORIGIN = "https://universal-ai-workforce.gronekthomas.chatgpt.site"
DEFAULT_APPROVER_EMAIL = "gronekthomas@gmail.com"


def _read_json_list(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return []
    return data if isinstance(data, list) else []


def _load_daily_stats():
    scraped_leads = _read_json_list("scraped_leads.json")
    audits = _read_json_list("audit_results.json")
    proposals_generated = 0
    if os.path.exists("proposals"):
        proposals_generated = len([name for name in os.listdir("proposals") if name.endswith(".txt")])

    error_count = 0
    recent_errors = []
    if os.path.exists("agency_cron.log"):
        try:
            with open("agency_cron.log", "r", encoding="utf-8") as handle:
                for raw_line in handle:
                    line = raw_line.strip()
                    if "[ERROR]" in line or "Traceback" in line:
                        error_count += 1
                        if len(recent_errors) < 3:
                            recent_errors.append(line)
        except OSError:
            pass

    return {
        "scraped_leads": len(scraped_leads),
        "audits": len(audits),
        "proposals_generated": proposals_generated,
        "error_count": error_count,
        "recent_errors": recent_errors,
    }


def build_report_content(config=None, stats=None):
    config = config or {}
    stats = stats or _load_daily_stats()

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

    return f"""Hello Thomas,

Here is your Asheville AI Agency daily control report in plain English.

Daily snapshot:
- Leads scraped: {stats['scraped_leads']}
- Websites audited: {stats['audits']}
- Proposals available: {stats['proposals_generated']}
- Errors found in the log: {stats['error_count']}

What the system is doing day to day:
- It safely runs internal research, website audits, proposal preparation, intake queue staging, and inbox checks.
- It does not send outreach, take payment, publish work, or connect client systems unless those actions have the required approval gate.
- New website intake requests, once deployed, will stay in owner-review mode until you explicitly approve the next step.

{action_status}

Public intake status:
{intake_status}

Your key links:
- Command Center: {command_center_url}
- Drive Folder: {drive_url}
- Main Website Origin: {website_origin}

How to use this report:
- Open the Command Center first if you want the live operating view.
- Use the public intake link above once it is marked live.
- If you want deployment to move forward, reply with the exact Gate B approval line from NEED_HUMAN_APPROVAL.
- If the report shows errors, check the recent error lines below before changing anything.

Approval and deployment note:
{approval_summary}

{recent_error_block}

Have a great day,
Your Automated Agency
"""


def send_report():
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
    msg["Subject"] = "Asheville AI Agency - Daily Control Report"
    msg["From"] = email_user
    msg["To"] = recipient
    msg.set_content(build_report_content(config=config))

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
