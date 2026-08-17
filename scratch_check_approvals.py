import yaml
import agency_auth
import sheet_approvals

for tenant in ["asheville", "charlotte"]:
    print(f"\nChecking {tenant} sheet...")
    with open("tenants.yaml", "r", encoding="utf-8") as handle:
        config = (yaml.safe_load(handle) or {}).get("tenants", {}).get(tenant) or {}
    spreadsheet_id = config.get("spreadsheet_id")
    client = agency_auth.sheets_client(probe_spreadsheet_id=spreadsheet_id)
    worksheet = client.open_by_key(spreadsheet_id).worksheet("Approval Queue")
    
    rows, index, headers = sheet_approvals._header_index(worksheet)
    print(f"Header at index {index}")
    approved_count = 0
    for row in rows[index+1:]:
        if len(row) > 0:
            record = dict(zip(headers, list(row) + [""] * (len(headers) - len(row))))
            status = str(record.get("Status", "")).strip()
            domain = str(record.get("Domain", "")).strip()
            if domain:
                print(f"Domain: {domain}, Status: {status}")
                if status.lower() in sheet_approvals.APPROVED_STATUSES:
                    approved_count += 1
    
    print(f"{tenant} has {approved_count} approved rows.")

