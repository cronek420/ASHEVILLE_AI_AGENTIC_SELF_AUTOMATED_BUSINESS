# Self-Annealing Operating Workflow

Use this workflow to execute the complete self-annealing continuous-improvement cycle:
**Observe → Record → Diagnose → Propose → Test → Measure → Adopt or Roll Back → Reuse**

---

## 1. Startup Procedure

Before starting any task or operating run:

1. **Read Active Task & State:** Read active task requirements, current approval status in `Approval Queue`, and active offer in `Start Here`.
2. **Load Relevant Lessons:** Read `.agents/memory/lessons-learned.md` for adopted lessons tagged with `reuse_scope: system` or `reuse_scope: workflow`. Ignore `rejected` or `rolled_back` entries.
3. **Check Known Error Patterns:** Inspect `.agents/memory/error-patterns.jsonl` for high-frequency categories related to the current task.
4. **Apply Preventive Controls:** Enforce pre-flight checklists from `.agents/memory/successful-patterns.md`.

---

## 2. 13-Point Required Learning Review

After every run, phase, error, or business test, execute the 13-point learning evaluation:

1. **What was expected?** (Document planned outcome).
2. **What actually happened?** (Document actual outcome).
3. **What evidence confirms the result?** (Logs, screenshots, file paths, test results).
4. **Was it successful, partial, blocked, or failed?**
5. **What was the root cause?** (Identify underlying systemic cause, not symptoms).
6. **Could the problem have been detected earlier?**
7. **Has a similar issue happened before?**
8. **What is the smallest useful improvement?**
9. **How can that improvement be tested safely?**
10. **What metric will prove it helped?**
11. **Could it introduce new risks?**
12. **Does it require Tom’s approval?** (Level 0/1: None; Level 2/3: Tom/G5).
13. **Should it be adopted, monitored, rejected, or rolled back?**

---

## 3. Error Categorization & Diagnosis

Classify any meaningful problem into one or more of the 16 standard categories:

- `INSTRUCTION_ERROR` — Missing, unclear, outdated, or conflicting instructions.
- `PLANNING_ERROR` — Incorrect order, dependencies, scope, or stopping rules.
- `ASSUMPTION_ERROR` — Unverified assumption treated as fact.
- `RESEARCH_ERROR` — Unsupported, outdated, or misinterpreted information.
- `TOOL_ERROR` — Incorrect tool use, timeout, failure, or incomplete result.
- `PERMISSION_ERROR` — Missing access or approval.
- `HANDOFF_ERROR` — Incomplete or incompatible agent output.
- `STATE_ERROR` — Files, spreadsheet, and real state do not agree.
- `DUPLICATION_ERROR` — Repeated work, contacts, records, or actions.
- `VALIDATION_ERROR` — Output accepted without adequate testing.
- `COMMUNICATION_ERROR` — Unclear request, status, message, or approval.
- `SECURITY_ERROR` — Secrets, permissions, or private data mishandled.
- `BUSINESS_ERROR` — Weak offer, audience, message, proof, timing, or price.
- `EFFICIENCY_ERROR` — Correct result with unnecessary time, steps, or cost.
- `EXTERNAL_CHANGE` — Platform, API, market, website, or policy changed.
- `UNKNOWN` — Evidence does not yet establish the cause.

---

## 4. 18-Field Lesson Record Generation

Record lessons in `.agents/memory/lessons-learned.md` using the exact 18-field schema:

```yaml
lesson_id: LESSON-YYYYMMDD-XX
run_id: RUN-YYYYMMDD-HHMM-XX
agent: agent-name
task: task description
classification: ERROR_CATEGORY
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

---

## 5. Safe 10-Step Testing Procedure

For any proposed improvement:

1. Preserve current version / baseline.
2. Record baseline metric.
3. Change **one variable at a time**.
4. Test in dry-run or sandbox mode (0 side effects).
5. Test normal and failure cases.
6. Compare results against baseline.
7. Confirm protected rules (gates, single-writer, truthfulness) remain 100% intact.
8. Record results in `.agents/memory/performance-baseline.md`.
9. Adopt only if success metric is satisfied.
10. Roll back immediately if accuracy, safety, or quality worsens.

---

## 6. Closeout Report Structure

End every operating run with the standardized closeout summary:

```yaml
run_id: RUN-YYYYMMDD-HHMM-XX
result: completed | partial | blocked | failed
what_worked:
  - verified success
what_failed:
  - verified problem
new_lessons:
  - lesson ID or none
improvements_tested:
  - change and result
improvements_adopted:
  - change or none
rollbacks:
  - change and reason or none
metrics_changed:
  - metric: before -> after
approval_needed:
  - approval ID or none
next_improvement: one specific recommendation
```
