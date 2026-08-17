# Project Requirements

## Goal
Build and operate an approval-gated, multi-agent AI business environment for Tom Gronek that operates autonomously for safe internal activities while strictly enforcing human approval gates (G0–G5) for all external and commercial actions.

## Acceptance Criteria
1. **Single-Writer Architecture:** Only `Atlas-Orchestrator` may write to the live Google Sheet command center. Specialist agents return structured change packets.
2. **Strict Approval Gates (G0–G5):** No outreach (G2), payment requests/pricing changes (G3), account/publishing access (G4), or strategic pivots (G5) are executed without explicit, unexpired written approval from Tom Gronek.
3. **Living Document Command Center:** Syncs state continuously across Google Sheet tabs (`Start Here`, `Prospect Tracker`, `48-Hour Plan`, `Offer & Checklists`, `Activity Log`, `Approval Queue`, `Client Delivery`, `System Setup`).
4. **Safety & Truthfulness:** Zero fabricated clients, reviews, metrics, or invented business problems. Strict do-not-contact and duplicate prospect enforcement.
5. **Idempotency & Failure Recovery:** All operations preserve evidence, record activity logs, support dry-run mode, and recover safely without deleting history.

## Functional Requirements
- **Orchestration Loop:** Execute Stages 1–9 (Start, Plan, Research & Draft, Validate & Record, Wait for Approval, Execute Approved Action, Fulfill & Test, Close Out, Improve).
- **Specialist Agent Roster:** Support `Atlas-Orchestrator`, `Scout-Research`, `Offer-Strategist`, `Proof-Builder`, `Outreach-Drafter`, `Sales-Coordinator`, `Delivery-Builder`, `QA-Risk`, and `Finance-Recorder`.
- **Change Packet Validation:** Validate agent outputs against strict schema, evidence requirements, and approval checks prior to writing.
- **Audit Logging:** Maintain an append-only `Activity Log` recording run IDs, actions, evidence, and outcomes.

## Non-Functional Requirements
- Concise, reliable markdown/JSON instructions compatible with Antigravity multi-agent system.
- Zero secret credentials stored in spreadsheets or git repository.
- Support dry-run mode for testing and automated workflow validation.

## Constraints and Non-Goals
- **Budget:** $0–$100 initial budget limit.
- **Timezone:** `America/New_York` (Asheville & Buncombe County, NC focus).
- **Non-Goals:** No speculative branding, unnecessary custom software development, or endless planning without customer contact. No revenue/ranking guarantees to prospects.

## Open Questions
1. Confirmation of active offer selected in tab `Start Here` of the live Google Sheet.
2. Google Cloud / Sheets API credentials setup method for live Sheet sync vs CLI interface.

