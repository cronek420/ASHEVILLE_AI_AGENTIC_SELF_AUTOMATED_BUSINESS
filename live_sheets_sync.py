"""
Live Google Sheets Synchronizer for Asheville AI Agentic Business.
Syncs local single-writer state to the live Google Sheet Command Center.
Per-tenant spreadsheet ids live in tenants.yaml.
Google Drive Folder: 14bNYctr5hoYcOhSCdWXOvPMS6qVMru10
"""

import os
import sys
import json
import datetime
import yaml
from typing import Dict, Any, List

import agency_auth

def get_tenant_config(tenant):
    try:
        with open("tenants.yaml", "r") as f:
            data = yaml.safe_load(f)
            return data.get("tenants", {}).get(tenant, {})
    except FileNotFoundError:
        return {}

DRIVE_FOLDER_ID = "14bNYctr5hoYcOhSCdWXOvPMS6qVMru10"

SYNC_RESULT_FILE = "sync_result_{tenant}.json"


def _write_sync_result(tenant, payload):
    """
    Leave a machine-readable record of what this sync actually wrote.

    daily_reporter.py reads it so the owner email can report real numbers and
    call out a run that touched nothing. Written on failure too: "we tried and
    wrote zero rows" is precisely the signal that went unnoticed for three days.
    """
    try:
        with open(SYNC_RESULT_FILE.format(tenant=tenant), "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
    except OSError as exc:
        print(f"  [WARN] Could not record the sync result: {exc}")


HIGHLIGHT_STATE_FILE = "highlighted_{tenant}.json"
# Light red: readable with black text, unmistakable at a glance on a phone.
FLAG_COLOR = {"red": 0.96, "green": 0.80, "blue": 0.80}
CLEAR_COLOR = {"red": 1.0, "green": 1.0, "blue": 1.0}


def highlight_flagged_rows(worksheet, rows, header_index, flagged_domains, tenant):
    """
    Turn the Prospect Tracker row red for any prospect that needs a human look.

    Only rows this function itself coloured are ever cleared — tracked in
    highlighted_<tenant>.json — so a blanket reformat can never wipe formatting
    Tom applied by hand.
    """
    headers = rows[header_index]
    try:
        website_col = headers.index("Website")
    except ValueError:
        return 0, 0

    previous = set()
    state_path = HIGHLIGHT_STATE_FILE.format(tenant=tenant)
    try:
        with open(state_path, "r", encoding="utf-8") as handle:
            previous = set(json.load(handle) or [])
    except (OSError, json.JSONDecodeError):
        pass

    wanted = {str(d).strip().lower() for d in flagged_domains if str(d).strip()}
    row_of = {}
    for offset, row in enumerate(rows[header_index + 1:], start=header_index + 2):
        if website_col < len(row):
            site = str(row[website_col]).strip().lower()
            if site:
                row_of.setdefault(site, offset)

    end_col = _column_label(max(len(headers) - 1, 0))
    to_flag = [row_of[d] for d in wanted if d in row_of]
    to_clear = [row_of[d] for d in (previous - wanted) if d in row_of]

    formats = []
    for row_number in to_flag:
        formats.append({"range": f"A{row_number}:{end_col}{row_number}", "format": {"backgroundColor": FLAG_COLOR}})
    for row_number in to_clear:
        formats.append({"range": f"A{row_number}:{end_col}{row_number}", "format": {"backgroundColor": CLEAR_COLOR}})

    if formats:
        try:
            agency_auth.retry_api(worksheet.batch_format, formats)
        except Exception as exc:
            print(f"  [WARN] could not batch_format rows: {exc}")

    try:
        with open(state_path, "w", encoding="utf-8") as handle:
            json.dump(sorted(wanted), handle, indent=2)
    except OSError:
        pass

    return len(to_flag), len(to_clear)


def read_sync_result(tenant):
    """The last recorded sync outcome for a tenant, or None if never recorded."""
    try:
        with open(SYNC_RESULT_FILE.format(tenant=tenant), "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None

# --- Prospect Tracker contract -------------------------------------------------
# The workbook template owns the outreach/money columns; the pipeline owns the
# research/audit columns. Rows are matched on Website, and a sync NEVER writes an
# owner-owned column on a row that already exists — otherwise a nightly run would
# erase the follow-up dates and quoted prices Tom typed in by hand.
PROSPECT_TEMPLATE_HEADERS = [
    "Business", "Category", "Website", "Visible Issue", "Source", "Contact Channel",
    "Public Contact", "Personalized Idea", "Priority", "Date Contacted", "Status",
    "Follow-Up Date", "Quoted Price", "Deposit Requested",
]
PROSPECT_AUDIT_HEADERS = [
    "Audit Score", "Grade", "Issues Found", "Top Opportunity", "Phone", "Email",
]
PROSPECT_HEADERS = PROSPECT_TEMPLATE_HEADERS + PROSPECT_AUDIT_HEADERS
PROSPECT_KEY_HEADER = "Website"
# Written by the pipeline on both append and update.
PROSPECT_AGENT_HEADERS = [
    "Business", "Category", "Website", "Visible Issue", "Source", "Contact Channel",
    "Public Contact", "Personalized Idea",
] + PROSPECT_AUDIT_HEADERS
# Seeded once on append, then left alone for the owner to manage.
PROSPECT_OWNER_HEADERS = [
    "Priority", "Date Contacted", "Status", "Follow-Up Date", "Quoted Price",
    "Deposit Requested",
]
INTAKE_PACKET_FILE = "intake_change_packets.json"

# --- Approval Queue vocabulary -------------------------------------------------
# The workbook's Gate and Status columns are typed DROPDOWN columns. A value
# outside the list is rejected by the cell and cannot be filtered or colour-coded,
# so the pipeline must write the workbook's labels, not its own shorthand.
GATE_LABELS = {
    "G0": "G0 Setup",
    "G1": "G1 Launch",
    "G2": "G2 Outreach",
    "G3": "G3 Payment",
    "G4": "G4 Access & Publish",
    "G5": "G5 Pivot & Scale",
}
APPROVAL_QUEUE_STATUSES = [
    "Pending", "Approved", "Approved with Conditions", "Rejected", "Expired", "Cancelled",
]
# Internal intake states that mean "a human has not decided yet".
WAITING_STATES = {"NEEDS_OWNER_REVIEW", "PENDING", "QUEUED", ""}


def gate_label(gate):
    """Map internal gate shorthand (G2) to the workbook dropdown label."""
    key = str(gate or "").strip()
    return GATE_LABELS.get(key.upper(), key)


def approval_status_label(status):
    """
    Map an internal intake state to a valid Approval Queue dropdown value.

    Anything not already a workbook status is treated as still awaiting the
    owner, which is the safe direction: it can never read as approved.
    """
    text = str(status or "").strip()
    for known in APPROVAL_QUEUE_STATUSES:
        if text.lower() == known.lower():
            return known
    if text.upper() in WAITING_STATES:
        return "Pending"
    return "Pending"
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


def _normalize_site(value):
    """Compare websites by bare domain so http/https/www/trailing-slash all match."""
    text = str(value or "").strip().lower()
    for prefix in ("https://", "http://"):
        if text.startswith(prefix):
            text = text[len(prefix):]
    if text.startswith("www."):
        text = text[4:]
    return text.rstrip("/")


def _find_headers(rows, required):
    """
    Locate a header row by its content rather than assuming row 1.

    The workbook templates put a title and a description above the real header,
    so a positional assumption silently writes data into the wrong columns.
    """
    required = set(required)
    for index, row in enumerate(rows):
        cells = {cell.strip() for cell in row if cell.strip()}
        if required.issubset(cells):
            return index
    return None


def _ensure_headers(worksheet, rows, header_index, wanted):
    """Append any missing columns to an existing header row, preserving order."""
    headers = [cell.strip() for cell in rows[header_index]]
    while headers and not headers[-1]:
        headers.pop()
    missing = [header for header in wanted if header not in headers]
    if missing:
        headers.extend(missing)
        end_col = _column_label(len(headers) - 1)
        agency_auth.retry_api(
            worksheet.update,
            values=[headers],
            range_name=f"A{header_index + 1}:{end_col}{header_index + 1}",
        )
    return headers


def _last_used_row(rows):
    """1-based index of the last row holding any value, or 0 when empty."""
    last = 0
    for index, row in enumerate(rows, start=1):
        if any(str(cell).strip() for cell in row):
            last = index
    return last


def _priority_for_grade(grade):
    return {"A": "High", "B": "High", "C": "Medium"}.get(str(grade).strip().upper(), "Low")


def _prospect_agent_fields(prospect):
    """The columns the pipeline is authorized to write."""
    email = prospect.get("email", "")
    phone = prospect.get("phone", "")
    issues = str(prospect.get("issues", "") or "0")
    return {
        "Business": prospect.get("name", ""),
        "Category": prospect.get("niche", ""),
        "Website": prospect.get("domain", ""),
        "Visible Issue": f"{issues} issue(s) found in automated audit",
        "Source": "Automated website audit",
        "Contact Channel": "Email" if email else ("Phone" if phone else "Unknown"),
        "Public Contact": email or phone,
        "Personalized Idea": prospect.get("top_opportunity", ""),
        "Audit Score": prospect.get("score", ""),
        "Grade": prospect.get("grade", ""),
        "Issues Found": issues,
        "Top Opportunity": prospect.get("top_opportunity", ""),
        "Phone": phone,
        "Email": email,
    }


def sync_prospect_tracker(worksheet, prospects):
    """
    Upsert audited prospects, matched on Website.

    Returns (appended, updated). Owner-owned columns are seeded on append and
    never touched afterwards, so hand-entered follow-up dates, quoted prices and
    deposit amounts survive every subsequent run.
    """
    rows = worksheet.get_all_values()
    header_index = _find_headers(rows, {PROSPECT_KEY_HEADER, "Business"})

    if header_index is None:
        # Legacy flat layout (Business Name / Domain / ...) or an empty tab.
        header_index = _find_headers(rows, {"Domain", "Business Name"})
        if header_index is None:
            header_index = 0
            worksheet.update(
                values=[PROSPECT_HEADERS],
                range_name=f"A1:{_column_label(len(PROSPECT_HEADERS) - 1)}1",
            )
            rows = [PROSPECT_HEADERS]
        else:
            raise ValueError(
                "Prospect Tracker uses the legacy flat layout; run the workbook "
                "normalizer before syncing so columns are not written misaligned."
            )

    headers = _ensure_headers(worksheet, rows, header_index, PROSPECT_HEADERS)
    key_col = headers.index(PROSPECT_KEY_HEADER)

    existing = {}
    for offset, row in enumerate(rows[header_index + 1:], start=header_index + 2):
        if len(row) > key_col:
            key = _normalize_site(row[key_col])
            if key:
                existing[key] = (offset, row)

    new_rows = []
    updated = 0
    batch_updates = []
    for prospect in prospects:
        fields = _prospect_agent_fields(prospect)
        key = _normalize_site(prospect.get("domain", ""))
        if not key:
            continue

        if key not in existing:
            fields["Status"] = "Not Contacted"
            fields["Priority"] = _priority_for_grade(prospect.get("grade"))
            new_rows.append([str(fields.get(header, "")) for header in headers])
            existing[key] = None  # queued in this batch; do not append twice
            continue

        entry = existing[key]
        if entry is None:
            continue

        row_number, current = entry
        padded = list(current) + [""] * (len(headers) - len(current))
        changed = False
        for header in PROSPECT_AGENT_HEADERS:
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
        # A per-row append_row loop is unsafe here: the templates pre-fill rows to
        # the bottom of the grid, so the append target does not advance and each
        # write lands on the same row, silently keeping only the last prospect.
        start = max(_last_used_row(rows), header_index + 1) + 1
        end = start + len(new_rows) - 1
        row_count = getattr(worksheet, "row_count", None)
        if row_count is not None and row_count < end:
            agency_auth.retry_api(worksheet.add_rows, end - row_count)
        end_col = _column_label(len(headers) - 1)
        agency_auth.retry_api(worksheet.update, values=new_rows, range_name=f"A{start}:{end_col}{end}")

    return len(new_rows), updated


def _ensure_intake_columns(worksheet, rows, header_row_index):
    headers = list(rows[header_row_index])
    missing = [header for header in INTAKE_HEADERS if header not in headers]
    if not missing:
        return headers
    start_col = len(headers)
    headers.extend(missing)
    end_col = _column_label(len(headers) - 1)
    agency_auth.retry_api(worksheet.update, range_name=f"A{header_row_index + 1}:{end_col}{header_row_index + 1}", values=[headers])
    rows[header_row_index] = headers
    return headers


def _row_fields_for_packet(packet, intake_fields):
    row_fields = dict(intake_fields)
    business_name = intake_fields.get("Company Name") or intake_fields.get("Name", "")
    row_fields.setdefault("Approval ID", intake_fields.get("Request ID", ""))
    row_fields.setdefault("Requested At", intake_fields.get("Submitted At", ""))
    row_fields.setdefault("Run ID", packet.get("run_id", ""))
    row_fields.setdefault("Requesting Agent", packet.get("agent", "Atlas-Orchestrator"))
    row_fields.setdefault("Gate", gate_label(packet.get("approval_request") or "G0"))
    row_fields.setdefault("Idea ID", packet.get("idea_id", ""))
    row_fields.setdefault("Business", business_name)
    row_fields.setdefault("Proposed Action", "Review public onboarding request")
    row_fields.setdefault("Evidence / Reason", "Validated website intake received; no external action taken.")
    row_fields.setdefault("Risk / Cost", "No external action. Owner review required.")
    raw_status = str(intake_fields.get("Status", "") or "").strip()
    note = intake_fields.get("Notes", "")
    if raw_status and raw_status.upper() in WAITING_STATES and raw_status != "Pending":
        note = f"{note} [intake state: {raw_status}]".strip()
    row_fields.setdefault("Conditions / Notes", note)
    # The raw intake state is preserved in Conditions / Notes above; the Status
    # column must hold a workbook dropdown value so the owner can filter, colour
    # and approve it from the dropdown.
    row_fields["Status"] = approval_status_label(intake_fields.get("Status"))
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
        agency_auth.retry_api(worksheet.append_row, APPROVAL_BASE_HEADERS + INTAKE_HEADERS)
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
    rows_to_append = []
    for packet in packets:
        change = packet["proposed_sheet_changes"][0]
        fields = _row_fields_for_packet(packet, change["fields"])
        request_id = change["record_key"]
        if request_id in existing_ids:
            continue
        rows_to_append.append([fields.get(header, "") for header in headers])
        appended_ids.append(request_id)
        existing_ids.add(request_id)

    if rows_to_append:
        agency_auth.retry_api(worksheet.append_rows, rows_to_append)

    if appended_ids:
        if appended_ids:
            activity = sheet.worksheet("Activity Log")
            log_rows = []
            for request_id in appended_ids:
                log_rows.append([
                    datetime.datetime.now().isoformat(), f"INTAKE-{request_id[:12]}",
                    "Atlas-Orchestrator", "Public intake staged",
                    f"Request {request_id} added to Approval Queue", "NEEDS_OWNER_REVIEW"
                ])
            if log_rows:
                agency_auth.retry_api(activity.append_rows, log_rows)
        if os.getenv("WORKFORCE_INTAKE_BACKEND") == "firestore":
            from intake_store import firestore_store_from_env
            store = firestore_store_from_env()
            for request_id in appended_ids:
                store.mark_queued(request_id)
    print(f"  [SUCCESS] Appended {len(appended_ids)} new intake request(s); duplicates skipped.")
    return len(appended_ids)

def get_dynamic_prospects(tenant):
    prospects = []
    
    # Known business names and niches for recognized domains
    known_names = {
        "wardph.com": ("Ward Plumbing, Heating, and Air", "Plumbing & HVAC"),
        "whiteandwilliams.com": ("White & Williams Co.", "Contracting & HVAC"),
        "ashevilleelectrician.com": ("Asheville Electrician", "Electrical Contractors"),
        "ashevilletreeservice.com": ("Asheville Tree Service", "Tree Care & Landscaping"),
        "bakerroofing.com": ("Baker Roofing", "Roofing Contractors"),
        "ashevillepressurewashing.com": ("Asheville Pressure Washing", "Pressure Washing"),
        "ashevillelawncare.com": ("Asheville Lawn Care", "Lawn Care & Landscaping"),
        "ashevillepestcontrol.com": ("Asheville Pest Control", "Pest Control"),
        "ashevillefamilydentistry.com": ("Asheville Family Dentistry", "Dental Practice"),
        "wncsoftwash.com": ("WNC Soft Wash", "Exterior Cleaning"),
        "gibsonpest.com": ("Gibson Pest Control", "Pest Control"),
    }
    
    audit_file = f"audit_results_{tenant}.json"
    if os.path.exists(audit_file):
        with open(audit_file, "r") as f:
            audits = json.load(f)
            
        for a in audits:
            if a.get("status") == "AUDITED":
                domain = a["domain"]
                
                # Check if a proposal was generated
                proposal_path = os.path.join(f"proposals_{tenant}", f"{domain.replace('.', '_')}_proposal.txt")
                status = "Audited / Proposal Drafted" if os.path.exists(proposal_path) else "Audited (No Proposal)"
                
                # Get name/niche from known list or fallback
                name_info = known_names.get(domain, (domain.split('.')[0].title(), "Local Business"))
                name, niche = name_info
                
                # Extract contact info
                contacts = a.get("contacts", {})
                tel_links = contacts.get("tel_links", [])
                phones = contacts.get("phones", [])
                emails = contacts.get("emails", [])
                phone = tel_links[0].replace("tel:", "") if tel_links else (phones[0] if phones else "")
                email = emails[0] if emails else ""
                
                issues = a.get("issues", [])
                opportunities = a.get("opportunities", [])
                top_opp = opportunities[0] if opportunities else ""
                
                prospects.append({
                    "name": name,
                    "domain": domain,
                    "niche": niche,
                    "score": a.get("score", 0),
                    "grade": a.get("grade", "F"),
                    "status": status,
                    "issues": str(len(issues)),
                    "top_opportunity": top_opp,
                    "phone": phone,
                    "email": email,
                })
    return prospects

def load_credentials_file():
    possible_paths = [
        "client_secret.json",
        "credentials.json",
        "/secrets/client/client_secret.json",
        "/secrets/client/credentials.json",
        os.path.expanduser("~/.config/gcloud/application_default_credentials.json")
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return p
    return None

def sync_to_google_sheet(tenant):
    config = get_tenant_config(tenant)
    spreadsheet_id = config.get("spreadsheet_id")
    
    if not spreadsheet_id:
        print(f"\n[ERROR] No spreadsheet_id configured for tenant '{tenant}' in tenants.yaml.")
        return False

    cred_file = load_credentials_file()
    dynamic_prospects = get_dynamic_prospects(tenant)
    
    print("=" * 70)
    print("  LIVE GOOGLE SHEETS SYNCHRONIZER")
    print(f"  Tenant: {tenant}")
    print(f"  Target Sheet ID: {spreadsheet_id}")
    print(f"  Target Drive Folder: {DRIVE_FOLDER_ID}")
    print("=" * 70)

    # In Cloud Run the job's own service account is used, so no credential file
    # is needed. Only the local OAuth path depends on one.
    if not cred_file and not agency_auth.running_in_cloud_run():
        print("\n[STATUS] Local state ready, but the Google credential file is missing.")
        return False

    try:
        import gspread

        if agency_auth.running_in_cloud_run():
            client = agency_auth.sheets_client(probe_spreadsheet_id=spreadsheet_id)
        else:
            with open(cred_file, "r", encoding="utf-8") as f:
                cred_data = json.load(f)

            if "installed" in cred_data or "web" in cred_data:
                print("  [AUTH] Authenticating via OAuth Client ID (installed desktop app)...")
                try:
                    client = gspread.authorize(agency_auth.oauth_credentials())
                except (FileNotFoundError, RuntimeError) as auth_err:
                    print(f"\n[ERROR] {auth_err}")
                    print("[ACTION REQUIRED] Run this script locally (with a browser) to authorize.")
                    return False
            else:
                print("  [AUTH] Authenticating via Service Account key...")
                client = gspread.service_account(filename=cred_file)

        sheet = client.open_by_key(spreadsheet_id)
        print(f"\n[SUCCESS] Connected to Google Sheet: '{sheet.title}'!")

        # Real counts, so the Activity Log and the daily report can both state
        # what happened rather than asserting a fixed sentence.
        appended = updated = 0
        prospects_written = False
        try:
            ws_prospects = sheet.worksheet("Prospect Tracker")
            print("  Updating 'Prospect Tracker' worksheet...")
            appended, updated = sync_prospect_tracker(ws_prospects, dynamic_prospects)
            prospects_written = True
            print(f"  [SUCCESS] Appended {appended}, updated {updated}; "
                  "owner-owned columns and unrelated history preserved.")

            # Anything a human must look at before it can be sent goes red.
            try:
                import proposal_engine

                flagged = proposal_engine.flagged_domains(tenant)
                fresh_rows = ws_prospects.get_all_values()
                header_index = _find_headers(fresh_rows, {"Website", "Business"})
                if header_index is not None:
                    lit, cleared = highlight_flagged_rows(
                        ws_prospects, fresh_rows, header_index, flagged, tenant)
                    if lit or cleared:
                        print(f"  [REVIEW] {lit} row(s) highlighted red, "
                              f"{cleared} cleared.")
            except Exception as exc:
                print(f"  [WARN] Could not update review highlighting: {exc}")
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
            # This row is audit evidence. It previously claimed "Synced 5 G2
            # approved prospects & dispatches" on every run no matter what
            # happened — worse than no log line, because a fixed number reads
            # as a measurement.
            if prospects_written:
                detail = f"Prospect Tracker: appended {appended}, updated {updated}"
                outcome = "SUCCESS"
            else:
                detail = "Prospect Tracker: not updated — see the run log"
                outcome = "PARTIAL"
            agency_auth.retry_api(
                ws_log.append_row,
                [now_str, "RUN-LIVE-SYNC", "Atlas-Orchestrator",
                               "Live Sheet Sync", detail, outcome]
            )
            print("  [SUCCESS] 'Activity Log' tab updated live.")
        except Exception as e:
            print(f"  [WARN] Could not update 'Activity Log' tab: {e}")

        _write_sync_result(tenant, {
            "ok": prospects_written,
            "appended": appended,
            "updated": updated,
            "sheet_title": sheet.title,
            "finished_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        })

        if not prospects_written:
            print("\n[INCOMPLETE] Connected, but the Prospect Tracker was not written.")
            return False
        print("\n[COMPLETE] Google Sheets live sync finished cleanly.")
        return True

    except Exception as e:
        import traceback
        print(f"\n[ERROR] Google Sheets API connection failed: {e}")
        traceback.print_exc()
        _write_sync_result(tenant, {
            "ok": False,
            "appended": 0,
            "updated": 0,
            "error": str(e),
            "finished_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        })
        return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--tenant", default="asheville", help="Tenant ID")
    args = parser.parse_args()

    # Exit non-zero on failure. Discarding this result made run_agency.py report
    # [PASS] for syncs that never touched the sheet.
    raise SystemExit(0 if sync_to_google_sheet(args.tenant) else 1)
