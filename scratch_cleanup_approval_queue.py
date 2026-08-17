import agency_auth
import yaml
import time
import gspread

with open('tenants.yaml') as f:
    config = yaml.safe_load(f)

for tenant, t_config in config.get("tenants", {}).items():
    spreadsheet_id = t_config.get("spreadsheet_id")
    if not spreadsheet_id: continue
    
    print(f"Cleaning {tenant} Approval Queue...")
    client = agency_auth.sheets_client(probe_spreadsheet_id=spreadsheet_id)
    sheet = client.open_by_key(spreadsheet_id)
    
    try:
        ws = sheet.worksheet('Approval Queue')
    except Exception:
        continue
        
    rows = ws.get_all_values()
    if not rows: continue
    
    header_index = -1
    for i, r in enumerate(rows):
        if "Approval ID" in r and "Status" in r:
            header_index = i
            break
            
    if header_index == -1: continue
    
    headers = rows[header_index]
    
    from live_sheets_sync import APPROVAL_BASE_HEADERS, INTAKE_HEADERS
    from sheet_approvals import OUTREACH_HEADERS
    
    all_valid_headers = APPROVAL_BASE_HEADERS + INTAKE_HEADERS + OUTREACH_HEADERS
    
    col_mapping = {}
    for h in all_valid_headers:
        if h in headers:
            col_mapping[h] = headers.index(h)
            
    new_rows = []
    # Write the new headers (only valid ones)
    new_headers = [h for h in all_valid_headers if h in col_mapping]
    # To avoid changing the original spacing at the top
    for i in range(header_index):
        new_rows.append(rows[i][:len(new_headers)])
    
    new_rows.append(new_headers)
    
    # Write the data rows
    for r in rows[header_index + 1:]:
        new_row = []
        for h in new_headers:
            idx = col_mapping[h]
            new_row.append(r[idx] if idx < len(r) else "")
        if any(new_row):
            new_rows.append(new_row)
            
    # Clear the entire sheet
    ws.clear()
    
    # Update with new contiguous data
    print(f"Uploading {len(new_rows) - header_index - 1} cleaned data rows to {tenant}...")
    agency_auth.retry_api(ws.update, values=new_rows, range_name=f"A1")
    
    # Remove any excess columns from the worksheet itself to prevent horizontal scrolling
    try:
        if ws.col_count > len(new_headers):
            body = {
                "requests": [
                    {
                        "deleteDimension": {
                            "range": {
                                "sheetId": ws.id,
                                "dimension": "COLUMNS",
                                "startIndex": len(new_headers),
                                "endIndex": ws.col_count
                            }
                        }
                    }
                ]
            }
            sheet.batch_update(body)
    except Exception as e:
        print("Could not trim extra columns:", e)

    time.sleep(2)
    
print("Cleanup complete.")
