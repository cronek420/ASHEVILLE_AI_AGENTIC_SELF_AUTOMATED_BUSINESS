"""
Add a new city to the agency.

Copies the blank Command Center template into the shared Drive folder, clears any
operational rows, reads the new workbook's tab gids, and appends the tenant to
tenants.yaml. After this the normal pipeline works for the new city with no code
changes:

    python add_city.py --tenant raleigh --location "Raleigh NC"
    python run_agency.py --sync-sheet

Nothing is sent, published, or charged. The new workbook starts with an empty
Prospect Tracker, Approval Queue, and Activity Log.
"""

import argparse
import os
import sys

import yaml
from googleapiclient.discovery import build

import agency_auth
import live_sheets_sync as sync

SCOPES = agency_auth.SCOPES
SHEET_MIME = "application/vnd.google-apps.spreadsheet"
TENANTS_FILE = "tenants.yaml"

# Tabs whose rows belong to one city and must not be inherited by the next one.
OPERATIONAL_TABS = {
    "Prospect Tracker": {"Website", "Business"},
    "Approval Queue": {"Approval ID", "Status"},
    "Activity Log": {"Action / Change", "Result"},
    "Client Delivery": {"Job ID", "Client"},
}
GID_TABS = {
    "live_dashboard": "Live Dashboard",
    "approval_queue": "Approval Queue",
    "prospect_tracker": "Prospect Tracker",
}


def credentials():
    """Cloud Run uses the job's own identity; locally this is the OAuth token."""
    try:
        return agency_auth.sheets_credentials()
    except (FileNotFoundError, RuntimeError) as err:
        raise SystemExit(f"[ERROR] {err}")


def load_tenants():
    if not os.path.exists(TENANTS_FILE):
        return {}
    with open(TENANTS_FILE, "r", encoding="utf-8") as handle:
        return (yaml.safe_load(handle) or {}).get("tenants", {}) or {}


def clear_operational_data(client, spreadsheet_id):
    """Blank every data row below the header on city-specific tabs."""
    sheet = client.open_by_key(spreadsheet_id)
    cleared = {}
    for tab, required in OPERATIONAL_TABS.items():
        try:
            ws = sheet.worksheet(tab)
        except Exception:
            continue
        rows = ws.get_all_values()
        header_index = sync._find_headers(rows, required)
        if header_index is None:
            continue
        first_data = header_index + 2  # 1-based row after the header
        last = sync._last_used_row(rows)
        if last < first_data:
            cleared[tab] = 0
            continue
        width = max(len(r) for r in rows) or 1
        end_col = sync._column_label(width - 1)
        ws.batch_clear([f"A{first_data}:{end_col}{last}"])
        cleared[tab] = last - first_data + 1
    return cleared


def read_gids(client, spreadsheet_id):
    sheet = client.open_by_key(spreadsheet_id)
    by_title = {ws.title: ws.id for ws in sheet.worksheets()}
    missing = [tab for tab in GID_TABS.values() if tab not in by_title]
    if missing:
        raise SystemExit(f"[ERROR] template is missing required tabs: {', '.join(missing)}")
    return {key: str(by_title[tab]) for key, tab in GID_TABS.items()}


def append_tenant(tenant, location, spreadsheet_id, gids):
    """Append to tenants.yaml as text so existing comments survive."""
    block = [
        f"  {tenant}:",
        f'    location: "{location}"',
        f'    spreadsheet_id: "{spreadsheet_id}"',
        '    email_user: "" # Not read by any code yet; see the note in tenants.yaml',
        "    gids:",
    ]
    for key in ["live_dashboard", "approval_queue", "prospect_tracker"]:
        block.append(f'      {key}: "{gids[key]}"')
    block.append("    # Optional: leads used only if the live scrape returns nothing for THIS city.")
    block.append("    # Never inherits another city's businesses.")
    block.append("    fallback_targets: []")

    with open(TENANTS_FILE, "r", encoding="utf-8") as handle:
        current = handle.read().rstrip("\n")
    with open(TENANTS_FILE, "w", encoding="utf-8") as handle:
        handle.write(current + "\n" + "\n".join(block) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Add a new city to the agency.")
    parser.add_argument("--tenant", required=True, help="Short slug, e.g. raleigh")
    parser.add_argument("--location", required=True, help='Search location, e.g. "Raleigh NC"')
    parser.add_argument("--template", default=os.getenv("CITY_TEMPLATE_SHEET_ID", ""),
                        help="Template spreadsheet id (or set CITY_TEMPLATE_SHEET_ID)")
    parser.add_argument("--folder", default=sync.DRIVE_FOLDER_ID, help="Destination Drive folder id")
    parser.add_argument("--title", default="", help="Workbook title (default: <TENANT>___Command_Center)")
    args = parser.parse_args()

    tenant = args.tenant.strip().lower()
    if not tenant.isidentifier():
        raise SystemExit("[ERROR] --tenant must be a simple slug such as raleigh")
    if not args.template:
        raise SystemExit("[ERROR] pass --template or set CITY_TEMPLATE_SHEET_ID")

    existing = load_tenants()
    if tenant in existing:
        raise SystemExit(f"[ERROR] tenant '{tenant}' already exists in {TENANTS_FILE}")

    import gspread

    creds = credentials()
    client = gspread.authorize(creds)
    drive = build("drive", "v3", credentials=creds)

    title = args.title or f"{tenant.upper()}___Command_Center"
    print(f"[1/4] Copying template -> {title}")
    created = drive.files().copy(
        fileId=args.template,
        body={"name": title, "mimeType": SHEET_MIME, "parents": [args.folder]},
        fields="id,name",
        supportsAllDrives=True,
    ).execute()
    spreadsheet_id = created["id"]
    print(f"      new workbook: {spreadsheet_id}")

    print("[2/4] Clearing operational rows")
    for tab, count in clear_operational_data(client, spreadsheet_id).items():
        print(f"      {tab}: cleared {count} row(s)")

    print("[3/4] Reading tab gids")
    gids = read_gids(client, spreadsheet_id)
    for key, value in gids.items():
        print(f"      {key}: {value}")

    print(f"[4/6] Appending '{tenant}' to {TENANTS_FILE}")
    append_tenant(tenant, args.location, spreadsheet_id, gids)

    # The scheduled job authenticates as its own service account, which has no
    # access to a workbook it did not create. Forgetting this step leaves the new
    # city looking correctly configured while its sync fails in the cloud with a
    # permission error, so do it here rather than trusting a runbook.
    print("[5/6] Sharing the new workbook with the pipeline service account")
    try:
        import grant_sheet_access

        drive.permissions().create(
            fileId=spreadsheet_id,
            body={"type": "user", "role": "writer",
                  "emailAddress": grant_sheet_access.DEFAULT_SERVICE_ACCOUNT},
            sendNotificationEmail=False,
            supportsAllDrives=True,
        ).execute()
        print(f"      shared with {grant_sheet_access.DEFAULT_SERVICE_ACCOUNT}")
    except Exception as exc:
        print(f"      [WARN] could not share automatically: {exc}")
        print("      Run this before the next pipeline run, or the cloud sync will fail:")
        print("        python grant_sheet_access.py --execute")

    print("[6/6] Refreshing the all-cities master dashboard")
    try:
        import master_dashboard

        count, master_id = master_dashboard.refresh(client=client)
        print(f"      rolled up {count} city/cities -> {master_id}")
    except Exception as exc:  # never fail the city creation over a roll-up
        print(f"      [WARN] roll-up not refreshed: {exc}")
        print("      run 'python master_dashboard.py' once this is resolved.")

    print(f"""
[DONE] {tenant} is registered.

  Workbook: https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit

Next:
  python run_agency.py --sync-sheet        # scrape, audit, propose, sync all cities
  Open the workbook's '✅ Owner Review' tab to see what needs you.

If the live scrape returns no leads for {args.location}, the run writes an empty
lead file on purpose. Add that city's own businesses under fallback_targets in
{TENANTS_FILE} rather than borrowing another city's.
""")


if __name__ == "__main__":
    sys.exit(main())
