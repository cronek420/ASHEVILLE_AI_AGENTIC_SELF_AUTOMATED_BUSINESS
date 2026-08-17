# Asheville AI Agentic Self-Automated Business

An approval-gated, agent-operated service business environment for Asheville and Buncombe County, NC.

## Quick Start for Any AI Agent

> [!IMPORTANT]
> **Start here:** Read [GEMINI.md](file:///c:/Users/crone/Projects/ASHEVILLE_AI_AGENTIC_SELF_AUTOMATED_BUSINESS/ASHEVILLE_AI_AGENTIC_SELF_AUTOMATED_BUSINESS/GEMINI.md) — it contains the mandatory reading order for all project context, rules, and state.
> All platform loaders (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`) point to this single source of truth.
> All pending owner decisions, approvals, costs, and manual checks are consolidated in `NEED_HUMAN_APPROVAL`.

---

## Project Layout

```
├── .agents/                    ← ALL agent config, rules, memory, and workflows live here
│   ├── agent.md                ← Agent roles & delegation rules
│   ├── rules/                  ← 7 governance rule files (00–06)
│   │   ├── 00-project-governance.md
│   │   ├── 01-single-writer-contract.md
│   │   └── ...
│   ├── workflows/              ← 12 operational workflow files (run operating loop, etc.)
│   ├── memory/                 ← Persistent memory ledgers (lessons-learned, baseline)
│   ├── skills/                 ← 4 reusable skills (debugging, privacy, design, QA)
│   └── skills_index.json       ← Skill registry
│
├── GEMINI.md                   ← START HERE — reading order for any AI
├── AGENTS.md / CLAUDE.md       ← Platform loaders → point to GEMINI.md
├── PROJECT_CONTEXT.md          ← Who, what, where, active offer
├── PROJECT_REQUIREMENTS.md     ← Acceptance criteria & functional requirements
├── SESSION_HANDOFF.md          ← Current stage, target metrics, next actions
├── DECISIONS.md                ← Approved decisions log
├── BUILD_PLAN.md               ← Phase-based implementation tracker
├── BUILD_STATUS.md             ← Dry-run operational test verification log
│
├── run_agency.py               ← Main pipeline (orchestrates steps 1-8 below)
├── lead_scraper.py             ← Step 1: Find prospects (with fallback targets)
├── batch_audit_scanner.py      ← Step 2: Audit websites (responsiveness, latency, SEO)
├── build_audit_previews.py      ← Step 3: Generate visual HTML previews
├── proposal_engine.py          ← Step 4: Pre-generate custom proposals
├── email_dispatcher.py         ← Step 5: Send outreach emails (G2 approved list only)
├── live_sheets_sync.py         ← Step 6: Single-writer Google Sheets sync (headless friendly)
├── inbox_monitor.py            ← Step 7: Gmail reply inbox check (single pass / loop modes)
├── daily_reporter.py           ← Step 8: Send daily owner control report with links and next actions
│
├── command_center_adapter.py   ← Single-writer validation engine (internal rules & dry run tests)
├── .env                        ← Credentials (never commit; set DRY_RUN=false for production)
├── token.json                  ← Google Sheets OAuth token (refreshed, never commit)
├── gmail_token.json            ← Gmail OAuth token (refreshed, never commit)
├── requirements.txt            ← Python dependencies
│
└── OLD_FILES_TO_DELETE/        ← Quarantined obsolete, duplicate, and test files
```

---

## 🛡️ Core Rules for AI Agents

All agents operating in this repository must strictly adhere to the following architectural rules:

### 1. The Single-Writer Spreadsheet Contract
- **ONLY `live_sheets_sync.py`** (managed by `Atlas-Orchestrator`) may write to the live Google Sheet Command Center.
- **Specialist agents** (`Scout-Research`, `Outreach-Drafter`, etc.) are **STRICTLY PROHIBITED** from modifying the Google Sheet workbook directly.
- **Change Packets:** Specialist agents must return structured change packets matching the schema in [.agents/rules/01-single-writer-contract.md](file:///c:/Users/crone/Projects/ASHEVILLE_AI_AGENTIC_SELF_AUTOMATED_BUSINESS/ASHEVILLE_AI_AGENTIC_SELF_AUTOMATED_BUSINESS/.agents/rules/01-single-writer-contract.md).

### 2. Strict Approval Gates (G0–G5)
- No external commercial actions (sending emails, asking for money, publishing) may occur without explicit, unexpired written approval from Tom Gronek.
- **G2 Gate (Outreach):** Only send outreach to domains explicitly approved for email.
- **G3 Gate (Proposals & Links):** Only send proposal documents or payment links explicitly approved in the `Approval Queue`.
- Reference [.agents/rules/02-approval-gates.md](file:///c:/Users/crone/Projects/ASHEVILLE_AI_AGENTIC_SELF_AUTOMATED_BUSINESS/ASHEVILLE_AI_AGENTIC_SELF_AUTOMATED_BUSINESS/.agents/rules/02-approval-gates.md).

### 3. Safety & Data Privacy
- **Zero Fabrication:** Never invent clients, mock replies, reviews, or metrics. Only report empirical data.
- **Do-Not-Contact:** Automatically cross-reference and reject duplicate leads or contacts in the opt-out / DNC registry.
- **Secret Redaction:** Never commit passwords, App Passwords, API keys, or raw OAuth secrets. Keep them in `.env`.

---

## 🚀 Running the Pipeline

To execute the safe, internal-only pipeline (external email and live Sheet writes are skipped):

```bash
pip install -r requirements.txt
python run_agency.py
```

Live Sheet synchronization is an explicit opt-in: `python run_agency.py --sync-sheet`.
Outreach is never sent by the general pipeline. Run `email_dispatcher.py` separately;
live sending requires `--execute` plus exact, unexpired G2 and G3 records in the local
approval manifest. The dispatcher also checks the DNC file and persistent sent ledger.

Output is written to both standard output and [agency_cron.log](file:///c:/Users/crone/Projects/ASHEVILLE_AI_AGENTIC_SELF_AUTOMATED_BUSINESS/ASHEVILLE_AI_AGENTIC_SELF_AUTOMATED_BUSINESS/agency_cron.log).

## Approval-Gated Public Onboarding

The optional Cloud Run service in `public_intake_api.py` accepts only validated
requests from one configured website origin. Requests are stored privately in
Firestore as `NEEDS_OWNER_REVIEW` / `DRY_RUN`; they never write directly to the
Google Sheet or trigger email, payment, publishing, customer access, or agents.

`process_intake_queue.py` creates Atlas-Orchestrator change packets. Only an
explicit `python run_agency.py --sync-sheet` run may stage deduplicated packets
in `Approval Queue`, through `live_sheets_sync.py` as the sole Sheet writer.

Local configuration names are documented in `.env.example`. Production secrets
belong in Google Secret Manager. Deployment and website connection require the
separate public-connection approval gate and are not performed by local setup.

## Daily Owner Email

`daily_reporter.py` now sends a plain-English owner briefing instead of a short stat dump.
It includes:

- the latest pipeline counts
- whether action is needed today
- the public intake status and live link once `WORKFORCE_INTAKE_PUBLIC_URL` is set
- the Command Center, Drive, and website links
- a short explanation of how day-to-day intake and approvals work

If the public intake is not deployed yet, the email says so clearly and points back to the Gate B approval path.
