# Reusable Lessons Learned Ledger

This ledger records all system lessons learned across operations. Every entry strictly follows the 18-field YAML schema.

## Schema Specification

```yaml
lesson_id: LESSON-YYYYMMDD-XX
run_id: RUN-YYYYMMDD-HHMM-XX
agent: agent-name
task: task description
classification: ERROR_CATEGORY | SUCCESS_PATTERN
expected: expected outcome
actual: actual outcome
evidence:
  - source, log, test, file, or URL
root_cause: verified cause or UNKNOWN
impact: time, cost, business effect, or risk
proposed_change: smallest useful improvement
risk: low | medium | high
approval: none | G0 | G1 | G2 | G3 | G4 | G5
test: safe test method
success_metric: measurable acceptance condition
status: proposed | testing | adopted | monitoring | rejected | rolled_back
rollback: reversal method
reuse_scope: task | workflow | agent | system
```

## Adopted Lessons

```yaml
lesson_id: LESSON-20260804-01
run_id: RUN-20260803-2200-01
agent: Atlas-Orchestrator
task: System Initialization & Dry-Run Operational Verification
classification: SUCCESS_PATTERN
expected: Establish single-writer engine and pass all operational tests with zero side-effects.
actual: Passed 18 operational test suite cases in dry-run mode.
evidence:
  - file:///c:/Users/crone/Projects/ASHEVILLE_AI_AGENTIC_SELF_AUTOMATED_BUSINESS/ASHEVILLE_AI_AGENTIC_SELF_AUTOMATED_BUSINESS/command_center_adapter.py
root_cause: Clean single-writer lock abstraction and strict schema validation prevents unsafe writes.
impact: Prevents unauthorized direct state mutations by specialist agents.
proposed_change: Maintain dry-run operational test suite as prerequisite for live operations.
risk: low
approval: G0
test: Run command_center_adapter.py in dry-run mode.
success_metric: 100% test pass rate across operational tests.
status: adopted
rollback: Revert to manual spreadsheet checks.
reuse_scope: system

lesson_id: LESSON-20260804-02
run_id: RUN-20260804-0013-01
agent: Outreach-Drafter
task: Subject Line Drafting for Cold Outreach
classification: COMMUNICATION_ERROR
expected: Subject line engages local prospect effectively.
actual: Initial subject line ("Factual site performance & local search note for Ward Plumbing") felt corporate / automated.
evidence:
  - Tom's explicit instruction: "change the subject to something more friendly, short, interesting and says that i am a local real person, not a spam bot. remember this"
root_cause: Default corporate audit wording lacked conversational human warmth and local peer framing.
impact: Higher risk of prospect assuming automated spam and ignoring email.
proposed_change: Always craft outreach subject lines to be short, friendly, interesting, and explicitly frame Tom as a real local resident in Asheville (e.g., "Quick neighborly note from Tom in Asheville").
risk: low
approval: G2
test: Present payload to Tom for G2 review.
success_metric: Tom approval rate of subject lines without edits.
status: adopted
rollback: Revert to formal corporate subject titles.
reuse_scope: workflow

lesson_id: LESSON-20260804-03
run_id: RUN-20260804-0040-01
agent: Sales-Coordinator
task: Gmail Deliverability & Anti-Spam Sending Best Practices
classification: SUCCESS_PATTERN
expected: Ensure 100% inbox placement and prevent Gmail account flagging when dispatching outreach emails.
actual: Evaluated Google anti-spam rules, SMTP rate limits, plain-text formatting, and randomized delay pacing.
evidence:
  - Tom's directive: "make sure to know the right way to send emails so google dont think it is a spammer or bot first."
root_cause: Rapid script loops, HTML tracking pixels, spam trigger words, and missing headers trigger automated Gmail spam filters.
impact: Protects domain reputation, prevents inbox delivery failure, and avoids Gmail account suspension.
proposed_change: Mandate 4-part anti-spam sending protocol: 1) Plain-text formatting (no HTML templates/tracking pixels), 2) Paced delivery with 30-90 second randomized delays between dispatches, 3) Hyper-local personalized content per domain, 4) Proper From/Reply-To headers with clear opt-out footer.
risk: low
approval: G2
test: Test SMTP dispatch script in dry-run mode with delay logs before live send.
success_metric: Zero Gmail deliverability warnings, 100% successful SMTP handshake and inbox placement.
status: adopted
rollback: Manual copy-paste sending only.
reuse_scope: workflow

lesson_id: LESSON-20260804-04
run_id: RUN-20260804-0043-01
agent: Sales-Coordinator
task: Live Gmail SMTP Authentication
classification: PERMISSION_ERROR
expected: Authenticate with smtp.gmail.com:587 using App Password.
actual: Received Google 535 5.7.8 Bad Credentials error response.
evidence:
  - Log output: (535, b'5.7.8 Username and Password not accepted. For more information, go to https://support.google.com/mail/?p=BadCredentials')
root_cause: Mismatch between SMTP_USER (lexiconatlas@gmail.com vs lexiatlas@gmail.com) or unverified 16-character App Password key in .env file.
impact: Prevents automated background email dispatch via Google SMTP.
proposed_change: Verify exact matching Gmail address in .env (SMTP_USER) and confirm 2-Step Verification + fresh 16-character Google App Password generation.
risk: low
approval: none
test: Execute python smtp_outreach_dispatcher.py --dry-run or 1-shot test.
success_metric: 250 Authentication Successful response from Google SMTP.
status: adopted
rollback: Use manual email copy-paste sending until App Password is re-verified.
reuse_scope: workflow

lesson_id: LESSON-20260804-06
run_id: RUN-20260804-0143-01
agent: Atlas-Orchestrator
task: Live Google Sheets ADC Authentication Scopes
classification: PERMISSION_ERROR
expected: Authenticate Google Sheets API via gcloud Application Default Credentials (ADC).
actual: Received Google API 403 error: "Request had insufficient authentication scopes".
evidence:
  - Log output: gspread.exceptions.APIError: APIError: [403]: Request had insufficient authentication scopes.
root_cause: Default 'gcloud auth application-default login' generates credentials without explicit Google Sheets & Drive API scopes.
impact: Prevents live cloud sync to online Google Sheet using default ADC login.
proposed_change: Require explicit --scopes flag when logging into gcloud ADC: gcloud auth application-default login --scopes="https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive","https://www.googleapis.com/auth/cloud-platform".
risk: low
approval: none
test: Re-run gcloud login with --scopes and execute python test_adc_sync.py.
success_metric: 200 OK response from Google Sheets API and live worksheet update.
status: adopted
rollback: Use Service Account client_secret.json key file for Google Sheets API.
reuse_scope: system

lesson_id: LESSON-20260804-07
run_id: RUN-20260804-0349-01
agent: Atlas-Orchestrator
task: User Google Account OAuth Scope Restrictions
classification: EXTERNAL_CHANGE
expected: Authorize Google Drive & Sheets scopes via gcloud ADC browser login.
actual: Google OAuth blocked the request: "This app tried to access sensitive info in your Google Account".
evidence:
  - Google OAuth Consent screen error message: "This app is blocked"
root_cause: Google OAuth policy blocks public unverified CLI client IDs from requesting sensitive Drive/Sheets scopes on personal @gmail.com accounts.
impact: Browser-based gcloud ADC login cannot be used for Google Sheets API sync on personal Gmail accounts.
proposed_change: Use dedicated Google Cloud Service Account JSON key (client_secret.json) or public web link / local adapter for Google Sheets sync.
risk: low
approval: none
test: Test gspread authentication using client_secret.json service account key.
success_metric: Direct API authentication without browser consent blocks.
status: adopted
rollback: Use local adapter and SESSION_HANDOFF.md tracking.
reuse_scope: system

lesson_id: LESSON-20260804-08
run_id: RUN-20260804-0421-01
agent: Atlas-Orchestrator
task: GCP Org Policy Key Creation Constraint Workaround
classification: EXTERNAL_CHANGE
expected: Create Google Cloud Service Account JSON key.
actual: GCP returned Org Policy constraint error: iam.disableServiceAccountKeyCreation is enforced.
evidence:
  - Log output: Service account key creation is disabled. Enforced Organization Policies IDs: iam.disableServiceAccountKeyCreation.
root_cause: Google Cloud Org Policy disables raw service account key downloads by default on managed organizations.
impact: Cannot download raw Service Account JSON key without turning off constraint or using OAuth Client ID.
proposed_change: Provide 2 alternative options: 1) Create Desktop OAuth Client ID credential (client_secret.json) or 2) Edit GCP Org Policy to set iam.disableServiceAccountKeyCreation to Not Enforced.
risk: low
approval: none
test: Test gspread.oauth() with Desktop App client_secret.json.
success_metric: 200 OK response from Google Sheets API.
status: adopted
rollback: Continue local single-writer state adapter tracking.
reuse_scope: system
lesson_id: LESSON-20260813-01
run_id: RUN-20260813-0001-01
agent: Atlas-Orchestrator
task: Google Sheets Row Appending via gspread
classification: SUCCESS_PATTERN
expected: Appending new rows places them directly underneath existing visible data (e.g. Row 6).
actual: New rows were appended at Row 210, out of user view, appearing as if the sheet failed to sync.
evidence:
  - User reported "Approval Queue is still empty" despite successful sync logs.
  - Inspection revealed rows 6-209 contained hidden dropdown validation metadata.
root_cause: Pre-formatted templates with dropdowns/data validation cause empty rows to be evaluated as "used" by gspread's append_row and _last_used_row logic.
impact: Users assume pipeline failed because data is appended below hundreds of blank but "formatted" rows.
proposed_change: Remove dropdowns/data validation from blank rows in template sheets, or proactively scan and delete "empty domain" formatted rows before appending.
risk: low
approval: G0
test: Sync a test row to a freshly formatted template sheet and confirm it lands on Row 6, not 200+.
success_metric: 100% of newly synced rows appear directly below the last populated row in human view.
status: adopted
rollback: Revert template to pre-filled 200 dropdown rows.
reuse_scope: workflow
```

## Active Proposals & Testing

*(No pending proposals currently in testing)*

## Archived / Rejected / Rolled Back Lessons

*(No rejected or rolled back lessons recorded)*
