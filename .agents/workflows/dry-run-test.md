# Workflow: Required Operational Test Suite (Dry-Run Mode)

```yaml
agent: Atlas-Orchestrator
type: Verification Suite
mode: Dry-Run (Mock / Test Records Only - No Real Businesses Contacted)
```

## 18 Required Operational Tests

Execute and verify all 18 tests prior to declaring the environment operational:

1. **Agent Instruction Discovery:** Verify all 9 specialist agent definitions and workflows load properly from `.agents/`.
2. **Run-ID Generation:** Confirm strict format compliance (`RUN-YYYYMMDD-HHMM-XX`).
3. **Active-Offer Detection:** Verify system reads and parses active offer cell in `Start Here`.
4. **Multiple-Active-Offer Blocking:** Simulate >1 active offers and verify system halts with error.
5. **Missing-Active-Offer Blocking:** Simulate 0 active offers and verify system halts with error.
6. **Specialist Change-Packet Validation:** Pass valid & invalid JSON/YAML packets to verify schema enforcement.
7. **Single-Writer Enforcement:** Confirm specialist agents cannot write directly and only Orchestrator writes.
8. **Duplicate-Prospect Detection:** Feed duplicate business/domain/email and verify rejection.
9. **Do-Not-Contact Enforcement:** Attempt outreach to DNC prospect and verify immediate block.
10. **Approval Lookup:** Verify correct lookup of G0–G5 approvals in `Approval Queue`.
11. **Expired-Approval Rejection:** Simulate expired approval timestamp and verify rejection.
12. **Approval-Condition Enforcement:** Verify action is blocked if conditional requirements are not met.
13. **Spreadsheet Read and Write Verification:** Test read-back verification on cell updates.
14. **Activity-Log Append Behavior:** Verify append-only logging format without history deletion.
15. **Failed-Action Recovery:** Simulate network failure and verify `Blocked`/`Error` status + recovery proposal.
16. **Restart Without Duplicate Actions:** Simulate run restart and verify no duplicate messages/writes occur.
17. **Secret-Detection Protections:** Pass mock API keys/passwords in packet and verify secret redactor blocks it.
18. **Dry-Run Mode:** Confirm complete operating loop runs end-to-end in simulation mode with 0 external network side-effects.
