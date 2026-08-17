"""
One-time setup: Clean the Charlotte Command Center sheet of copied Asheville data
and set up the Master Dashboard with IMPORTRANGE formulas.

Run from PowerShell in the project folder:
  python setup_charlotte_sheet.py
"""

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import gspread

ASHEVILLE_ID = "1sq1xtu50uiNHm97db9c5-doqgatOpYkl8IQroscVCCY"
CHARLOTTE_ID = "1I7KFUzBFPx70uR77WUvFORBSdcjvbdERAKL3YLLgVng"
MASTER_ID = "197dx4GwoB7t1bPfSY0UvSgXjUZbYIklph7VdixvulQ8"

creds = Credentials.from_authorized_user_file("token.json")
if not creds.valid:
    creds.refresh(Request())
gc = gspread.authorize(creds)

# --- STEP 1: Clean Charlotte sheet ---
print("=== Cleaning Charlotte Command Center ===")
charlotte = gc.open_by_key(CHARLOTTE_ID)

ws = charlotte.worksheet("Start Here")
ws.update(values=[["URGENT 24-48 HOUR CASH-FLOW BUSINESS COMMAND CENTER — CHARLOTTE NC"]], range_name="A1")
ws.update(values=[["Research date: 2026-08-07 | Goal: collect a legitimate deposit or paid task quickly | Charlotte NC market"]], range_name="A2")
print("  Start Here updated")

ws_pt = charlotte.worksheet("Prospect Tracker")
all_rows = ws_pt.get_all_values()
if len(all_rows) > 1:
    ws_pt.batch_clear([f"A2:J{len(all_rows)}"])
print(f"  Prospect Tracker cleared ({len(all_rows)-1} data rows removed)")

ws_al = charlotte.worksheet("Activity Log")
al_rows = ws_al.get_all_values()
if len(al_rows) > 3:
    ws_al.batch_clear([f"A4:F{len(al_rows)}"])
print("  Activity Log cleared")

ws_aq = charlotte.worksheet("Approval Queue")
aq_rows = ws_aq.get_all_values()
if len(aq_rows) > 4:
    last_col = chr(64 + min(ws_aq.col_count, 26))
    ws_aq.batch_clear([f"A5:{last_col}{len(aq_rows)}"])
print("  Approval Queue cleared")

ws_ld = charlotte.worksheet("Live Dashboard")
ws_ld.update(values=[["LIVE OPERATIONS DASHBOARD — CHARLOTTE NC"]], range_name="A1")
print("  Live Dashboard updated")

ws_cd = charlotte.worksheet("Client Delivery")
cd_rows = ws_cd.get_all_values()
if len(cd_rows) > 3:
    ws_cd.batch_clear([f"A4:O{len(cd_rows)}"])
print("  Client Delivery cleared")

print("  Charlotte sheet cleaned.\n")

# --- STEP 2: Set up Master Dashboard ---
print("=== Setting Up Master Dashboard ===")
master = gc.open_by_key(MASTER_ID)

ws_main = master.sheet1
ws_main.update_title("All Cities Dashboard")

headers = [
    ["MASTER DASHBOARD — ALL CITIES"],
    ["Live overview pulling data from each city's Command Center. Updated automatically via IMPORTRANGE."],
    [""],
    ["City", "Prospects", "Proposals Drafted", "Cash Collected", "Deals Won",
     "Approvals Waiting", "Last Agent Sync", "Sheet Link"],
]

asheville_row = [
    "Asheville NC",
    f'=IFERROR(COUNTA(IMPORTRANGE("{ASHEVILLE_ID}","Prospect Tracker!B2:B100")),0)',
    f'=IFERROR(COUNTIF(IMPORTRANGE("{ASHEVILLE_ID}","Prospect Tracker!F2:F100"),"*Proposal*"),0)',
    f'=IFERROR(IMPORTRANGE("{ASHEVILLE_ID}","Start Here!C16"),0)',
    f'=IFERROR(IMPORTRANGE("{ASHEVILLE_ID}","Start Here!C17"),0)',
    f'=IFERROR(IMPORTRANGE("{ASHEVILLE_ID}","Live Dashboard!B10"),0)',
    f'=IFERROR(IMPORTRANGE("{ASHEVILLE_ID}","Start Here!C11"),"—")',
    f"https://docs.google.com/spreadsheets/d/{ASHEVILLE_ID}/edit",
]

charlotte_row = [
    "Charlotte NC",
    f'=IFERROR(COUNTA(IMPORTRANGE("{CHARLOTTE_ID}","Prospect Tracker!B2:B100")),0)',
    f'=IFERROR(COUNTIF(IMPORTRANGE("{CHARLOTTE_ID}","Prospect Tracker!F2:F100"),"*Proposal*"),0)',
    f'=IFERROR(IMPORTRANGE("{CHARLOTTE_ID}","Start Here!C16"),0)',
    f'=IFERROR(IMPORTRANGE("{CHARLOTTE_ID}","Start Here!C17"),0)',
    f'=IFERROR(IMPORTRANGE("{CHARLOTTE_ID}","Live Dashboard!B10"),0)',
    f'=IFERROR(IMPORTRANGE("{CHARLOTTE_ID}","Start Here!C11"),"—")',
    f"https://docs.google.com/spreadsheets/d/{CHARLOTTE_ID}/edit",
]

totals_row = [
    "TOTALS",
    "=SUM(B5:B6)",
    "=SUM(C5:C6)",
    "=SUM(D5:D6)",
    "=SUM(E5:E6)",
    "=SUM(F5:F6)",
    "",
    "",
]

all_data = headers + [asheville_row, charlotte_row, [""], totals_row]
ws_main.update(values=all_data, range_name="A1", value_input_option="USER_ENTERED")
print("  Dashboard formulas written.")
print("  NOTE: You must open the Master Dashboard in your browser and click")
print("        'Allow access' on each IMPORTRANGE prompt for the formulas to work.")

print(f"\n=== DONE ===")
print(f"Charlotte Command Center: https://docs.google.com/spreadsheets/d/{CHARLOTTE_ID}/edit")
print(f"Master Dashboard:         https://docs.google.com/spreadsheets/d/{MASTER_ID}/edit")
print(f"\nNext: update tenants.yaml with Charlotte's spreadsheet_id: {CHARLOTTE_ID}")
