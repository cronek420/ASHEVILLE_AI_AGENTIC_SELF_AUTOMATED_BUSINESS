import agency_auth
import yaml

with open("tenants.yaml", "r", encoding="utf-8") as handle:
    config = (yaml.safe_load(handle) or {}).get("tenants", {}).get("charlotte") or {}
spreadsheet_id = config.get("spreadsheet_id")
client = agency_auth.sheets_client(probe_spreadsheet_id=spreadsheet_id)
worksheet = client.open_by_key(spreadsheet_id).worksheet("Approval Queue")

rows = worksheet.get_all_values()
from live_sheets_sync import _find_headers
index = _find_headers(rows, {"Approval ID", "Status"})

print(f"Header index is {index}. Sheet has {len(rows)} rows.")

if index is not None:
    headers = rows[index]
    domain_col = headers.index("Domain") if "Domain" in headers else -1
    
    # We want to keep the header (row index) and maybe row index+1 (IDEA-01)
    # Then for rows index+2 to the end, if Domain is empty, we delete them.
    # To delete multiple rows safely, we iterate backwards.
    
    rows_to_delete = []
    # from index 5 (which is row 6) to len(rows)-1
    for i in range(len(rows) - 1, index + 1, -1):
        row = rows[i]
        domain = row[domain_col] if len(row) > domain_col else ""
        if not domain.strip():
            rows_to_delete.append(i + 1) # gspread is 1-indexed

    print(f"Found {len(rows_to_delete)} rows with empty domain to delete.")
    
    # Try batch deletion if possible, or delete one by one
    # If they are contiguous, we can delete them in one go
    # Since we go backwards, we can just delete them one by one, but that's slow.
    # Actually, the rows from index 5 to 209 are empty domain.
    # Let's find contiguous blocks to delete
    if rows_to_delete:
        # group contiguous
        blocks = []
        current_block = [rows_to_delete[0]]
        for r in rows_to_delete[1:]:
            if r == current_block[-1] - 1:
                current_block.append(r)
            else:
                blocks.append(current_block)
                current_block = [r]
        blocks.append(current_block)
        
        for block in blocks:
            start_row = block[-1]
            end_row = block[0] + 1
            print(f"Deleting rows {start_row} to {end_row - 1}")
            worksheet.delete_rows(start_row, end_row)
        
        print("Done deleting.")
