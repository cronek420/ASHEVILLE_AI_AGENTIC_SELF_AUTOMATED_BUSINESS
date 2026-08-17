import yaml
import agency_auth

def check_dropdowns(tenant):
    with open("tenants.yaml", "r", encoding="utf-8") as handle:
        config = (yaml.safe_load(handle) or {}).get("tenants", {}).get(tenant) or {}
    spreadsheet_id = config.get("spreadsheet_id")
    client = agency_auth.sheets_client(probe_spreadsheet_id=spreadsheet_id)
    sheet = client.open_by_key(spreadsheet_id)
    
    # We can fetch the raw spreadsheet metadata to check for data validation rules
    metadata = sheet.fetch_sheet_metadata()
    print(f"\n--- {tenant} Sheet Metadata ---")
    for ws in metadata.get('sheets', []):
        if ws['properties']['title'] == 'Approval Queue':
            print(f"Approval Queue Sheet ID: {ws['properties']['sheetId']}")
            # Data validation rules are usually inside the cells, which requires a grid data request
            break
            
check_dropdowns("asheville")
check_dropdowns("charlotte")
