"""
Bridge between the owner's Approval Queue tab and the outreach dispatcher.

Without this, approving a row in the workbook records a decision but authorizes
nothing: email_dispatcher.py only reads approvals.local.json. This module lets a
phone approval actually gate a send, while keeping every existing safety rule.

Two halves:

  stage_outreach_approvals()  writes one Pending row per gate for a specific
                              message, including the sha256 of the exact text.
  load_sheet_approvals()      reads decided rows back as approval records in the
                              shape _valid_approval() expects.

Fail-closed by construction:
  * a row authorizes only the exact message it was staged with — editing the
    proposal changes the hash and voids the approval;
  * a row without an Expires At is ignored, so a blank cell never authorizes;
  * both G2 (outreach) and G3 (payment) must be approved separately;
  * anything not explicitly Approved is treated as not approved.
"""

import datetime as dt

from live_sheets_sync import (
    APPROVAL_BASE_HEADERS,
    GATE_LABELS,
    _column_label,
    _find_headers,
    _ensure_headers,
    _last_used_row,
)

# Columns this bridge needs that the base template does not define.
OUTREACH_HEADERS = ["Recipient", "Domain", "Message SHA256"]
REQUIRED_GATES = ["G2", "G3"]
APPROVED_STATUSES = {"approved", "approved with conditions"}
DEFAULT_VALID_DAYS = 14

# "G2 Outreach" -> "G2"
LABEL_TO_GATE = {label: gate for gate, label in GATE_LABELS.items()}


def _gate_code(value):
    text = str(value or "").strip()
    if text in LABEL_TO_GATE:
        return LABEL_TO_GATE[text]
    code = text.split()[0].upper() if text else ""
    return code if code in GATE_LABELS else ""


def _header_index(worksheet):
    rows = worksheet.get_all_values()
    index = _find_headers(rows, {"Approval ID", "Status"})
    if index is None:
        raise ValueError("Approval Queue is missing a recognized header row.")
    headers = _ensure_headers(worksheet, rows, index, list(APPROVAL_BASE_HEADERS) + OUTREACH_HEADERS)
    return rows, index, headers


def load_sheet_approvals(worksheet, now=None, tenant=""):
    """Return approval records for rows the owner has explicitly approved."""
    now = now or dt.datetime.now(dt.timezone.utc)
    rows, index, headers = _header_index(worksheet)

    approvals = []
    for row in rows[index + 1:]:
        record = dict(zip(headers, list(row) + [""] * (len(headers) - len(row))))
        
        # If we are loading from a master sheet, filter by tenant if specified
        if tenant and "City" in headers:
            row_city = str(record.get("City", "")).strip().lower()
            if row_city and row_city != tenant.lower():
                continue

        if str(record.get("Status", "")).strip().lower() not in APPROVED_STATUSES:
            continue
        gate = _gate_code(record.get("Gate"))
        if gate not in REQUIRED_GATES:
            continue
        digest = str(record.get("Message SHA256", "")).strip()
        recipient = str(record.get("Recipient", "")).strip()
        domain = str(record.get("Domain", "")).strip()
        expires = str(record.get("Expires At", "")).strip()
        # A row missing any of these cannot be matched to a specific message and
        # must never widen into a general permission.
        if not (digest and recipient and domain and expires):
            continue
        approvals.append({
            "status": "Approved" if record["Status"].strip().lower() == "approved"
                      else "Approved with Conditions",
            "gate_type": gate,
            "recipient": recipient,
            "domain": domain,
            "message_sha256": digest,
            "expires_at": expires,
            "source": "sheet",
            "approval_id": str(record.get("Approval ID", "")).strip(),
        })
    return approvals


def stage_outreach_approvals(worksheet, items, run_id="", valid_days=DEFAULT_VALID_DAYS, now=None, tenant=""):
    """
    Write Pending approval rows for messages awaiting a decision.

    `items` are dicts with domain, recipient, business, subject, message_sha256
    and optional risk/evidence text. One row per required gate. Existing rows for
    the same (gate, domain, hash) are left alone so a decision is never reset.
    """
    now = now or dt.datetime.now(dt.timezone.utc)
    rows, index, headers = _header_index(worksheet)

    seen = set()
    for row in rows[index + 1:]:
        record = dict(zip(headers, list(row) + [""] * (len(headers) - len(row))))
        # Support Master sheet tracking by taking city into account if present
        row_city = str(record.get("City", "")).strip().lower()
        if "City" in headers and row_city and tenant and row_city != tenant.lower():
            continue
            
        seen.add((
            _gate_code(record.get("Gate")),
            str(record.get("Domain", "")).strip().lower(),
            str(record.get("Message SHA256", "")).strip(),
        ))

    expires = (now + dt.timedelta(days=valid_days)).isoformat()
    new_rows = []
    for item in items:
        domain = str(item.get("domain", "")).strip()
        digest = str(item.get("message_sha256", "")).strip()
        recipient = str(item.get("recipient", "")).strip()
        if not (domain and digest and recipient):
            continue
        for gate in REQUIRED_GATES:
            if (gate, domain.lower(), digest) in seen:
                continue
            seen.add((gate, domain.lower(), digest))
            fields = {
                "City": tenant.title() if tenant else "",
                "Approval ID": f"{gate}-{domain}-{digest[:8]}",
                "Requested At": now.isoformat(),
                "Run ID": run_id,
                "Requesting Agent": "Atlas-Orchestrator",
                "Gate": GATE_LABELS[gate],
                "Business": item.get("business", domain),
                "Proposed Action": (
                    f"Send outreach email to {recipient}" if gate == "G2"
                    else f"Include payment link / commercial terms for {item.get('business', domain)}"
                ),
                "Evidence / Reason": item.get("evidence", f"Audited {domain}; proposal drafted."),
                "Risk / Cost": item.get("risk", "External send to a real business. No cost."),
                "Status": "Pending",
                "Conditions / Notes": f"Subject: {item.get('subject', '')}",
                "Expires At": expires,
                "Recipient": recipient,
                "Domain": domain,
                "Message SHA256": digest,
            }
            new_rows.append([str(fields.get(header, "")) for header in headers])

    if new_rows:
        start = max(_last_used_row(rows), index + 1) + 1
        end = start + len(new_rows) - 1
        row_count = getattr(worksheet, "row_count", None)
        if row_count is not None and row_count < end:
            worksheet.add_rows(end - row_count)
        worksheet.update(
            values=new_rows,
            range_name=f"A{start}:{_column_label(len(headers) - 1)}{end}",
        )
    return len(new_rows)
