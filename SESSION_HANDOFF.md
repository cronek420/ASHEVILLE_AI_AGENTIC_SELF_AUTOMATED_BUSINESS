# Session Handoff

## Current Objective
The daily cloud pipeline works and now reports honestly about itself. Next is
monitoring `lexiconatlas@gmail.com` for prospect replies and presenting G3 proposal
packets for Tom's approval.

## Read these first
- `MISSION.md` — what the business is for; breaks ties when a rule and a goal conflict.
- `.agents/agents.md` — the real roster. Role names are hats worn by one session,
  not concurrent staff.
- `.agents/AGENT_AUDIT.md` — the 2026-08-09 audit and its reasoning.

## What was wrong, and what fixed it (2026-08-09)

### 1. The daily run could not finish
`VERIFIED` The 08:00 UTC run failed on a 600s task timeout. Asheville-only runs took
3m11s, but Charlotte is in the image now and the cloud scrape returns ~188 leads.
Fixed: `--task-timeout=3600 --max-retries=1`. Two-city runs take about 15-20 minutes.

### 2. Every cloud run had been silently doing nothing
`VERIFIED` The real problem. Under Cloud Run the OAuth tokens are read-only Secret
Manager mounts. The code refreshed a token successfully, tried to write it back,
caught the `Errno 30 Read-only file system` error, and treated a *persistence*
failure as an *authentication* failure — discarding valid credentials. No sheet was
written and no mailbox read for at least three days.

It went unnoticed because `live_sheets_sync.py` ignored its own return value, so a
failed sync exited 0 and `run_agency.py` printed `[PASS]`.

Both halves fixed: token caching is best effort, a genuine refresh failure still
fails closed, and entry points propagate exit codes.

### 3. Sheets now authenticates as the job itself
`VERIFIED` Cloud Run authenticates as `agency-pipeline-runtime@` — no token file in
the cloud path at all. The workbooks and Drive folder are shared with it as Editor;
Sheets access comes from document sharing, not project IAM.

One trap, hit twice: `google.auth` honours `GOOGLE_APPLICATION_CREDENTIALS` from the
mounted `.env`, which points at a `client_secret.json` that does not exist in the
container. That broke Sheets first, and then Firestore. It is now cleared in one
shared place, `agency_auth.clear_stale_adc_pointer()`. If a Google client ever fails
with "File client_secret.json was not found", this is why.

### 4. No record existed of who had been emailed
`VERIFIED` Bounce notices proved outreach went out 2026-08-03/04 while
`sent_ledger.local.jsonl`, `dnc.local.json` and `approvals.local.json` were all
absent. `outreach_ledger.py` now keeps sends and suppressions in Firestore, every
read fail-closed, and the recoverable history was reconstructed into it.

Two addresses hard-bounced and are suppressed: `info@ashevillepressurewashing.com`
and `service@ashevillelawncare.com`. Both domains publish no usable MX record.

### 5. The seven audit follow-ups
All approved as a batch (`AUDIT7-20260809-01`) and implemented:

1. The daily report leads with rows actually written, and the subject line reads
   `[CHECK: a step did no work]` when any step wrote nothing.
2. The Activity Log records measured counts instead of the hardcoded
   "Synced 5 G2 approved prospects & dispatches".
3. `smoke_test.py` proves this environment can read and write before the run trusts
   itself. It runs first in the pipeline.
4. The agent roster is reconciled; `.agents/agents.md` is authoritative.
5. The skill library went from 246 directories and 55.8 MB to 56 and 6.92 MB.
   Nothing deleted — see `OLD_FILES_TO_DELETE/skills-archive-2026-08-09/`.
6. `deliverability.py` screens a domain before a send is proposed. A domain with no
   usable MX is skipped rather than queued; a merely unreachable server only earns a
   warning on the approval row.
7. Hardening: dedicated `agency-pipeline-runtime@` service account, image pinned by
   digest, and the four orphaned secret volumes removed (8 -> 4).

## Current state
- `VERIFIED` 102 unit tests pass: `python -m unittest discover -s tests`
  (from the project root; pytest is not installed in C:\Python314).
- `VERIFIED` Cloud Scheduler `agency-daily-pipeline` ENABLED, `0 8 * * *` Etc/UTC.
- `VERIFIED` Cloud outreach dispatch remains OFF; `run_agency.py` skips it.
- `VERIFIED` The smoke test works as intended. On execution `agency-pipeline-j8nbn`
  it failed the ledger check and the run reported "11 passed, 1 failed" rather than
  a false all-green — the anti-false-green guard proving itself on a real fault.
- `VERIFIED` Execution `agency-pipeline-4ddjg` (19m28s): **12 passed, 0 failed**,
  including `smoke_test`. Asheville appended 15 / updated 51; Charlotte appended 37 /
  updated 35. That run used image `sha256:59fee51a`.
- `VERIFIED` The deployed image `sha256:0829b7f4` is confirmed green. Execution
  `agency-pipeline-s54tw` (15m46s): **12 passed, 0 failed**, with the smoke test
  reporting the identity precisely:

  ```
  [PASS] Sheets read/write: wrote and verified one row in 'ASHEVILLE_NC___Command_Center'
         as job identity (agency-pipeline-runtime@asheville-ai-agentic-automate.iam.gserviceaccount.com)
  [PASS] Durable ledger: durable ledger reachable (2 suppressed, 2 contacted)
  ```

  Nothing is outstanding. To roll back to the previous verified image if ever needed:

  ```powershell
  gcloud run jobs update agency-pipeline --region=us-east1 `
    --image=us-east1-docker.pkg.dev/asheville-ai-agentic-automate/cloud-run-source-deploy/agency-pipeline@sha256:59fee51a4d798506ce25cdc8777639eff31c83230938add1f8a326f3fe8f5da8
  ```

## Useful commands
```powershell
python -m unittest discover -s tests                  # 102 tests
python smoke_test.py --tenant asheville               # can this machine do the work?
python run_agency.py --sync-sheet                     # full pipeline
python email_dispatcher.py --tenant asheville         # DRY RUN, sends nothing
python grant_sheet_access.py                          # show sheet-sharing changes
python reconstruct_outreach_history.py                # rebuild history from bounces
gcloud run jobs execute agency-pipeline --region=us-east1
```

Note: `gcloud run jobs update --remove-volume a,b,c` reports success and silently
does nothing. Use a repeated `--remove-volume` flag per volume.

## Known, deliberately not done
- `run_agency.py` caps each step at 1200s. Charlotte's audit measured 7m45s, so
  there is headroom, but it remains a silent-partial-result risk as leads grow.
- The archived skills are staged in `OLD_FILES_TO_DELETE/`, awaiting Tom's approval
  for permanent deletion.
- Gmail still uses OAuth and cannot use a service account, because
  `lexiconatlas@gmail.com` is a consumer mailbox and domain-wide delegation requires
  Workspace. If that refresh token is revoked, `inbox_monitor.py` needs a local
  browser re-authorization.
- These MCP connectors are unauthorized and unusable until Tom authorizes them in
  claude.ai connector settings: **Stripe** (relevant to G3 payment links), Vercel,
  CodeWords, Anthropic Economic Index.

## Exact Next Action
1. Confirm `agency-pipeline-4ddjg` shows `[PASS] smoke_test` with both checks green.
2. Resume monitoring `lexiconatlas@gmail.com` for prospect replies.
3. Do not enable cloud dispatch without a separate explicit approval.
