"""
Prove the pipeline can actually do its job in the environment it is running in.

Why this is separate from the unit tests
----------------------------------------
94 unit tests passed every day between 2026-08-07 and 2026-08-09 while every
cloud run silently wrote nothing. They could not have caught it: locally the
OAuth token file is writable, and under Cloud Run it is a read-only Secret
Manager mount. The bug lived entirely in the difference between the two
environments, which unit tests deliberately abstract away.

This checks the things that only break in the real deployment:

  1. Can we obtain a Sheets client at all, and as which identity?
  2. Can we actually WRITE to the live workbook and read the value back?
  3. Is the durable outreach ledger reachable, so the send guard has a memory?

It writes one row to a dedicated 'Smoke Test' tab, never to the Activity Log,
so the audit trail is not polluted with test traffic. The tab is trimmed to the
most recent rows so it cannot grow without bound.

    python smoke_test.py --tenant asheville
    python smoke_test.py --tenant asheville --read-only   # skip the write

Exit code 0 means the environment is genuinely capable of the work.
"""

import argparse
import datetime as dt
import os
import sys

import agency_auth

SMOKE_TAB = "Smoke Test"
HEADERS = ["Checked At", "Environment", "Identity", "Check", "Result"]
KEEP_ROWS = 20


def tenant_config(tenant):
    import yaml

    with open("tenants.yaml", "r", encoding="utf-8") as handle:
        tenants = (yaml.safe_load(handle) or {}).get("tenants", {}) or {}
    config = tenants.get(tenant)
    if not config:
        raise SystemExit(f"[ERROR] unknown tenant '{tenant}' in tenants.yaml")
    return config


def environment_label():
    job = os.getenv("CLOUD_RUN_JOB")
    return f"Cloud Run job {job}" if job else "local"


def identity_label():
    """
    Who we authenticated as, reported by the auth layer rather than guessed.

    The first version inspected the gspread client and defaulted to "user OAuth
    token" when it found nothing — then printed exactly that on a run where the
    log line above confirmed the job identity had been accepted. A check that
    misreports the identity is worse than one that says nothing.
    """
    return agency_auth.last_identity


def get_or_create_tab(sheet):
    try:
        return sheet.worksheet(SMOKE_TAB)
    except Exception:
        worksheet = sheet.add_worksheet(title=SMOKE_TAB, rows=100, cols=len(HEADERS))
        worksheet.append_row(HEADERS)
        return worksheet


def trim(worksheet):
    """Keep the tab small; this is a heartbeat, not a record worth accumulating."""
    rows = worksheet.get_all_values()
    excess = len(rows) - (KEEP_ROWS + 1)  # +1 for the header
    if excess > 0:
        worksheet.delete_rows(2, 1 + excess)


def check_sheets(tenant, read_only=False):
    config = tenant_config(tenant)
    spreadsheet_id = config.get("spreadsheet_id")
    if not spreadsheet_id:
        return False, f"tenant '{tenant}' has no spreadsheet_id"

    client = agency_auth.sheets_client(probe_spreadsheet_id=spreadsheet_id)
    sheet = client.open_by_key(spreadsheet_id)
    who = identity_label()

    if read_only:
        return True, f"opened '{sheet.title}' as {who} (write skipped)"

    stamp = dt.datetime.now(dt.timezone.utc).isoformat()
    worksheet = get_or_create_tab(sheet)
    worksheet.append_row([stamp, environment_label(), who, "write+readback", "pending"])

    # Read it back. Appending without verifying is how a silent failure hides:
    # the call returned, so the code assumed the data landed.
    rows = worksheet.get_all_values()
    last = rows[-1] if rows else []
    if not last or last[0] != stamp:
        return False, "the appended row could not be read back"

    worksheet.update_cell(len(rows), 5, "ok")
    trim(worksheet)
    return True, f"wrote and verified one row in '{sheet.title}' as {who}"


def check_ledger():
    """The send guard is only a guard if its memory survives this container."""
    import outreach_ledger

    ledger = outreach_ledger.OutreachLedger(use_firestore=True, require_durable=False)
    if ledger.client() is None:
        return False, "Firestore unreachable — the duplicate-send guard would have no memory"
    suppressed = ledger.suppressed()
    contacted = ledger.sent_recipients()
    return True, f"durable ledger reachable ({len(suppressed)} suppressed, {len(contacted)} contacted)"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tenant", default="asheville")
    parser.add_argument("--read-only", action="store_true",
                        help="Check access without writing a row.")
    args = parser.parse_args()

    print("=" * 66)
    print(f"  SMOKE TEST — {environment_label()}")
    print(f"  Tenant: {args.tenant}")
    print("=" * 66)

    checks = [
        ("Sheets read/write", lambda: check_sheets(args.tenant, args.read_only)),
        ("Durable ledger", check_ledger),
    ]

    failures = 0
    for name, run in checks:
        try:
            ok, detail = run()
        except Exception as exc:
            ok, detail = False, f"{type(exc).__name__}: {exc}"
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")
        if not ok:
            failures += 1

    print("=" * 66)
    if failures:
        print(f"  {failures} check(s) FAILED — this environment cannot do the work.")
        return 1
    print("  All checks passed; the environment can do real work.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
