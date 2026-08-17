import yaml
import agency_auth
import gspread

def init_master():
    print("Authenticating with Google Sheets...")
    client = agency_auth.sheets_client()
    
    print("Creating Master Command Center spreadsheet...")
    sheet = client.create("Agency Command Center - Master")
    
    print(f"Spreadsheet created. ID: {sheet.id}")
    print("Sharing spreadsheet with owners...")
    
    for email in ["lexiconatlas@gmail.com", "gronekthomas@gmail.com"]:
        try:
            sheet.share(email, perm_type='user', role='writer')
            print(f"Shared with {email}")
        except Exception as e:
            print(f"Could not share with {email}: {e}")
            
    print("Setting up tabs...")
    # Dashboard
    dashboard = sheet.sheet1
    dashboard.update_title("Dashboard")
    dashboard.update(values=[["Agency Command Center - Master Dashboard"], ["City", "Audited", "Approved", "Sent"]], range_name="A1:D2")
    
    # Master Approval Queue
    approval_queue = sheet.add_worksheet(title="Master Approval Queue", rows=1000, cols=20)
    approval_headers = [
        "City", "Approval ID", "Requested At", "Run ID", "Requesting Agent", "Gate", "Idea ID", "Business",
        "Proposed Action", "Evidence / Reason", "Risk / Cost", "Status", "Decision By",
        "Decision At", "Conditions / Notes", "Expires At"
    ]
    approval_queue.update(values=[approval_headers], range_name="A1:P1")
    
    # Add Data Validation for Status
    VALID_STATUSES = ["Pending", "Approved", "Approved with Conditions", "Rejected", "Expired", "Cancelled"]
    body = {
        "requests": [
            {
                "setDataValidation": {
                    "range": {
                        "sheetId": approval_queue.id,
                        "startRowIndex": 1,
                        "startColumnIndex": approval_headers.index("Status"),
                        "endColumnIndex": approval_headers.index("Status") + 1
                    },
                    "rule": {
                        "condition": {
                            "type": "ONE_OF_LIST",
                            "values": [{"userEnteredValue": s} for s in VALID_STATUSES]
                        },
                        "showCustomUi": True,
                        "strict": True
                    }
                }
            }
        ]
    }
    sheet.batch_update(body)
    
    # Master Prospect Tracker
    prospect_tracker = sheet.add_worksheet(title="Master Prospect Tracker", rows=1000, cols=20)
    prospect_headers = [
        "City", "Business", "Category", "Website", "Visible Issue", "Source", "Contact Channel",
        "Public Contact", "Personalized Idea", "Priority", "Date Contacted", "Status",
        "Follow-Up Date", "Quoted Price", "Deposit Requested", "Audit Score", "Grade", "Issues Found", "Top Opportunity", "Phone", "Email"
    ]
    prospect_tracker.update(values=[prospect_headers], range_name="A1:U1")
    
    print("Updating tenants.yaml...")
    with open("tenants.yaml", "r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}
        
    config["master"] = {
        "spreadsheet_id": sheet.id
    }
    
    with open("tenants.yaml", "w", encoding="utf-8") as handle:
        yaml.safe_dump(config, handle, sort_keys=False)
        
    print("Master Sheet initialized successfully!")
    print(f"URL: https://docs.google.com/spreadsheets/d/{sheet.id}/edit")

if __name__ == "__main__":
    init_master()
