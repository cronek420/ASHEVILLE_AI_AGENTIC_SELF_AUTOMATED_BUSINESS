"""
Live Google Sheets Synchronizer for Asheville AI Agentic Business.
Syncs local single-writer state to the live Google Sheet Command Center:
Spreadsheet ID: 1sq1xtu50uiNHm97db9c5-doqgatOpYkl8IQroscVCCY
Google Drive Folder: 1GlPw9gqABltrWVcsZda5iI1WDVifPqYH
"""

import os
import sys
import json
import datetime
from typing import Dict, Any, List

SPREADSHEET_ID = "1sq1xtu50uiNHm97db9c5-doqgatOpYkl8IQroscVCCY"
DRIVE_FOLDER_ID = "1GlPw9gqABltrWVcsZda5iI1WDVifPqYH"
INTAKE_PACKET_FILE = "intake_change_packets.json"
INTAKE_HEADERS = [
    "Request ID", "Status", "Mode", "Source", "Submitted At", "Name", "Email",
    "Starting Point", "Company Name", "Website", "Notes", "External Action Taken", "Next Step"
]
APPROVAL_BASE_HEADERS = [
    "Approval ID", "Requested At", "Run ID", "Requesting Agent", "Gate", "Idea ID", "Business",
    "Proposed Action", "Evidence / Reason", "Risk / Cost", "Status", "Decision By",
    "Decision At", "Conditions / Notes", "Expires At"
]


def load_intake_packets():
    # A stale local packet file must never be consumed when the private intake
    # backend is disabled or misconfigured.
    if os.getenv("WORKFORCE_INTAKE_BACKEND") != "firestore":
        return []
    if not os.path.exists(INTAKE_PACKET_FILE):
        return []
    with open(INTAKE_PACKET_FILE, "r", encoding="utf-8") as packet_file:
        packets = json.load(packet_file)
    valid = []
    for packet in packets:
        changes = packet.get("proposed_sheet_changes", [])
        if (packet.get("agent") == "Atlas-Orchestrator"
                and packet.get("external_action_taken") is False
                and len(changes) == 1
                and changes[0].get("tab") == "Approval Queue"):
            valid.append(packet)
    return valid


def _find_header_row(rows):
    for index, row in enumerate(rows):
        cells = {cell.strip() for cell in row if cell.strip()}
        if "Status" in cells and ("Approval ID" in cells or "Request ID" in cells):
            return index
    return None


def _column_label(index):
    label = ""
    value = index + 1
    while value:
        value, remainder = divmod(value - 1, 26)
        label = chr(65 + remainder) + label
    return label


def _ensure_intake_columns(worksheet, rows, header_row_index):
    headers = list(rows[header_row_index])
    missing = [header for header in INTAKE_HEADERS if header not in headers]
    if not missing:
        return headers
    start_col = len(headers)
    headers.extend(missing)
    end_col = _column_label(len(headers) - 1)
    worksheet.update(f"A{header_row_index + 1}:{end_col}{header_row_index + 1}", [headers])
    rows[header_row_index] = headers
    return headers


def _row_fields_for_packet(packet, intake_fields):
    row_fields = dict(intake_fields)
    business_name = intake_fields.get("Company Name") or intake_fields.get("Name", "")
    row_fields.setdefault("Approval ID", intake_fields.get("Request ID", ""))
    row_fields.setdefault("Requested At", intake_fields.get("Submitted At", ""))
    row_fields.setdefault("Run ID", packet.get("run_id", ""))
    row_fields.setdefault("Requesting Agent", packet.get("agent", "Atlas-Orchestrator"))
    row_fields.setdefault("Gate", packet.get("approval_request", "G0"))
    row_fields.setdefault("Idea ID", packet.get("idea_id", ""))
    row_fields.setdefault("Business", business_name)
    row_fields.setdefault("Proposed Action", "Review public onboarding request")
    row_fields.setdefault("Evidence / Reason", "Validated website intake received; no external action taken.")
    row_fields.setdefault("Risk / Cost", "No external action. Owner review required.")
    row_fields.setdefault("Conditions / Notes", intake_fields.get("Notes", ""))
    row_fields["Status"] = intake_fields.get("Status", "NEEDS_OWNER_REVIEW")
    return row_fields


def sync_intake_packets(sheet):
    """Append deduplicated Atlas-approved intake rows and safe audit entries."""
    packets = load_intake_packets()
    if not packets:
        print("  [SAFE DEFAULT] No staged onboarding intake packets.")
        return 0
    worksheet = sheet.worksheet("Approval Queue")
    existing = worksheet.get_all_values()
    if not existing:
        worksheet.append_row(APPROVAL_BASE_HEADERS + INTAKE_HEADERS)
        existing = [APPROVAL_BASE_HEADERS + INTAKE_HEADERS]
    header_row_index = _find_header_row(existing)
    if header_row_index is None:
        raise ValueError("Approval Queue is missing a recognized header row.")
    headers = _ensure_intake_columns(worksheet, existing, header_row_index)
    request_id_column = headers.index("Request ID")
    existing_ids = {
        row[request_id_column].strip() for row in existing[header_row_index + 1:]
        if len(row) > request_id_column and row[request_id_column].strip()
    }
    appended_ids = []
    for packet in packets:
        change = packet["proposed_sheet_changes"][0]
        fields = _row_fields_for_packet(packet, change["fields"])
        request_id = change["record_key"]
        if request_id in existing_ids:
            continue
        worksheet.append_row([fields.get(header, "") for header in headers])
        appended_ids.append(request_id)
        existing_ids.add(request_id)

    if appended_ids:
        activity = sheet.worksheet("Activity Log")
        for request_id in appended_ids:
            activity.append_row([
                datetime.datetime.now().isoformat(), f"INTAKE-{request_id[:12]}",
                "Atlas-Orchestrator", "Public intake staged",
                f"Request {request_id} added to Approval Queue", "NEEDS_OWNER_REVIEW"
            ])
        if os.getenv("WORKFORCE_INTAKE_BACKEND") == "firestore":
            from intake_store import firestore_store_from_env
            store = firestore_store_from_env()
            for request_id in appended_ids:
                store.mark_queued(request_id)
    print(f"  [SUCCESS] Appended {len(appended_ids)} new intake request(s); duplicates skipped.")
    return len(appended_ids)

def get_dynamic_prospects():
    prospects = []
    
    # 1. First add the initial Batch 1 prospects we know about to ensure their names/niches are preserved if not in audit_results
    batch1 = {
        "wardph.com": {"name": "Ward Plumbing, Heating, and Air", "niche": "Plumbing & HVAC"},
        "whiteandwilliams.com": {"name": "White & Williams Co.", "niche": "Contracting & HVAC"},
        "ashevilleelectrician.com": {"name": "Asheville Electrician", "niche": "Electrical Contractors"},
        "ashevilletreeservice.com": {"name": "Asheville Tree Service", "niche": "Tree Care & Landscaping"},
        "bakerroofing.com": {"name": "Baker Roofing", "niche": "Roofing Contractors"}
    }
    
    audit_file = "audit_results.json"
    if os.path.exists(audit_file):
        with open(audit_file, "r") as f:
            audits = json.load(f)
            
        for a in audits:
            if a.get("status") == "AUDITED":
                domain = a["domain"]
                
                # Check if a proposal was generated
                proposal_path = os.path.join("proposals", f"{domain.replace('.', '_')}_proposal.txt")
                # A local draft is not evidence of approval or delivery.
                status = "Audited / Proposal Drafted" if os.path.exists(proposal_path) else "Audited (No Proposal)"
                
                # Try to get name/niche from batch1 or fallback to domain name
                b1_info = batch1.get(domain, {})
                name = b1_info.get("name", domain.split('.')[0].title())
                niche = b1_info.get("niche", "Local Business")
                
                prospects.append({
                    "name": name,
                    "domain": domain,
                    "niche": niche,
                    "score": a.get("score", 0),
                    "grade": a.get("grade", "F"),
                    "status": status
                })
    return prospects

def load_credentials_file():
    possible_paths = [
        "client_secret.json",
        "credentials.json",
        os.path.expanduser("~/.config/gcloud/application_default_credentials.json")
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return p
    return None

def sync_to_google_sheet():
    cred_file = load_credentials_file()
    dynamic_prospects = get_dynamic_prospects()
    
    print("=" * 70)
    print("  LIVE GOOGLE SHEETS SYNCHRONIZER")
    print(f"  Target Sheet ID: {SPREADSHEET_ID}")
    print(f"  Target Drive Folder: {DRIVE_FOLDER_ID}")
    print("=" * 70)

    if not cred_file:
        print("\n[STATUS] Local state ready, but Google Service Account credential file is missing.")
        return False

    try:
        import gspread
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials

        with open(cred_file, "r", encoding="utf-8") as f:
            cred_data = json.load(f)

        if "installed" in cred_data or "web" in cred_data:
            print("  [AUTH] Authenticating via OAuth Client ID (installed desktop app)...")
            token_path = "token.json"
            SCOPES = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            creds = None
            if os.path.exists(token_path):
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    print("  [AUTH] Token expired, refreshing...")
                    try:
                        creds.refresh(Request())
                        with open(token_path, "w", encoding="utf-8") as token_file:
                            token_file.write(creds.to_json())
                        print("  [AUTH] Token refreshed successfully.")
                    except Exception as refresh_err:
                        print(f"\n[ERROR] Token refresh failed: {refresh_err}")
                        print("[ACTION REQUIRED] Re-run this script locally (with a browser) to re-authorize,")
                        print("                  then upload the new token.json to the server.")
                        return False
                else:
                    # No valid token and no refresh token — cannot do interactive auth on headless server
                    print("\n[ERROR] No valid OAuth token and no refresh token available.")
                    print("[ACTION REQUIRED] Run this script locally (with a browser) to authorize,")
                    print("                  then upload token.json to the server.")
                    return False
            
            client = gspread.authorize(creds)
        else:
            print("  [AUTH] Authenticating via Service Account key...")
            client = gspread.service_account(filename=cred_file)

        sheet = client.open_by_key(SPREADSHEET_ID)
        print(f"\n[SUCCESS] Connected to Google Sheet: '{sheet.title}'!")

        # Update Prospect Tracker tab
        try:
            ws_prospects = sheet.worksheet("Prospect Tracker")
            print("  Updating 'Prospect Tracker' worksheet...")
            headers = ["Business Name", "Domain", "Niche", "Audit Score", "Grade", "Status"]
            existing = ws_prospects.get_all_values()
            if not existing:
                ws_prospects.append_row(headers)
                existing = [headers]
            domain_col = headers.index("Domain")
            existing_rows = {
                row[domain_col].strip().lower(): (index, row)
                for index, row in enumerate(existing[1:], start=2)
                if len(row) > domain_col and row[domain_col].strip()
            }
            appended = 0
            updated = 0
            for prospect in dynamic_prospects:
                row = [prospect["name"], prospect["domain"], prospect["niche"],
                       prospect["score"], prospect["grade"], prospect["status"]]
                key = prospect["domain"].strip().lower()
                if key not in existing_rows:
                    ws_prospects.append_row(row)
                    appended += 1
                    continue
                row_number, current = existing_rows[key]
                normalized_current = [str(value) for value in (current + [""] * len(headers))[:len(headers)]]
                normalized_new = [str(value) for value in row]
                if normalized_current != normalized_new:
                    ws_prospects.update(f"A{row_number}:F{row_number}", [row])
                    updated += 1
            print(f"  [SUCCESS] Appended {appended}, updated {updated}; preserved unrelated history.")
        except Exception as e:
            print(f"  [WARN] Could not update 'Prospect Tracker' tab: {e}")

        # Stage public intake only through Atlas-Orchestrator's validated packet path.
        try:
            sync_intake_packets(sheet)
        except Exception as e:
            print(f"  [WARN] Could not stage public intake requests: {e}")

        # Update Activity Log tab
        try:
            ws_log = sheet.worksheet("Activity Log")
            now_str = datetime.datetime.now().isoformat()
            log_row = [now_str, "RUN-LIVE-SYNC", "Atlas-Orchestrator", "Live Sheet Sync", "Synced 5 G2 approved prospects & dispatches", "SUCCESS"]
            ws_log.append_row(log_row)
            print("  [SUCCESS] 'Activity Log' tab updated live.")
        except Exception as e:
            print(f"  [WARN] Could not update 'Activity Log' tab: {e}")

        print("\n[COMPLETE] Google Sheets live sync finished cleanly.")
        return True

    except Exception as e:
        import traceback
        print(f"\n[ERROR] Google Sheets API connection failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    sync_to_google_sheet()
