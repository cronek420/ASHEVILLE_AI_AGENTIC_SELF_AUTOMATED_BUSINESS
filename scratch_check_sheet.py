import agency_auth
import yaml

with open("tenants.yaml", "r", encoding="utf-8") as handle:
    config = (yaml.safe_load(handle) or {}).get("tenants", {}).get("asheville") or {}
spreadsheet_id = config.get("spreadsheet_id")
client = agency_auth.sheets_client(probe_spreadsheet_id=spreadsheet_id)
worksheet = client.open_by_key(spreadsheet_id).worksheet("Approval Queue")
rows = worksheet.get_all_values()

from live_sheets_sync import _find_headers
index = _find_headers(rows, {"Approval ID", "Status"})

print(f"Total rows in Approval Queue: {len(rows)}")
if index is not None:
    headers = rows[index]
    status_col = headers.index("Status") if "Status" in headers else -1
    domain_col = headers.index("Domain") if "Domain" in headers else -1
    for i, row in enumerate(rows[index+1:]):
        if row and len(row) > status_col:
            status = row[status_col]
            domain = row[domain_col] if len(row) > domain_col else ""
            if status or domain:
                print(f"Row {index+1+i}: Status={status}, Domain={domain}")
