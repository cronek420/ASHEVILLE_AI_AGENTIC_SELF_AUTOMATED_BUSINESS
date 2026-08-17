"""
Syncs data from all cities to the Master Command Center sheet.
"""

import os
import yaml
import agency_auth
import datetime
import json
from live_sheets_sync import get_dynamic_prospects, _priority_for_grade, PROSPECT_HEADERS, _prospect_agent_fields, _normalize_site, _column_label, _find_headers, _ensure_headers, _last_used_row

def _sync_master_prospect_tracker(worksheet, prospects_by_tenant):
    """
    prospects_by_tenant: dict {tenant: [prospects]}
    """
    rows = worksheet.get_all_values()
    master_headers = ["City"] + PROSPECT_HEADERS
    header_index = _find_headers(rows, {"Website", "City", "Business"})
    
    if header_index is None:
        header_index = 0
        worksheet.update(values=[master_headers], range_name=f"A1:{_column_label(len(master_headers) - 1)}1")
        rows = [master_headers]
        
    headers = _ensure_headers(worksheet, rows, header_index, master_headers)
    key_col = headers.index("Website")
    city_col = headers.index("City")
    
    existing = {}
    for offset, row in enumerate(rows[header_index + 1:], start=header_index + 2):
        if len(row) > key_col and len(row) > city_col:
            key = _normalize_site(row[key_col])
            city = str(row[city_col]).strip().lower()
            if key and city:
                existing[(city, key)] = (offset, row)
                
    new_rows = []
    updated = 0
    batch_updates = []
    
    # We only update agent fields. Owner fields remain untouched.
    agent_headers = ["City", "Business", "Category", "Website", "Visible Issue", "Source", "Contact Channel", "Public Contact", "Personalized Idea", "Audit Score", "Grade", "Issues Found", "Top Opportunity", "Phone", "Email"]

    for tenant, prospects in prospects_by_tenant.items():
        for prospect in prospects:
            fields = _prospect_agent_fields(prospect)
            fields["City"] = tenant.title()
            
            key = _normalize_site(prospect.get("domain", ""))
            city_key = tenant.lower()
            if not key:
                continue
                
            if (city_key, key) not in existing:
                fields["Status"] = "Not Contacted"
                fields["Priority"] = _priority_for_grade(prospect.get("grade"))
                new_rows.append([str(fields.get(header, "")) for header in headers])
                existing[(city_key, key)] = None
                continue
                
            entry = existing[(city_key, key)]
            if entry is None:
                continue
                
            row_number, current = entry
            padded = list(current) + [""] * (len(headers) - len(current))
            changed = False
            for header in agent_headers:
                if header not in headers:
                    continue
                column = headers.index(header)
                new_value = str(fields.get(header, ""))
                if padded[column] != new_value:
                    padded[column] = new_value
                    changed = True
            if changed:
                end_col = _column_label(len(headers) - 1)
                batch_updates.append({
                    "range": f"A{row_number}:{end_col}{row_number}",
                    "values": [padded[:len(headers)]]
                })
                updated += 1
                
    if batch_updates:
        agency_auth.retry_api(worksheet.batch_update, batch_updates)
                
    if new_rows:
        start = max(_last_used_row(rows), header_index + 1) + 1
        end = start + len(new_rows) - 1
        row_count = getattr(worksheet, "row_count", None)
        if row_count is not None and row_count < end:
            agency_auth.retry_api(worksheet.add_rows, end - row_count)
        end_col = _column_label(len(headers) - 1)
        agency_auth.retry_api(worksheet.update, values=new_rows, range_name=f"A{start}:{end_col}{end}")
        
    return len(new_rows), updated

def sync_master_sheet():
    print("=" * 70)
    print("  LIVE GOOGLE SHEETS SYNCHRONIZER - MASTER SHEET")
    print("=" * 70)
    
    with open("tenants.yaml", "r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}
        
    master_config = config.get("master")
    if not master_config or not master_config.get("spreadsheet_id"):
        print("  [SKIP] No master sheet configured in tenants.yaml")
        return True
        
    master_id = master_config.get("spreadsheet_id")
    client = agency_auth.sheets_client(probe_spreadsheet_id=master_id)
    sheet = client.open_by_key(master_id)
    
    print(f"  [SUCCESS] Connected to Master Sheet: '{sheet.title}'!")
    
    tenants = list(config.get("tenants", {}).keys())
    prospects_by_tenant = {}
    
    for t in tenants:
        prospects_by_tenant[t] = get_dynamic_prospects(t)
        
    try:
        ws_prospects = sheet.worksheet("Master Prospect Tracker")
        print("  Updating 'Master Prospect Tracker' worksheet...")
        appended, updated = _sync_master_prospect_tracker(ws_prospects, prospects_by_tenant)
        print(f"  [SUCCESS] Appended {appended}, updated {updated} in Master Prospect Tracker.")
    except Exception as e:
        print(f"  [WARN] Could not update 'Master Prospect Tracker' tab: {e}")
        
    try:
        # Dashboard updates
        ws_dash = sheet.worksheet("Dashboard")
        # Compute metrics
        dashboard_rows = [["Agency Command Center - Master Dashboard"], ["City", "Audited", "Approved", "Sent"]]
        for t in tenants:
            prospects = prospects_by_tenant[t]
            audited = len(prospects)
            
            # Read approvals from local ledger or file
            sent_count = 0
            ledger_file = f"outreach_ledger_{t}.json"
            if os.path.exists(ledger_file):
                try:
                    with open(ledger_file, "r") as f:
                        ledger = json.load(f)
                        sent_count = len(ledger.get("events", []))
                except:
                    pass
                    
            dashboard_rows.append([t.title(), audited, "See Approval Queue", sent_count])
            
        agency_auth.retry_api(ws_dash.update, values=dashboard_rows, range_name=f"A1:D{len(dashboard_rows)}")
        print("  [SUCCESS] Dashboard metrics updated.")
    except Exception as e:
        print(f"  [WARN] Could not update 'Dashboard' tab: {e}")

if __name__ == "__main__":
    sync_master_sheet()
