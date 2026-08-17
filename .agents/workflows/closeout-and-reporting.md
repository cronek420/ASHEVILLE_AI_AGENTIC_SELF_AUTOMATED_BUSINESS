# Workflow: Closeout & Reporting

```yaml
agent: Atlas-Orchestrator
stage: Stage 8
```

## Steps
1. Reconcile all live Google Sheet tabs (`Prospect Tracker`, `48-Hour Plan`, `Approval Queue`, `Client Delivery`, `Activity Log`).
2. Generate Stage 8 Closeout Report with exact metrics:
   - Qualified prospects
   - Contacts attempted & replies received
   - Positive replies & discovery calls
   - Proposals sent & jobs won
   - Deposits verified, balances collected, cash collected
   - Work delivered & QA status
   - Follow-ups due & pending approvals
   - Failures detected & corrections applied
   - Main operational blocker
   - Most valuable next action
3. Log summary entry in `Activity Log`.
