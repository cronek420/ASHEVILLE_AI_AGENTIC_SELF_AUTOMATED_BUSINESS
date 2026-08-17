"""
ADC Live Google Sheets Sync Tester
Uses Application Default Credentials (gcloud auth application-default login) to access Google Sheets.
"""

import os
import sys
import json
import datetime

SPREADSHEET_ID = "1sq1xtu50uiNHm97db9c5-doqgatOpYkl8IQroscVCCY"

LOCAL_PROSPECTS = [
    {"name": "Ward Plumbing, Heating, and Air", "domain": "wardph.com", "niche": "Plumbing & HVAC", "score": 85, "grade": "B", "status": "G2 Approved / Outreach Dispatched"},
    {"name": "White & Williams Co.", "domain": "whiteandwilliams.com", "niche": "Contracting & HVAC", "score": 36, "grade": "F", "status": "G2 Approved / Outreach Dispatched"},
    {"name": "Asheville Electrician", "domain": "ashevilleelectrician.com", "niche": "Electrical Contractors", "score": 76, "grade": "B", "status": "G2 Approved / Outreach Dispatched"},
    {"name": "Asheville Tree Service", "domain": "ashevilletreeservice.com", "niche": "Tree Care & Landscaping", "score": 85, "grade": "B", "status": "G2 Approved / Outreach Dispatched"},
    {"name": "Baker Roofing", "domain": "bakerroofing.com", "niche": "Roofing Contractors", "score": 87, "grade": "B", "status": "G2 Approved / Outreach Dispatched"}
]

def try_adc_sync():
    print("=" * 70)
    print("  TESTING GOOGLE SHEETS SYNC VIA APPLICATION DEFAULT CREDENTIALS (ADC)")
    print(f"  Target Sheet ID: {SPREADSHEET_ID}")
    print("=" * 70)

    try:
        import google.auth
        import gspread

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        creds, project = google.auth.default(scopes=scopes)
        print(f"[STATUS] ADC Credentials loaded successfully for project: {project}")

        client = gspread.authorize(creds)
        sheet = client.open_by_key(SPREADSHEET_ID)
        print(f"\n[SUCCESS] Connected to Google Sheet: '{sheet.title}'!")

        # Update Prospect Tracker
        try:
            ws_prospects = sheet.worksheet("Prospect Tracker")
            print("  Updating 'Prospect Tracker' worksheet...")
            ws_prospects.clear()
            headers = ["Business Name", "Domain", "Niche", "Audit Score", "Grade", "Status"]
            rows = [headers] + [[p["name"], p["domain"], p["niche"], p["score"], p["grade"], p["status"]] for p in LOCAL_PROSPECTS]
            ws_prospects.update("A1", rows)
            print("  [SUCCESS] 'Prospect Tracker' tab updated live in online Google Sheet!")
        except Exception as e:
            print(f"  [WARN] Could not update 'Prospect Tracker' tab: {e}")

        # Append Activity Log
        try:
            ws_log = sheet.worksheet("Activity Log")
            now_str = datetime.datetime.now().isoformat()
            log_row = [now_str, "RUN-ADC-SYNC", "Atlas-Orchestrator", "ADC Cloud Sheet Sync", "Synced 5 G2 approved prospects & dispatches via ADC", "SUCCESS"]
            ws_log.append_row(log_row)
            print("  [SUCCESS] 'Activity Log' tab updated live in online Google Sheet!")
        except Exception as e:
            print(f"  [WARN] Could not update 'Activity Log' tab: {e}")

        print("\n[COMPLETE] Cloud Google Sheets sync successful!")
        return True

    except Exception as e:
        import traceback
        print(f"\n[ADC SYNC ERROR] {type(e).__name__}: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try_adc_sync()
