"""
Rebuild the all-cities master dashboard from tenants.yaml.

One row per city, pulled live from each Command Center with IMPORTRANGE, so the
roll-up grows automatically as cities are added:

    python master_dashboard.py

First run only: Google requires a one-time manual authorization per source
workbook. Open the dashboard and click "Allow access" on each #REF! cell.
"""

import argparse
import os

import gspread
import yaml

from add_city import credentials

TENANTS_FILE = "tenants.yaml"
DEFAULT_MASTER_ID = os.getenv(
    "MASTER_DASHBOARD_SHEET_ID", "197dx4GwoB7t1bPfSY0UvSgXjUZbYIklph7VdixvulQ8"
)
TAB = "All Cities"

# Prospect Tracker column K = Status, Approval Queue column K = Status.
PROSPECT_STATUS_RANGE = "Prospect Tracker!K5:K"
PROSPECT_KEY_RANGE = "Prospect Tracker!A5:A"
APPROVAL_STATUS_RANGE = "Approval Queue!K5:K"

HEADERS = [
    "City", "Prospects", "Not Contacted", "Replied", "Won",
    "Waiting On You", "Approved", "Workbook",
]


def load_tenants(path=TENANTS_FILE):
    with open(path, "r", encoding="utf-8") as handle:
        return (yaml.safe_load(handle) or {}).get("tenants", {}) or {}


def _remote(spreadsheet_id, range_name):
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
    return f'IMPORTRANGE("{url}","{range_name}")'


def build_rows(tenants):
    rows = [HEADERS]
    for name, cfg in tenants.items():
        sid = cfg.get("spreadsheet_id")
        if not sid:
            continue
        url = f"https://docs.google.com/spreadsheets/d/{sid}/edit"
        prospects = _remote(sid, PROSPECT_KEY_RANGE)
        statuses = _remote(sid, PROSPECT_STATUS_RANGE)
        approvals = _remote(sid, APPROVAL_STATUS_RANGE)
        label = cfg.get("location") or name.title()
        rows.append([
            label,
            f'=IFERROR(COUNTA({prospects}),"—")',
            f'=IFERROR(COUNTIF({statuses},"Not Contacted"),"—")',
            f'=IFERROR(COUNTIF({statuses},"Replied"),"—")',
            f'=IFERROR(COUNTIF({statuses},"Won"),"—")',
            f'=IFERROR(COUNTIF({approvals},"Pending"),"—")',
            f'=IFERROR(COUNTIF({approvals},"Approved")+COUNTIF({approvals},"Approved with Conditions"),"—")',
            f'=HYPERLINK("{url}","Open {name}")',
        ])

    last = len(rows)
    if last > 1:
        rows.append([
            "TOTAL",
            f"=SUM(B2:B{last})", f"=SUM(C2:C{last})", f"=SUM(D2:D{last})",
            f"=SUM(E2:E{last})", f"=SUM(F2:F{last})", f"=SUM(G2:G{last})", "",
        ])
    return rows


def refresh(master_id=None, tenants_file=TENANTS_FILE, client=None):
    master_id = master_id or DEFAULT_MASTER_ID
    client = client or gspread.authorize(credentials())
    tenants = load_tenants(tenants_file)
    sheet = client.open_by_key(master_id)

    try:
        ws = sheet.worksheet(TAB)
        ws.clear()
    except gspread.WorksheetNotFound:
        ws = sheet.add_worksheet(title=TAB, rows=60, cols=len(HEADERS), index=0)

    rows = build_rows(tenants)
    banner = [[f"ALL CITIES — {len(tenants)} live market(s). Counts pull live from each Command Center."], []]
    ws.update(values=banner, range_name="A1:A2")
    ws.update(values=rows, range_name=f"A3:H{2 + len(rows)}", value_input_option="USER_ENTERED")

    sheet.batch_update({"requests": [
        {"repeatCell": {
            "range": {"sheetId": ws.id, "startRowIndex": 0, "endRowIndex": 1,
                      "startColumnIndex": 0, "endColumnIndex": len(HEADERS)},
            "cell": {"userEnteredFormat": {
                "backgroundColor": {"red": 0.19, "green": 0.25, "blue": 0.33},
                "textFormat": {"bold": True, "fontSize": 13,
                               "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
            }},
            "fields": "userEnteredFormat(backgroundColor,textFormat)",
        }},
        {"repeatCell": {
            "range": {"sheetId": ws.id, "startRowIndex": 2, "endRowIndex": 3,
                      "startColumnIndex": 0, "endColumnIndex": len(HEADERS)},
            "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
            "fields": "userEnteredFormat.textFormat",
        }},
        {"updateSheetProperties": {
            "properties": {"sheetId": ws.id, "gridProperties": {"frozenRowCount": 3}},
            "fields": "gridProperties.frozenRowCount",
        }},
        {"updateDimensionProperties": {
            "range": {"sheetId": ws.id, "dimension": "COLUMNS", "startIndex": 0, "endIndex": 8},
            "properties": {"pixelSize": 150},
            "fields": "pixelSize",
        }},
    ]})
    return len(tenants), master_id


def main():
    parser = argparse.ArgumentParser(description="Rebuild the all-cities roll-up.")
    parser.add_argument("--master", default=DEFAULT_MASTER_ID)
    args = parser.parse_args()
    count, master_id = refresh(args.master)
    print(f"[DONE] rolled up {count} city/cities")
    print(f"https://docs.google.com/spreadsheets/d/{master_id}/edit")
    print("\nFirst run: open it and click 'Allow access' on any #REF! cell —")
    print("IMPORTRANGE needs a one-time approval per source workbook.")


if __name__ == "__main__":
    main()
