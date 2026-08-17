# Agent Audit — 2026-08-09

Requested by Tom: roles, responsibilities, organization, communication, guards, and
whether there should be more or fewer agents.

The short answer: **fewer, and honest about which ones are real.** The system does
not need more agents. It needs the written roster to match the things that actually
run.

## Finding 1 — There are two rosters, and they disagree

`PROJECT_REQUIREMENTS.md` specifies nine specialists:

> `Atlas-Orchestrator`, `Scout-Research`, `Offer-Strategist`, `Proof-Builder`,
> `Outreach-Drafter`, `Sales-Coordinator`, `Delivery-Builder`, `QA-Risk`,
> `Finance-Recorder`

`.agents/agents.md` specifies six generic roles:

> Orchestrator, Research, Architect, Builder, Reviewer, Documentation

These are different taxonomies describing the same work. Neither maps to the other.
A reader following the required reading order meets the six-role table last and has
no way to reconcile it with the nine names used everywhere else.

## Finding 2 — None of those agents exist as running processes

`VERIFIED` The agent types actually available in this environment are: `claude`,
`claude-code-guide`, `Explore`, `general-purpose`, `Plan`, `statusline-setup`.

There is no `Atlas-Orchestrator` process. There is no `QA-Risk`. When the rules say
"`Atlas-Orchestrator` validates specialist Change Packets", what physically happens
is that one assistant session does that step itself, sequentially.

`.agents/agents.md` is honest about this in its own first line — "verify actual agent
availability before delegation" — but the rest of the documentation reads as though
a standing multi-agent staff exists. It does not. Treating an aspirational roster as
an operational one is how work silently goes undone: every role is assumed to be
someone else's.

## Finding 3 — The real swarm already exists, and it works

The genuine agents are the pipeline programs. They have clean single
responsibilities, run in dependency order, and are individually testable:

| Program | Responsibility | Writes |
| --- | --- | --- |
| `process_intake_queue.py` | Stage website intake for owner review | Firestore, Approval Queue |
| `lead_scraper.py` | Find candidate businesses per city | `scraped_leads_<tenant>.json` |
| `batch_audit_scanner.py` | Audit sites, extract contacts, grade | `audit_results_<tenant>.json` |
| `proposal_engine.py` | Draft a proposal per audited site | `proposals_<tenant>/` |
| `live_sheets_sync.py` | Publish state to the Command Center | Google Sheets |
| `inbox_monitor.py` | Watch for prospect replies | read-only |
| `daily_reporter.py` | Tell Tom what happened | email to owner |
| `email_dispatcher.py` | Send only exactly-approved outreach | SMTP, outreach ledger |
| `sheet_approvals.py` | Bridge phone approvals to the dispatcher | Approval Queue |

This roster is real, it is scheduled, and as of 2026-08-09 it demonstrably works.
It should be *the* roster in the documentation.

## Finding 4 — The skill library is 246 skills and 55.8 MB of mostly noise

`VERIFIED` `.agents/skills/` holds 246 skill directories plus a 22.9 MB
`skills_fixed.zip`. The catalogue includes `active-directory-attacks`,
`3d-web-experience`, and hundreds of others with no relationship to running a local
web-services agency.

This is not free. A large undifferentiated catalogue makes it harder to find the few
skills that matter, and the zip bloats every clone and container build context.

## Finding 5 — Guards that exist and work

Genuinely good, and worth protecting:

- Approval gates G0–G5, with silence explicitly not counting as approval.
- Single-writer contract: one writer to the Command Center.
- Fail-closed dispatch: exact recipient, domain, message hash, and unexpired approval
  on both G2 and G3, or nothing sends.
- Editing a proposal changes its hash and voids the approval.
- Dry-run is the default; `--execute` is always explicit.
- Durable outreach ledger with fail-closed reads (added 2026-08-09).
- Do-not-contact enforcement ahead of every send.

## Finding 6 — Guards that are missing

1. **No proof of work.** Until 2026-08-09 a step could do nothing and report `[PASS]`.
   Exit codes are fixed, but the pipeline still cannot distinguish "synced 126 rows"
   from "synced 0 rows" in its summary.
2. **A hardcoded audit line.** `live_sheets_sync.py` writes the Activity Log row
   "Synced 5 G2 approved prospects & dispatches" no matter what happened. An audit
   trail that states a fixed number is worse than none, because it looks like
   evidence.
3. **No environment smoke test.** 87 local tests passed for days while every cloud
   run silently did nothing, because local disks are writable and Secret Manager
   mounts are not. Nothing tests the environment the business actually runs in.
4. **No deliverability check.** Two of the first prospects had dead mail servers.
   Approvals are being spent on addresses that cannot receive mail.

## Recommendation

Do not add agents. Do this instead:

1. Replace both rosters with the real one from Finding 3, and state plainly that
   role names are hats worn by one session, not concurrent staff.
2. Trim the skill library to what this business uses; archive the rest outside the
   repo and delete the zip.
3. Close the four guard gaps in Finding 6, cheapest first: measured counts in the
   daily report, then the honest Activity Log row, then a cloud smoke test.
4. Adopt `MISSION.md` as the tie-breaker when a rule and a goal conflict.
