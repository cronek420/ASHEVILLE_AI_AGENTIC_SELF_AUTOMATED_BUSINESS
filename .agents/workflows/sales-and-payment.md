# Workflow: Sales & Payment Handling (G3 Gate)

```yaml
agents: Sales-Coordinator, Finance-Recorder
governance: .agents/rules/02-approval-gates.md
```

## Steps
1. **Classify Prospect Response:** Categorize reply (Positive Interest, Discovery Question, Objection, Opt-Out, Not Interested).
2. **Draft Discovery / Scope Response:** Formulate written scope of work matching approved offer parameters.
3. **Generate G3 Approval Request:** Draft proposal, invoice details, deposit requirement, and payment provider link. Return Change Packet to `Atlas-Orchestrator`.
4. **Wait for G3 Approval:** DO NOT send proposal, invoice, or payment link until status is `Approved` in `Approval Queue`.
5. **Verify Deposit:** Upon customer payment, `Finance-Recorder` verifies deposit in merchant account, logs transaction in `Activity Log`, and updates `Client Delivery` tab.
