# User Control Commands

Tom Gronek can control the operating environment at any time using these standard commands:

- **`START` / `RUN`**: Initiates a new operating session using `.agents/workflows/run-operating-loop.md`.
- **`PAUSE`**: Pauses ongoing internal work at the end of the current task. Preserves current state in Google Sheet and `Activity Log`.
- **`RESUME`**: Resumes a paused session, re-reading state from the Google Sheet and checking for new approvals.
- **`STOP`**: Immediately halts all operations, logs the stop reason, and produces a Stage 8 closeout report.
- **`DRY-RUN`**: Executes the 18-step verification test suite (`.agents/workflows/dry-run-test.md`) in mock mode.
- **`APPROVE <ID>`**: Approves a pending G0–G5 gate request in `Approval Queue`.
- **`REJECT <ID>`**: Denies a pending gate request with optional notes for agent revision.
