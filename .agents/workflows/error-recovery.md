# Workflow: Error Recovery

```yaml
agent: Atlas-Orchestrator
governance: .agents/rules/05-failure-and-recovery.md
```

## Steps
1. **Detect Failure:** Identify tool error, API timeout, partial execution, or packet validation rejection.
2. **Preserve Evidence:** Save raw error logs, HTTP status codes, or stack traces without erasing history.
3. **Mark Blocked Status:** Update affected row in `48-Hour Plan` or `Prospect Tracker` to `Blocked` or `Error`.
4. **Append Activity Log:** Record incident with `run_id`, timestamp, error summary, and evidence.
5. **Formulate Smallest Safe Recovery:**
   - If internal error: fix parameters and re-attempt.
   - If external error: check if action partially executed before retrying.
   - If change required: submit updated approval request to Tom Gronek.
6. **Re-Verify Idempotency:** Ensure restart will not create duplicate outreach messages, duplicate payment links, or corrupt spreadsheet state.
