# Worker Quarantine Runbook

## Purpose

Contain a worker that may be compromised, misconfigured, offline, or outside policy.

## When To Use

Use when heartbeat fails, identity cannot be verified, capability manifest
changes unexpectedly, evidence writing fails, prompt injection is suspected,
repeated Guardian replay/stale-decision use appears, clock skew exceeds policy,
or an operator requests containment.

## Prerequisites

- Supervisor registry is accessible.
- Operator can view worker status and recent evidence.
- Quarantine authority is available.

## Steps

1. Identify affected worker and tenant.
2. Stop new task assignments to the worker.
3. Mark worker `quarantined`.
4. Record quarantine reason.
5. Revoke active approval tokens scoped to that worker.
6. Revoke the worker capability lease and disable privileged tool packs for that worker.
7. Preserve recent heartbeat, task, and evidence records.
8. Preserve Guardian decision and `guardian.replay` records tied to the worker.
9. Review last capability manifest and task transitions.
10. Determine whether LIMA IT diagnostic handoff is needed.
11. Keep worker quarantined until the re-enrollment runbook clears release, re-enrollment, revocation, or replacement.

## Approval Requirements

Quarantine can be initiated as containment. Release from quarantine requires operator approval and evidence.

## Evidence To Capture

- Worker ID.
- Tenant ID.
- Quarantine reason.
- Triggering event.
- Guardian decision ID.
- Guardian replay check result, if replay, stale, expiry, or clock-skew
  triggered containment.
- Active tasks affected.
- Approval tokens revoked.
- Operator identity.

## Rollback/Containment

Rollback is release from quarantine only after review, identity/channel recheck, capability hash verification, evidence writer health, and evidence capture. If compromise is suspected, revoke and replace instead.

## Escalation

Escalate to security reviewer for suspected compromise. Escalate to LIMA IT for diagnostics if device or network health is involved.

## Done Criteria

- Worker receives no new assignments.
- Quarantine state is visible.
- Evidence is recorded.
- Operator has a release, revoke, or replace path.
- Re-enrollment uses the dedicated [Worker Re-Enrollment Runbook](worker-reenrollment.md).
