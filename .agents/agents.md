# Agents

## Read this first

There is no standing multi-agent staff. One assistant session does the work,
wearing different hats in sequence. Names like `Atlas-Orchestrator` and `QA-Risk`
are **roles**, not running processes — nobody is waiting in the background to pick
up a task assigned to them.

This matters. When documentation implies a team, work gets assigned to a role and
quietly never happens, because every role is assumed to be somebody else's job.
If a step needs doing, the session doing the reading does it, or it does not
get done.

`VERIFIED 2026-08-09` The agent types actually available here are `claude`,
`general-purpose`, `Explore`, `Plan`, `claude-code-guide`, and `statusline-setup`.
Verify availability before delegating anything.

## The real roster: the pipeline programs

These are the agents that genuinely run, on a schedule, without supervision. Each
has one responsibility and one owner for its output.

| Program | Responsibility | Writes | Gate |
| --- | --- | --- | --- |
| `smoke_test.py` | Prove this environment can read and write before trusting a run | `Smoke Test` tab | — |
| `process_intake_queue.py` | Stage website intake for owner review | Firestore, Approval Queue | — |
| `lead_scraper.py` | Find candidate businesses for one city | `scraped_leads_<tenant>.json` | — |
| `batch_audit_scanner.py` | Audit sites, extract contacts, grade them | `audit_results_<tenant>.json` | — |
| `proposal_engine.py` | Draft one proposal per audited site | `proposals_<tenant>/` | — |
| `live_sheets_sync.py` | Publish state to the Command Center | Google Sheets | single-writer |
| `inbox_monitor.py` | Watch for prospect replies | read-only | — |
| `daily_reporter.py` | Tell Tom what actually happened | email to owner | — |
| `email_dispatcher.py` | Send only exactly-approved outreach | SMTP, outreach ledger | **G2 + G3** |
| `sheet_approvals.py` | Bridge workbook approvals to the dispatcher | Approval Queue | **G2 + G3** |
| `outreach_ledger.py` | Remember who was contacted and who must not be | Firestore | fail-closed |

Orchestration lives in `run_agency.py`, which runs these in dependency order per
tenant and reports a per-step result. It deliberately does **not** dispatch
outreach; that stays a separate, explicitly gated command.

## Role hats

When the work needs a different kind of thinking, name the hat and wear it. Use a
separate hat only when it changes the outcome.

| Hat | Use when | Output | Boundary |
| --- | --- | --- | --- |
| Orchestrator | Any substantial task | Plan, integration, status | Owns final coordination |
| Research | Gathering evidence | Sources and unknowns | Read-only unless authorized |
| Architect | System design | Decisions, contracts, risks | Does not implement unapproved designs |
| Builder | Approved implementation | Working change and notes | Stays within approved scope |
| Reviewer | Verification or risk review | Test evidence and defects | Does not conceal failures |
| Documentation | Guides and handoff | Accurate durable docs | No unsupported claims |

The nine names in `PROJECT_REQUIREMENTS.md` (`Scout-Research`, `Offer-Strategist`,
`Proof-Builder`, `Outreach-Drafter`, `Sales-Coordinator`, `Delivery-Builder`,
`QA-Risk`, `Finance-Recorder`, `Atlas-Orchestrator`) describe business functions in
the operating loop. They map onto the hats above and onto the programs in the real
roster. They are not additional processes, and none of them should be invoked as
though they were.

## Guards that keep this on track

1. **A step must prove it did work.** Exit codes propagate, and the daily report
   states rows actually written. A run that touches nothing says so, in the
   subject line.
2. **Approval is specific.** An approval binds to one recipient, one domain, and
   one exact message hash, and it expires. Editing the message voids it.
3. **Silence is never approval.** Not from Tom, not from an empty ledger, not from
   an unreachable backend.
4. **The record outlives the container.** Sends and suppressions live in Firestore.
   An unreadable ledger blocks sending rather than reading as "nobody contacted".
5. **Dry run is the default.** Every send path requires an explicit `--execute`.
6. **One writer.** Only the sync writes the Command Center; specialists return
   change packets.
7. **`MISSION.md` breaks ties.** When a rule and a goal conflict, the mission wins.

## When unsure

Inspect before changing. State assumptions. Ask rather than infer approval. Prefer
the smallest reversible change that can be verified.
