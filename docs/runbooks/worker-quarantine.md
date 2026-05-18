# Worker Quarantine Runbook

## Purpose

Contain a worker that may be compromised, misconfigured, offline, or outside policy.

## When To Use

Use when heartbeat fails, identity cannot be verified, capability manifest changes unexpectedly, evidence writing fails, prompt injection is suspected, or an operator requests containment.

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
6. Disable privileged tool packs for that worker.
7. Preserve recent heartbeat, task, and evidence records.
8. Review last capability manifest and task transitions.
9. Determine whether LIMA IT diagnostic handoff is needed.
10. Keep worker quarantined until operator review clears release or replacement.

## Approval Requirements

Quarantine can be initiated as containment. Release from quarantine requires operator approval and evidence.

## Evidence To Capture

- Worker ID.
- Tenant ID.
- Quarantine reason.
- Triggering event.
- Guardian decision ID.
- Active tasks affected.
- Approval tokens revoked.
- Operator identity.

## Rollback/Containment

Rollback is release from quarantine only after review. If compromise is suspected, revoke and replace instead.

## Escalation

Escalate to security reviewer for suspected compromise. Escalate to LIMA IT for diagnostics if device or network health is involved.

## Done Criteria

- Worker receives no new assignments.
- Quarantine state is visible.
- Evidence is recorded.
- Operator has a release, revoke, or replace path.
