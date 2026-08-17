# Session Handoff

## Current Objective
Wait for and monitor incoming prospect replies on `lexiconatlas@gmail.com` across all 10 live outreach prospects. Present generated G3 proposal packets (now armed with a live Stripe Payment link) for Tom's approval as prospects respond.

## Project State
- **Consolidated Operating Environment:**
  - Merged `.agent/` and `.agents/` directories into a single unified `.agents/` folder.
  - Quarantined 17 obsolete, duplicate, and test scripts in `OLD_FILES_TO_DELETE/` to keep the filesystem optimized for AI agents.
  - Updated all codebase references from `.agent/` to `.agents/`.
- **Pipeline Fixed & Verified:**
  - Resolved `DRY_RUN` and empty data file cascades.
  - Standardized `run_agency.py` to run lead scraping (with fallback targets), batch auditing, proposal drafting, sheet sync, and inbox monitoring.
  - Replaced logging checkmark emojis with ASCII text (`[PASS]`/`[FAIL]`) to prevent Unicode console crashes on Windows.
  - Refreshed expired OAuth credentials (`token.json`).
  - Executed a full pipeline run successfully (`Results: 4 passed, 0 failed`).
- **Blocked:**
  - Gmail API needs to be enabled in Google Console project `857010500760` (logs show `accessNotConfigured`).
  - External outreach dispatches (G2) and Sheets Sync are safely disabled by default inside the runner until `--execute` / `--sync-sheet` flags are passed.

## Active Prospects Summary (10 Live Targets)

| Domain | Business Name | Score | Grade | Status | G3 Proposal Asset |
| --- | --- | --- | --- | --- | --- |
| `wardph.com` | Ward Plumbing, Heating, and Air | 85 | B | Dispatched / Monitoring | [wardph_com_proposal.txt](file:///c:/Users/crone/Projects/ASHEVILLE_AI_AGENTIC_SELF_AUTOMATED_BUSINESS/ASHEVILLE_AI_AGENTIC_SELF_AUTOMATED_BUSINESS/proposals/wardph_com_proposal.txt) |
| `whiteandwilliams.com` | White & Williams Co. | 36 | F | Dispatched / Monitoring | [whiteandwilliams_com_proposal.txt](file:///c:/Users/crone/Projects/ASHEVILLE_AI_AGENTIC_SELF_AUTOMATED_BUSINESS/ASHEVILLE_AI_AGENTIC_SELF_AUTOMATED_BUSINESS/proposals/whiteandwilliams_com_proposal.txt) |
| `ashevilleelectrician.com` | Asheville Electrician | 76 | B | Dispatched / Monitoring | [ashevilleelectrician_com_proposal.txt](file:///c:/Users/crone/Projects/ASHEVILLE_AI_AGENTIC_SELF_AUTOMATED_BUSINESS/ASHEVILLE_AI_AGENTIC_SELF_AUTOMATED_BUSINESS/proposals/ashevilleelectrician_com_proposal.txt) |
| `ashevilletreeservice.com` | Asheville Tree Service | 85 | B | Dispatched / Monitoring | [ashevilletreeservice_com_proposal.txt](file:///c:/Users/crone/Projects/ASHEVILLE_AI_AGENTIC_SELF_AUTOMATED_BUSINESS/ASHEVILLE_AI_AGENTIC_SELF_AUTOMATED_BUSINESS/proposals/ashevilletreeservice_com_proposal.txt) |
| `bakerroofing.com` | Baker Roofing | 87 | B | Dispatched / Monitoring | [bakerroofing_com_proposal.txt](file:///c:/Users/crone/Projects/ASHEVILLE_AI_AGENTIC_SELF_AUTOMATED_BUSINESS/ASHEVILLE_AI_AGENTIC_SELF_AUTOMATED_BUSINESS/proposals/bakerroofing_com_proposal.txt) |
| `ashevillepressurewashing.com` | Asheville Pressure Washing | 41 | D | Dispatched / Monitoring | [ashevillepressurewashing_com_proposal.txt](file:///c:/Users/crone/Projects/ASHEVILLE_AI_AGENTIC_SELF_AUTOMATED_BUSINESS/ASHEVILLE_AI_AGENTIC_SELF_AUTOMATED_BUSINESS/proposals/ashevillepressurewashing_com_proposal.txt) |
| `ashevillelawncare.com` | Asheville Lawn Care | 41 | D | Dispatched / Monitoring | [ashevillelawncare_com_proposal.txt](file:///c:/Users/crone/Projects/ASHEVILLE_AI_AGENTIC_SELF_AUTOMATED_BUSINESS/ASHEVILLE_AI_AGENTIC_SELF_AUTOMATED_BUSINESS/proposals/ashevillelawncare_com_proposal.txt) |
| `ashevillepestcontrol.com` | Asheville Pest Control | 64 | C | Dispatched / Monitoring | [ashevillepestcontrol_com_proposal.txt](file:///c:/Users/crone/Projects/ASHEVILLE_AI_AGENTIC_SELF_AUTOMATED_BUSINESS/ASHEVILLE_AI_AGENTIC_SELF_AUTOMATED_BUSINESS/proposals/ashevillepestcontrol_com_proposal.txt) |
| `ashevillefamilydentistry.com` | Asheville Family Dentistry | 79 | B | Dispatched / Monitoring | [ashevillefamilydentistry_com_proposal.txt](file:///c:/Users/crone/Projects/ASHEVILLE_AI_AGENTIC_SELF_AUTOMATED_BUSINESS/ASHEVILLE_AI_AGENTIC_SELF_AUTOMATED_BUSINESS/proposals/ashevillefamilydentistry_com_proposal.txt) |
| `wncsoftwash.com` | WNC Soft Wash | 85 | B | Dispatched / Monitoring | [wncsoftwash_com_proposal.txt](file:///c:/Users/crone/Projects/ASHEVILLE_AI_AGENTIC_SELF_AUTOMATED_BUSINESS/ASHEVILLE_AI_AGENTIC_SELF_AUTOMATED_BUSINESS/proposals/wncsoftwash_com_proposal.txt) |

## Decisions and Risks
- **Decision:** Tom Gronek approved G2 Outreach for 10 Asheville prospects sent via `lexiconatlas@gmail.com` and initialized G3 Proposal Engine.
- **Risk:** Zero unapproved sending. Incoming replies will trigger G3 Proposal approval packets.

## Exact Next Action
1. Enable the Gmail API in the Developer Console project `857010500760`.
2. Schedule a daily cron job to run the pipeline `python run_agency.py --sync-sheet` on Google Cloud once deployed.

## Public Onboarding Integration (Gate A)

- **Approved:** Local implementation change set for the Universal AI Workforce onboarding bridge.
- **Implemented locally:** Cloud Run-compatible Flask endpoint, Firestore private intake store,
  privacy-preserving rate limits, Atlas change-packet staging, and sole-writer Sheet handoff.
- **Safety state:** Every intake remains `NEEDS_OWNER_REVIEW` and `DRY_RUN`; no external action starts.
- **Not approved / not performed:** Cloud deployment, Firestore creation/configuration, public API URL,
  CORS production activation, or landing-site connection (Gate B).
- **Verified:** 13 unit tests, 22 governance checks, and the safe agency pipeline (5 passed, 0 failed).
- **Gate B prerequisites:** Enable Cloud Run and Firestore APIs, create/configure Firestore, provision
  `INTAKE_HASH_KEY` in Secret Manager, inspect `Approval Queue` headers, then approve deployment URL/origin.
