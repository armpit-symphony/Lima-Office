# Worker Attestation Failure Runbook

## Purpose

Contain a worker when identity, attestation, policy hash, model hash, runtime
hash placeholder, or capability manifest posture fails review.

## When To Use

- Worker attestation fails or is ambiguous.
- Policy or model hash mismatch occurs.
- Capability manifest changes unexpectedly.
- Device identity or channel identity mismatch is detected.
- Re-enrollment is requested after quarantine.

## Prerequisites

- [Worker Attestation Policy](../governance/WORKER_ATTESTATION_POLICY.md)
- [Worker Quarantine And Re-Enrollment](../policies/worker-quarantine-reenrollment.md)
- [Worker Lifecycle](../deployment/WORKER_LIFECYCLE.md)
- Worker deployment, lifecycle, and heartbeat records.

## Steps

1. Confirm worker ID, deployment ID, and tenant/customer context.
2. Stop new assignment in planning records.
3. Mark worker degraded, quarantined, revoked, or re-enrollment pending as
   policy requires.
4. Record failed identity, attestation, policy hash, model hash, or capability
   reason.
5. Capture evidence refs.
6. Require security reviewer for release from security quarantine.
7. Require field IT reviewer for hardware, OS, network, and device custody
   checks.
8. Require cache purge proof where revoke, retirement, or replacement is in
   scope.

## Approval Requirements

- Security quarantine release requires security reviewer approval.
- Re-enrollment requires operator review, identity recheck, capability review,
  policy review, and evidence.
- Automated re-enrollment remains blocked.

## Evidence To Capture

- Worker ID and deployment ID.
- Failed check type.
- Hash refs.
- Device/channel identity refs.
- Quarantine or revoke record.
- Cache purge proof refs where applicable.
- Evidence refs.

## Rollback / Containment

- Quarantine worker.
- Revoke capability lease if needed.
- Revoke approval tokens bound to the worker where policy requires.
- Block privileged actions until re-enrollment is approved.

## Escalation

Escalate to security reviewer for identity/capability mismatch and to field IT
reviewer for hardware, OS, or network custody issues.

## Done Criteria

- Worker is quarantined, revoked, retired, or explicitly re-enrollment pending.
- Evidence refs exist.
- Release criteria are documented.
- Privileged work remains blocked until all gates pass.
