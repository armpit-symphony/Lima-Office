# Health Checks Runbook

## Purpose

Review Supervisor Server and Arc worker health in lab mode.

## When To Use

Use during routine lab checks, before onboarding a worker, after a failed heartbeat, after update planning, or before LIMA IT handoff.

## Prerequisites

- Operator dashboard or status summary is available.
- Worker registry exists.
- Evidence writer status is visible.
- No live connector actions are enabled.

## Steps

1. Check Supervisor Server service state.
2. Check worker list and status.
3. Review last heartbeat timestamp and age for each worker.
4. Review missed heartbeat count.
5. Review task queue depth and approval queue age.
6. Review Guardian allow/deny/approval counts.
7. Review Guardian decision age, expiry remaining, replay-check result counts,
   and clock-skew warnings.
8. Review evidence write success/failure.
9. Review local model status and model routing posture.
10. Review mock connector readiness states.
11. Review disk, memory, CPU, and network posture.
12. Record degraded, offline, stale-decision, replay-denied, or quarantined
   states.
13. Open incident or quarantine runbook if thresholds are crossed.

## Approval Requirements

Read-only health checks do not require human approval beyond normal operator access. Diagnostic gathering means metadata/ref-based checks only: no secrets, no raw sensitive payload dumps, no mutation, and no hidden background work.

Software updates, remediation, endpoint changes, network changes, and production server touch are blocked from execution in Phase 0 unless future policy and contracts explicitly authorize them.

## Evidence To Capture

- Health check timestamp.
- Operator identity.
- Supervisor health.
- Worker heartbeat summary.
- Guardian decision summary.
- Guardian replay summary, including stale, expired, replay-denied, and
  clock-skew-denied counts when present.
- Evidence writer status.
- Quarantine or incident references.
- LIMA IT handoff ID if created.

## Rollback/Containment

If health checks reveal unsafe state, stop new assignments to affected worker and use the worker quarantine runbook.

## Escalation

Escalate repeated heartbeat failures, evidence write failures, suspicious model/tool requests, or device/network issues to the appropriate reviewer or LIMA IT diagnostic handoff.

## Done Criteria

- Health state is recorded.
- Any degraded/offline/quarantined worker has a next action.
- Evidence exists for the check.
- No remediation, endpoint/network change, software update, or production touch was executed.
