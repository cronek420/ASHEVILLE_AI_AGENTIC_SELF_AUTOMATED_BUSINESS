# Workflow: Run Operating Loop

Follow this workflow to execute an autonomous, approval-gated operating session.

```yaml
description: Execute the 9-stage operating cycle for the active business offer
roles:
  orchestrator: Atlas-Orchestrator
  specialists: Scout-Research, Offer-Strategist, Proof-Builder, Outreach-Drafter, Sales-Coordinator, Delivery-Builder, QA-Risk, Finance-Recorder
```

## Step 1: Start Session (Stage 1)
1. Generate unique `run_id`: `RUN-YYYYMMDD-HHMM-XX`.
2. Read Google Sheet tabs: `Start Here`, `Agent Guide`, `System Setup`, `Approval Queue`, `48-Hour Plan`, `Prospect Tracker`, `Client Delivery`.
3. Validate active offer count. Stop if active offers != 1.
4. Check setup readiness in `System Setup`.
5. Identify pending approvals in `Approval Queue`.
6. **Self-Annealing Startup:** Load active adopted lessons from `.agents/memory/lessons-learned.md`, check error patterns in `.agents/memory/error-patterns.jsonl`, and apply preventive controls from `.agents/memory/successful-patterns.md`.
7. Output Startup Summary & Next 3 Recommended Actions.

## Step 2: Plan Tasks (Stage 2)
1. Break current objective into dependency-ordered task items.
2. Assign owners and evidence criteria for each task.
3. Mark any blocked tasks.

## Step 3: Research & Draft (Stage 3)
1. Instruct `Scout-Research` to find qualified prospects and verify visible need.
2. Execute duplicate and do-not-contact checks.
3. Instruct `Proof-Builder` to generate sample audits/previews from public data.
4. Instruct `Outreach-Drafter` to prepare personalized outreach messages.
5. Collect structured Change Packets from specialists (including any error reporting or lesson proposals).

## Step 4: Validate & Record (Stage 4)
1. Validate Change Packets according to `.agents/rules/01-single-writer-contract.md`.
2. Apply authorized field updates to live Google Sheet.
3. Read changed cells back to confirm update.
4. Append `Activity Log` entry.
5. Create G2/G3/G4/G5 approval requests in `Approval Queue`.

## Step 5: Wait for Approval (Stage 5)
1. Stop all gated external actions.
2. Present approval request payload clearly to Tom Gronek.
3. Wait for explicit `Approved` status before proceeding to Step 6.

## Step 6: Execute Approved Action (Stage 6)
1. Re-verify approval validity and unexpired timestamp.
2. Perform exact approved action.
3. Capture response evidence and log to `Activity Log`.

## Step 7: Fulfill & QA (Stage 7)
1. Verify paid deposit/balance (G3).
2. Execute deliverable within isolated workspace (`Delivery-Builder`).
3. Run QA audit (`QA-Risk`).
4. Present G4 approval request before client delivery or system publish.

## Step 8: Close Out & Self-Annealing Report (Stage 8)
1. Calculate full session metrics (prospects, outreach, replies, proposals, cash collected, work delivered, blockers).
2. Execute 13-Point Required Learning Review (.agents/workflows/self-anneal.md).
3. Render YAML Closeout Report and append any new lesson entries to `.agents/memory/lessons-learned.md` and `.agents/memory/error-patterns.jsonl`.

## Step 9: Recommend Improvement (Stage 9)
1. Identify 1 evidence-based test variable to improve performance.
2. Request G5 approval if modifying offer parameters (Level 3 change).
