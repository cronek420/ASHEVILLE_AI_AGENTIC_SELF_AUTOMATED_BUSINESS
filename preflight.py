"""
Is this business ready to operate? Run it any time, especially after adding a city.

Every check answers a question that has actually bitten this project:

  * Can the pipeline reach the workbook AS THE IDENTITY THE CLOUD JOB USES?
    A workbook you can open from your laptop is not necessarily one the
    scheduled job can write.
  * Is exactly one offer active? Stage 1 of the operating loop stops on zero or
    on more than one, so a blank cell quietly halts the whole city.
  * Does the durable ledger answer? If not, outreach must not run, because the
    duplicate-send guard would have no memory.
  * Can we send mail at all?

    python preflight.py                    # every tenant
    python preflight.py --tenant charlotte # just one

Exit code 0 means ready. Non-zero means something listed below must be fixed.
"""

import argparse
import os
import sys

import yaml
from dotenv import load_dotenv

import agency_auth

REQUIRED_TABS = [
    "Start Here", "Prospect Tracker", "Offer & Checklists",
    "Activity Log", "Approval Queue", "Client Delivery",
]

PASS, WARN, FAIL = "PASS", "WARN", "FAIL"


class Report:
    def __init__(self):
        self.rows = []

    def add(self, level, check, detail, fix=""):
        self.rows.append((level, check, detail, fix))

    def show(self):
        for level, check, detail, fix in self.rows:
            print(f"  [{level}] {check}: {detail}")
            if fix and level != PASS:
                print(f"         -> {fix}")

    @property
    def failures(self):
        return sum(1 for level, *_ in self.rows if level == FAIL)

    @property
    def warnings(self):
        return sum(1 for level, *_ in self.rows if level == WARN)


def load_tenants():
    with open("tenants.yaml", "r", encoding="utf-8") as handle:
        return (yaml.safe_load(handle) or {}).get("tenants", {}) or {}


def check_tenant(name, config, client, drive, service_account, report):
    spreadsheet_id = config.get("spreadsheet_id")
    if not spreadsheet_id:
        report.add(FAIL, f"{name}: configuration", "no spreadsheet_id in tenants.yaml",
                   "Re-run add_city.py, or add the id by hand.")
        return

    try:
        sheet = client.open_by_key(spreadsheet_id)
    except Exception as exc:
        report.add(FAIL, f"{name}: workbook access", f"cannot open: {exc}",
                   "python grant_sheet_access.py --execute")
        return
    report.add(PASS, f"{name}: workbook access", f"opened '{sheet.title}'")

    titles = [ws.title for ws in sheet.worksheets()]
    missing = [tab for tab in REQUIRED_TABS if tab not in titles]
    if missing:
        report.add(FAIL, f"{name}: tabs", f"missing {', '.join(missing)}",
                   "Copy the template again with add_city.py, or add the tabs by hand.")
    else:
        report.add(PASS, f"{name}: tabs", f"all {len(REQUIRED_TABS)} required tabs present")

    # The scheduled job runs as a service account, not as you. Opening the sheet
    # from a laptop proves nothing about whether the cloud can write to it.
    try:
        permissions = drive.permissions().list(
            fileId=spreadsheet_id, fields="permissions(emailAddress,role)",
            supportsAllDrives=True).execute().get("permissions", [])
        emails = {(p.get("emailAddress") or "").lower(): p.get("role") for p in permissions}
        role = emails.get(service_account.lower())
        if role in {"writer", "owner", "organizer"}:
            report.add(PASS, f"{name}: cloud job access", f"service account has '{role}'")
        else:
            report.add(FAIL, f"{name}: cloud job access",
                       "the pipeline service account cannot write this workbook",
                       "python grant_sheet_access.py --execute")
    except Exception as exc:
        report.add(WARN, f"{name}: cloud job access", f"could not read sharing: {exc}")

    # Exactly one active offer, or the operating loop stops.
    if "Start Here" in titles:
        rows = sheet.worksheet("Start Here").get_all_values()
        offers = [r[1].strip() for r in rows
                  if len(r) > 1 and r[0].strip().lower() == "active offer" and r[1].strip()]
        if len(offers) == 1:
            report.add(PASS, f"{name}: active offer", f"'{offers[0]}'")
        elif not offers:
            report.add(FAIL, f"{name}: active offer", "none set",
                       "Put one offer name in the 'Active Offer' row of 'Start Here'.")
        else:
            report.add(FAIL, f"{name}: active offer", f"{len(offers)} are set: {offers}",
                       "Exactly one. Do not run several offers at once.")

    # Informational: what is waiting for a human right now.
    if "Approval Queue" in titles:
        rows = sheet.worksheet("Approval Queue").get_all_values()
        header = next((i for i, r in enumerate(rows)
                       if "Status" in r and ("Approval ID" in r or "Request ID" in r)), None)
        if header is None:
            report.add(WARN, f"{name}: approval queue", "no recognizable header row",
                       "The dispatcher will add the columns it needs on first use.")
        else:
            index = rows[header].index("Status")
            pending = sum(1 for r in rows[header + 1:]
                          if index < len(r) and r[index].strip().lower()
                          in {"pending", "needs_owner_review"})
            report.add(PASS, f"{name}: approval queue",
                       f"{pending} item(s) waiting for you")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tenant", default="", help="Check one tenant instead of all.")
    args = parser.parse_args()

    load_dotenv("/secrets/env/.env" if os.path.exists("/secrets/env/.env") else ".env")

    print("=" * 70)
    print("  PREFLIGHT — is the business ready to operate?")
    print("=" * 70)

    report = Report()

    # Shared services first: if these are down, per-city results are noise.
    try:
        import outreach_ledger

        ledger = outreach_ledger.OutreachLedger(use_firestore=True, require_durable=False)
        if ledger.client() is None:
            report.add(FAIL, "durable ledger", "Firestore unreachable",
                       "Outreach must not run: the duplicate-send guard has no memory.")
        else:
            report.add(PASS, "durable ledger",
                       f"{len(ledger.suppressed())} suppressed, "
                       f"{len(ledger.sent_recipients())} previously contacted")
    except Exception as exc:
        report.add(FAIL, "durable ledger", f"{type(exc).__name__}: {exc}")

    if os.getenv("SMTP_USER") and os.getenv("SMTP_PASSWORD"):
        report.add(PASS, "email sending", "SMTP credentials present")
    else:
        report.add(FAIL, "email sending", "SMTP_USER or SMTP_PASSWORD missing from .env",
                   "Outreach and the daily report cannot be sent.")

    if os.getenv("STRIPE_PAYMENT_LINK") or os.getenv("STRIPE_API_KEY"):
        report.add(PASS, "getting paid", "a Stripe setting is present")
    else:
        report.add(WARN, "getting paid", "no STRIPE_PAYMENT_LINK or STRIPE_API_KEY in .env",
                   "G3 proposals cannot include a payment link until this is set.")

    if os.getenv("CITY_TEMPLATE_SHEET_ID"):
        report.add(PASS, "adding cities", "CITY_TEMPLATE_SHEET_ID is set")
    else:
        report.add(WARN, "adding cities", "CITY_TEMPLATE_SHEET_ID not set",
                   "add_city.py needs --template until this is set.")

    try:
        from googleapiclient.discovery import build

        import grant_sheet_access

        creds = agency_auth.sheets_credentials(verbose=False)
        client = agency_auth.sheets_client(verbose=False)
        drive = build("drive", "v3", credentials=creds)
        service_account = grant_sheet_access.DEFAULT_SERVICE_ACCOUNT
    except Exception as exc:
        report.add(FAIL, "google access", f"could not authenticate: {exc}")
        report.show()
        return 1

    tenants = load_tenants()
    if args.tenant:
        tenants = {k: v for k, v in tenants.items() if k == args.tenant}
        if not tenants:
            print(f"  [FAIL] unknown tenant '{args.tenant}'")
            return 1

    for name, config in tenants.items():
        check_tenant(name, config, client, drive, service_account, report)

    report.show()
    print("=" * 70)
    print(f"  {len(tenants)} city/cities checked. "
          f"{report.failures} failure(s), {report.warnings} warning(s).")
    if report.failures:
        print("  NOT ready: fix the FAIL items above.")
        return 1
    print("  Ready to operate.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
