# Workflow: Fulfillment and QA (G4 Gate)

```yaml
agents: Delivery-Builder, QA-Risk
governance: .agents/rules/02-approval-gates.md
```

## Steps
1. **Scope & Deposit Verification:** Confirm written scope and verified payment status (G3 approved & deposit verified).
2. **Build Deliverable:** `Delivery-Builder` completes client work within isolated, non-production workspace.
3. **QA-Risk Testing Audit:** `QA-Risk` validates:
   - Functional links and interactive elements
   - Mobile and desktop responsive behavior
   - Content accuracy matching written scope
   - Privacy, permission, and backup safeguards
   - Rollback procedures established
4. **Submit G4 Approval Request:** Return Change Packet to `Atlas-Orchestrator` for client system access, publishing, or deliverable transfer.
5. **Execute Hand-off:** Transfer completed asset to client upon receiving explicit G4 approval.
