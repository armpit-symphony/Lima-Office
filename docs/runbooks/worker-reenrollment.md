# Worker Re-Enrollment Runbook

## Purpose

Guide an operator through safely releasing, re-enrolling, revoking, or replacing a quarantined Arc worker.

## Policy Traceability

- Policy ref: `policy.worker_quarantine_reenrollment.phase0`
- Version: `policy-phase0-v1`
- Triggering contracts: `worker.lifecycle`, `worker.heartbeat`, `approval.token`, `task.execution`, `incident.ops`, `evidence.artifact`.
- Required fields: tenant/customer context, worker ID, quarantine state/reason, device/channel identity refs, capability lease/hash refs, token revocation refs, Guardian decision ID, evidence artifact IDs, correlation ID.
- Fail-closed outcome: keep worker quarantined or revoked, block new assignments, require new lease and evidence for re-enrollment.

## When To Use

Use this runbook when:

- Worker is quarantined.
- Worker was revoked.
- Capability manifest hash changed.
- Device or channel identity changed.
- Evidence writer failed.
- Update verification failed.
- Worker replacement is needed.

## Prerequisites

- Worker lifecycle record.
- Latest worker heartbeat.
- Guardian decision.
- Quarantine reason code.
- Capability manifest hash ref.
- Capability lease ID.
- Evidence artifact refs.
- Active task and approval token list.

## Must Not

- Do not release a worker with missing evidence.
- Do not reuse old approval tokens.
- Do not reuse a revoked capability lease.
- Do not assign new tasks while quarantined.
- Do not trust prior local cache after compromise suspicion.
- Do not treat missing attestation as stronger trust.

## Procedure

1. Confirm quarantine reason and affected tasks.
2. Stop new assignments.
3. Revoke approval tokens bound to the worker.
4. Revoke old capability lease if quarantine is confirmed.
5. Check device identity ref and channel identity ref.
6. Check capability manifest version and hash ref.
7. Check policy/model hash refs.
8. Check evidence writer state.
9. Decide one of:
   - Keep quarantined.
   - Release after review.
   - Re-enroll with new lease.
   - Revoke and replace.
10. For re-enrollment, create new enrollment evidence and new capability lease.
11. Confirm active task disposition: cancel, block, or requeue.
12. Record release, re-enrollment, revoke, or replacement evidence.

## Approval Requirements

Release requires the role defined by policy, normally operator plus security reviewer or field IT reviewer depending on reason.

Re-enrollment after identity mismatch, evidence failure, or suspicious tool request requires security review.

## Evidence To Capture

- Quarantine trigger.
- Operator/reviewer identity.
- Guardian release or revoke decision.
- Identity and channel checks.
- Capability/policy/model hash verification.
- Approval token revocation.
- Local cache disposition.
- New capability lease ID if re-enrolled.

## Containment / Rollback

- If release check fails, keep worker quarantined.
- If identity cannot be verified, revoke worker.
- If local cache cannot be trusted, require purge/replacement plan before re-enrollment.
- If evidence writer remains failed, block re-enrollment.

## Escalation

Escalate to:

- Security reviewer for identity mismatch, suspicious tool request, prompt injection, or evidence tampering.
- Field IT reviewer for hardware, OS, network, update, or rollback issues.
- Supervisor admin for replacement decisions.

## Done Criteria

- Worker state is released, re-enrolled, revoked, or replaced.
- New tasks are blocked unless release/re-enrollment completed.
- Old tokens and leases are revoked when required.
- Evidence refs are recorded.
- Tenant/customer context and correlation ID are preserved.
