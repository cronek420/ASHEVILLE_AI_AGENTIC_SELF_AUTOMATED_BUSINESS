# Command Center Sheet Write Contract

Applies to any code or agent that writes to a tenant Command Center workbook.
Complements `01-single-writer-contract.md` (who may write) by defining **how** to
write without corrupting the workbook or erasing the owner's work.

## 1. Workbook discovery

- Never hardcode a spreadsheet id. Read `tenants.yaml`; each tenant has its own
  `spreadsheet_id` and `gids`.
- Tab deep links come from `gids`. A gid belongs to one spreadsheet only — if
  `spreadsheet_id` changes, re-read the gids from the new workbook.

## 2. Never assume row 1

Every LIVE tab is laid out as:

| Row | Content |
| --- | --- |
| 1 | Tab title |
| 2 | Description of the tab |
| 3 | Blank |
| 4 | **Header row** |
| 5+ | Data |

Locate the header **by its column names**, not by position — `live_sheets_sync._find_headers`
does this. Writing to `A1` because "that's where headers go" silently misaligns
every column.

## 3. Match rows by key, never by position

- `Prospect Tracker` is keyed on **Website**, compared as a bare domain:
  scheme, `www.` and trailing slash stripped (`_normalize_site`).
- `Approval Queue` is keyed on **Request ID** / **Approval ID**.
- Appending without checking the key creates duplicates that quietly split a
  prospect's history across two rows.

## 4. Column ownership — the rule that matters most

`Prospect Tracker` columns are split between the pipeline and the owner:

- **Agent-owned** (`PROSPECT_AGENT_HEADERS`): Business, Category, Website,
  Visible Issue, Source, Contact Channel, Public Contact, Personalized Idea,
  Audit Score, Grade, Issues Found, Top Opportunity, Phone, Email.
- **Owner-owned** (`PROSPECT_OWNER_HEADERS`): Priority, Date Contacted, Status,
  Follow-Up Date, Quoted Price, Deposit Requested.

Owner-owned columns are seeded once when a row is created and **never written
again**. A nightly resync that rewrites them destroys hand-entered follow-up
dates, quoted prices and deposits — data that exists nowhere else.

The same split applies to `Approval Queue`: agents write the request columns,
the owner writes `Status`, `Decision By`, `Decision At`, `Conditions / Notes`.
**An agent must never write an approval decision.**

## 5. Typed columns have a fixed vocabulary

These tabs are Google Sheets **Tables**. Several columns are typed `DROPDOWN`
and reject any value outside their list — such a value cannot be filtered,
coloured, or selected by the owner.

| Column | Allowed values |
| --- | --- |
| `Gate` | `G0 Setup`, `G1 Launch`, `G2 Outreach`, `G3 Payment`, `G4 Access & Publish`, `G5 Pivot & Scale` |
| `Status` (Approval Queue) | `Pending`, `Approved`, `Approved with Conditions`, `Rejected`, `Expired`, `Cancelled` |

Use `live_sheets_sync.gate_label()` and `approval_status_label()` rather than
writing shorthand. Internal states such as `NEEDS_OWNER_REVIEW` are **not**
workbook statuses: map them to `Pending` and record the raw state in
`Conditions / Notes`. Unknown states must map to `Pending`, never to an
approved value — fail toward "still needs a human".

Do not call `setDataValidation` on a typed column; the API rejects it and the
template already supplies the dropdown.

## 6. Reading an approval

An approval authorizes an action only when **all** hold:

1. `Status` starts with `Approved`.
2. The row has not expired (`Expires At`).
3. Recipient, message text, price, scope and destination match the row exactly.
4. Every condition in `Conditions / Notes` is satisfied.

Silence, a blank status, or a row edited after approval is never authorization.

### Outreach approvals are wired to the dispatcher

`sheet_approvals.py` turns approved rows into records the dispatcher accepts, so
a decision made in the workbook — including from a phone — actually gates a send.
Three extra columns carry the binding:

| Column | Purpose |
| --- | --- |
| `Recipient` | the exact address the approval covers |
| `Domain` | the business the approval covers |
| `Message SHA256` | hash of the exact subject + body approved |

Consequences that must not be softened:

- **Two rows per prospect.** `G2 Outreach` and `G3 Payment` are approved
  separately; one alone sends nothing.
- **Editing the proposal voids the approval.** The hash changes, so the approved
  row no longer matches and the send is blocked.
- **A row missing Recipient, Domain, Message SHA256 or Expires At is ignored.**
  A blank cell must never widen into general permission.
- **Staging is not approving.** `stage_outreach_approvals()` writes rows as
  `Pending`; it can never mark its own row approved.
- **An unreadable sheet authorizes nothing.** Errors return an empty approval
  list rather than falling back to "allow".

Sending still additionally requires `--execute`, a DNC miss, the daily send
limit, and an unused message hash in the sent ledger.

## 7. After every successful write

Append one row to `Activity Log`. Never overwrite log history. Report conflicts
and lock errors instead of retrying blindly.

## 8. Tabs that are off limits

- `✅ Owner Review` is computed entirely from formulas. **No agent writes to it.**
- Reference tabs (`Opportunities`, `Buyer Search`, `Outreach Scripts`, `Sources`,
  `Idea Library`, `Offer Details`, `Competitor Research`, `Agent Guide`) are
  read-only without explicit approval.

## 9. Before changing sync code

Run `python -m unittest discover -s tests -q`. `tests/test_prospect_tracker_sync.py`
covers header discovery, owner-column preservation, domain normalization, and the
dropdown vocabulary. If a change makes those tests fail, the change is wrong —
they encode data-loss bugs that have already happened once.
