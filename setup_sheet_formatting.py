import yaml
import agency_auth
import gspread
from gspread.utils import a1_to_rowcol

VALID_STATUSES = [
    "Pending", "Approved", "Approved with Conditions", "Rejected", "Expired", "Cancelled"
]
VALID_GATES = [
    "G0 Setup", "G1 Launch", "G2 Outreach", "G3 Payment", "G4 Access & Publish", "G5 Pivot & Scale"
]

def format_sheet(tenant):
    print(f"Formatting {tenant}...")
    with open("tenants.yaml", "r", encoding="utf-8") as handle:
        config = (yaml.safe_load(handle) or {}).get("tenants", {}).get(tenant) or {}
    spreadsheet_id = config.get("spreadsheet_id")
    if not spreadsheet_id:
        print(f"No ID for {tenant}")
        return

    client = agency_auth.sheets_client(probe_spreadsheet_id=spreadsheet_id)
    sheet = client.open_by_key(spreadsheet_id)
    
    try:
        ws = sheet.worksheet("Approval Queue")
    except gspread.WorksheetNotFound:
        print(f"Approval Queue not found in {tenant}")
        return
        
    rows = ws.get_all_values()
    header_index = None
    for index, row in enumerate(rows):
        cells = {cell.strip() for cell in row if cell.strip()}
        if "Status" in cells and ("Approval ID" in cells or "Request ID" in cells):
            header_index = index
            break
            
    if header_index is None:
        print(f"Header not found in {tenant}")
        return
        
    headers = [cell.strip() for cell in rows[header_index]]
    
    # Freeze header rows
    # gspread uses 1-based indexing for freeze requests
    body = {
        "requests": [
            {
                "updateSheetProperties": {
                    "properties": {
                        "sheetId": ws.id,
                        "gridProperties": {
                            "frozenRowCount": header_index + 1
                        }
                    },
                    "fields": "gridProperties.frozenRowCount"
                }
            }
        ]
    }
    sheet.batch_update(body)
    
    # Add data validation to Status column
    status_col = headers.index("Status") if "Status" in headers else -1
    gate_col = headers.index("Gate") if "Gate" in headers else -1
    
    requests = []
    
    if status_col != -1:
        requests.append({
            "setDataValidation": {
                "range": {
                    "sheetId": ws.id,
                    "startRowIndex": header_index + 1,
                    "startColumnIndex": status_col,
                    "endColumnIndex": status_col + 1
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
        })
        
    if gate_col != -1:
        requests.append({
            "setDataValidation": {
                "range": {
                    "sheetId": ws.id,
                    "startRowIndex": header_index + 1,
                    "startColumnIndex": gate_col,
                    "endColumnIndex": gate_col + 1
                },
                "rule": {
                    "condition": {
                        "type": "ONE_OF_LIST",
                        "values": [{"userEnteredValue": g} for g in VALID_GATES]
                    },
                    "showCustomUi": True,
                    "strict": True
                }
            }
        })
        
    if requests:
        sheet.batch_update({"requests": requests})
        print(f"Data validation applied for {tenant}.")

if __name__ == "__main__":
    format_sheet("asheville")
    format_sheet("charlotte")
    print("Formatting complete.")
