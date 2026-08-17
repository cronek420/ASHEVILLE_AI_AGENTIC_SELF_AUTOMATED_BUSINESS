# Performance Baseline & Metrics Ledger

This document tracks quantitative system metrics across operating runs to measure self-annealing continuous improvement.

## Key Performance Indicators (KPIs)

| Metric Category | Metric Name | Baseline Value | Current Target | Current Value | Status |
| --- | --- | --- | --- | --- | --- |
| **Accuracy** | First-Attempt Success Rate | 100% (Dry-Run) | >= 95% | 100% | Optimal |
| **Accuracy** | Write-Verification Rate | 100% | 100% | 100% | Optimal |
| **Safety** | Unauthorized External Action Rate | 0% | 0% | 0% | Protected |
| **Safety** | Secret Redaction / Leak Rate | 0% | 0% | 0% | Protected |
| **Efficiency** | Dry-Run Test Execution Time | ~0.05s | < 1.0s | 0.05s | Optimal |
| **Efficiency** | Tool Calls Per Completed Task | Minimizing | Optimal | Tracked | Active |
| **Quality** | Duplicate / DNC Prevention Rate | 100% | 100% | 100% | Optimal |
| **Quality** | Handoff Rejection Rate | 0% | < 5% | 0% | Optimal |

## Run Historical Metrics Log

```yaml
run_id: RUN-20260803-2200-01
date: 2026-08-04
first_attempt_success: true
tasks_completed: 18 (Operational Tests)
tool_calls_used: 1 (command_center_adapter execution)
duplicates_prevented: 1
dnc_prevented: 1
secrets_blocked: 1
approval_violations: 0
recovery_time_seconds: 0
```
