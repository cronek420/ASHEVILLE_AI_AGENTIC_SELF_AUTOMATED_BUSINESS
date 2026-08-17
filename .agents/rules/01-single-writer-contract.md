# Single-Writer Architecture & Specialist Change-Packet Contract

> This rule defines **who** may write to the workbook. Before writing, also read
> `07-sheet-write-contract.md`, which defines **how**: header discovery, row keys,
> which columns belong to the owner, and the dropdown vocabularies that typed
> columns enforce.

## 1. Single-Writer Authority
- **ONLY `Atlas-Orchestrator` MAY WRITE TO THE LIVE GOOGLE SHEET OR SHARED STATE.**
- Specialist agents (`Scout-Research`, `Offer-Strategist`, `Proof-Builder`, `Outreach-Drafter`, `Sales-Coordinator`, `Delivery-Builder`, `QA-Risk`, `Finance-Recorder`) are **STRICTLY PROHIBITED** from writing directly to the Google Sheet workbook.
- All specialist agents must return a structured **Change Packet** to `Atlas-Orchestrator` for validation.

## 2. Specialist Change-Packet Schema

Every specialist agent response MUST adhere to the following schema:

```yaml
run_id: RUN-YYYYMMDD-HHMM-XX
agent: agent-name
idea_id: IDEA-XX
task: short task description
status: completed | blocked | needs_approval | error
evidence:
  - source_or_artifact: URL, file, screenshot, or record reference
    observation: exact factual finding
proposed_sheet_changes:
  - tab: exact tab name (e.g., Prospect Tracker, 48-Hour Plan, Approval Queue)
    record_key: stable business, prospect, task, approval, or job identifier
    fields:
      Field Name: proposed value
approval_request: null | G0 | G1 | G2 | G3 | G4 | G5
external_action_taken: false
next_step: one specific action
uncertainties:
  - missing fact, conflict, risk, or unresolved question
```

## 3. Packet Validation Rules for Orchestrator

The `Atlas-Orchestrator` MUST automatically REJECT a change packet if:
1. Evidence is missing or incomplete.
2. A claim or finding cannot be verified from public sources/artifacts.
3. The destination tab or field is ambiguous.
4. The `record_key` is missing, unstable, or non-unique.
5. The specialist agent took an unauthorized external action (`external_action_taken: true`).
6. Required information (such as source URL or opt-out clause) is missing.
7. The proposed change conflicts with an existing active approval or do-not-contact record.
8. It contains credentials, secret keys, passwords, or unnecessary personal data.

## 4. Orchestrator Write Protocol

When writing to the live Google Sheet, `Atlas-Orchestrator` MUST perform these 9 steps sequentially:
1. Validate the specialist agent's evidence.
2. Reject unsupported or invented claims.
3. Re-read the target destination cell/row in the Sheet.
4. Confirm that the active offer and approval state have not changed.
5. Apply the smallest authorized update.
6. Read the changed cells back from the Sheet.
7. Verify that the write succeeded exactly as intended.
8. Append an entry to `Activity Log`.
9. Report any conflicts or lock errors immediately to Tom Gronek instead of guessing.

## 5. Living-Document Read & Write Access

### Authorized Live Operating Tabs (Writable by Orchestrator):
- `Start Here`
- `Prospect Tracker`
- `48-Hour Plan`
- `Offer & Checklists`
- `Activity Log`
- `Approval Queue`
- `Client Delivery`
- `System Setup`

### Reference Tabs (Read-Only Controlled Reference Material):
- `Opportunities`
- `Buyer Search`
- `Outreach Scripts`
- `Sources`
- `Idea Library`
- `Offer Details`
- `Competitor Research`
- `Agent Guide`

*Note: Reference tabs must never be silently rewritten. Any material change must be evidence-backed, recorded in `Activity Log`, and approved by Tom Gronek.*
