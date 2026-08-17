# Rule 06: Self-Annealing Governance & Change Levels

This rule governs how the system self-anneals and adopts continuous improvements without altering protected controls or exceeding agent authority.

---

## 1. Protected Controls (Inviolable Rules)

The following controls MUST NEVER be altered, weakened, or bypassed for speed, efficiency, or convenience:

1. **Tom Gronek's Final Authority:** Human approval governs all external actions.
2. **Approval Gates (G0–G5):** No outreach (G2), payment requests/pricing (G3), account access/publishing (G4), or strategic pivots (G5) without explicit approval.
3. **Single-Writer Spreadsheet Rule:** Only `Atlas-Orchestrator` writes to the live Google Sheet command center.
4. **Truthfulness & Evidence:** No fabricated clients, reviews, metrics, or invented business problems.
5. **Do-Not-Contact Protections:** Strict checking of DNC lists and duplicate prospects.
6. **Privacy & Credentials:** Zero secrets, API keys, passwords, or customer PII stored in code, logs, or memory ledgers.
7. **Payment Verification:** No payment links or invoice recording without verified evidence.
8. **Backup & Rollback Requirements:** All changes must be reversible.

---

## 2. Change Levels & Approval Authority

Self-annealing changes are classified into 4 levels:

### Level 0 — Record and Monitor (No Approval Required)
- **Scope:** Isolated events or incomplete evidence.
- **Action:** Record in `.agents/memory/lessons-learned.md` and `.agents/memory/error-patterns.jsonl` with status `monitoring`. No code or workflow modifications.

### Level 1 — Safe Internal Improvement (Orchestrator Approval)
- **Scope:** Internal task ordering, duplicate detection rules, validation checklists, retry timing, internal summaries, read caching, formatting.
- **Action:** `Atlas-Orchestrator` adopts after successful dry-run testing. Must NOT impact external behavior, permissions, prices, security, or approval gates.

### Level 2 — Controlled Workflow Change (Tom's Approval Required)
- **Scope:** Agent responsibilities, living document structure, core workflows, prospect qualification criteria, required evidence schemas, tool permissions, business rules.
- **Action:** Formally draft proposal in `Approval Queue` and wait for Tom's written approval before adoption.

### Level 3 — Business or Autonomy Change (G5 Pivot Approval Required)
- **Scope:** Active offer details, pricing, deposits, guarantees, target market, outreach volume, budget/spending, external-action authority, publication authority, self-modification limits.
- **Action:** Strictly blocked until G5 approval is granted by Tom.

---

## 3. Repeated-Error Escalation Rules

- **1st Occurrence:** Record in `.agents/memory/error-patterns.jsonl`, diagnose root cause, add preventive checklist step in `.agents/memory/successful-patterns.md`.
- **2nd Occurrence:** Identify shared pattern across occurrences, test an improvement in dry-run mode.
- **3rd Occurrence:** **STOP the affected workflow immediately** and request formal review from Tom.
- **Zero-Tolerance Category Errors:** Any `SECURITY_ERROR`, `PERMISSION_ERROR`, payment link error, unauthorized send/deletion, or unauthorized account access requires **IMMEDIATE WORKFLOW HALT**, evidence preservation, and notification to Tom.
