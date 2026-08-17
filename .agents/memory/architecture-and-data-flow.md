# Architecture and Data Flow Reference
**Project:** Asheville AI Agentic Self-Automated Business

This document serves as a quick-reference guide for how the system's architecture, data flow, and components are structured.

## 1. Core Principles
1. **Single-Writer Architecture:** 
   - Multiple local scripts perform specialized tasks (auditing, HTML building, drafting emails, reading emails).
   - Only ONE script (`live_sheets_sync.py`) pushes the local state up to the live Google Sheet Command Center. This prevents race conditions and corrupted sheet data.
2. **Approval Gates (G0-G5):**
   - No external commercial actions (sending emails, asking for money, accessing client servers) occur without explicit human approval from Tom Gronek.
3. **Local First, Cloud Synced:**
   - The true working state lives in local files (e.g., `audit_results.json`, `proposals/` folder, `audit_previews/` folder).
   - The Google Sheet is a *reflection* of this local state, acting as a dashboard for Tom.

## 2. The Operational Flow

### Phase 1: Target Generation & Auditing
1. **`batch_audit_scanner.py`**: Given a list of local Asheville domain names, it attempts to load them, audits their speed, SEO (meta tags, H1, alt text), and mobile responsiveness.
2. **Output**: Writes results to `audit_results.json`.

### Phase 2: Proof & Asset Generation
1. **`build_audit_previews.py`**: Reads `audit_results.json` and generates responsive HTML visual reports for each prospect.
2. **Output**: Writes HTML files to `audit_previews/` directory.

### Phase 3: Outreach (G2 Approval Required)
1. **`smtp_outreach_dispatcher.py` / `smtp_outreach_batch2.py`**: Uses Gmail SMTP (`lexiconatlas@gmail.com`) to send personalized cold emails referencing the audits.
2. **Execution**: Paces emails (15-20s delay) to avoid spam filters.

### Phase 4: Inbound Monitoring & Proposals (G3 Approval Required)
1. **`proposal_engine.py`**: Reads `audit_results.json` and pre-generates $50 deposit proposals for all active targets.
2. **Output**: Writes text proposals to `proposals/{domain}_proposal.txt`.
3. **`inbox_monitor.py`**: Polls the `lexiconatlas@gmail.com` inbox using the Gmail API looking for replies.
4. **Action**: When a reply is detected, Tom approves the pre-generated proposal text (G3), and it is sent back to the prospect.

### Phase 5: Dashboard Synchronization
1. **`live_sheets_sync.py`**: The Orchestrator's single-writer script. It reads `audit_results.json` and the `proposals/` directory to deduce current statuses, then pushes the unified data to the "Prospect Tracker" and "Activity Log" tabs in Google Sheets.

## 3. Persistent Memory
- **`SESSION_HANDOFF.md`**: The current execution context, blocked items, and next actions.
- **`.agents/memory/lessons-learned.md`**: Operational pitfalls, API constraints (like GCP org policies blocking service account keys), and their solutions.
- **`.agents/rules/`**: Governance rules that enforce the G0-G5 gates.
