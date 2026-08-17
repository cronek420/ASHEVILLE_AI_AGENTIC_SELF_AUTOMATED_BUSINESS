# Failure Handling & Error Recovery Protocol

For every tool call, external action, or system operation, the environment MUST enforce systematic error handling and safe recovery.

## 1. Action Execution Protocol
1. **Record Intended Action:** Log target, payload, timestamp, and parameters before execution.
2. **Define Expected Result:** Establish clear, measurable success criteria.
3. **Detect Outcome:** Monitor for explicit success, tool failure, network timeout, or partial completion.
4. **Prevent Blind Retries:** DO NOT automatically retry failed network operations without verifying partial execution.
5. **Inspect Partial Completion:** Check if email was partially sent, form was submitted, or sheet cell was updated before re-attempting.

## 2. Evidence & Failure Logging
- Preserve all error output, status codes, response headers, and partial payloads.
- Mark affected task status as `Blocked` or `Error` in `48-Hour Plan` and `Prospect Tracker`.
- Append a detailed entry to `Activity Log`:
  - `run_id`
  - `timestamp`
  - `agent`
  - `action_attempted`
  - `error_code_or_message`
  - `evidence_summary`
  - `recovery_proposed`

## 3. Recovery Procedure
1. Propose the **smallest safe recovery action** (e.g. retry with updated parameters, mark prospect as uncontactable, flag for manual review).
2. If recovery changes the original approved action (e.g. alternate email address or message modification), obtain a **NEW approval** from Tom Gronek.
3. Workflows MUST be designed to be **idempotent**, ensuring restarting a run does not result in duplicate contact messages, duplicate payment requests, or duplicate records.
4. Never delete or erase activity history to make logs look cleaner. Correct mistakes by appending explicit correction records explaining what changed.
