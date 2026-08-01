# Worker Quarantine And Re-Enrollment Policy

## Purpose

Define Phase 0 worker quarantine, release, re-enrollment, and revocation behavior for Arc worker mini PCs. This policy is scaffolding only and does not implement worker control, attestation, update, or enrollment services.

## Policy Metadata

- Policy ref: `policy.worker_quarantine_reenrollment.phase0`
- Version: `policy-phase0-v1`
- Status: Draft scaffold.
- Owner role: Field IT reviewer.
- Applies to contracts: `worker.lifecycle`, `worker.heartbeat`, `task.execution`, `approval.token`, `incident.ops`, `evidence.artifact`.
- Evidence artifact types: `worker_lifecycle`, `worker_heartbeat`, `quarantine`, `incident`, `approval_token`.
- Fail-closed outcome: keep worker quarantined or revoked, block new assignments, revoke related tokens and leases, record evidence.
- Runbook: [Worker Re-Enrollment Runbook](../runbooks/worker-reenrollment.md).

## Must Not

- Do not release a worker without Guardian, evidence, identity/channel checks, and role approval.
- Do not reuse revoked capability leases or old approval tokens.
- Do not assign customer tasks while quarantined.
- Do not trust prior local cache after compromise suspicion.
- Do not silently reactivate revoked or replaced workers.

## Quarantine Triggers

Automatic or manual quarantine may be triggered by:

- Missed heartbeat threshold.
- Identity verification failure.
- Channel identity mismatch.
- Capability manifest hash mismatch.
- Capability lease mismatch.
- Evidence writer failure.
- Suspicious tool request.
- Prompt injection suspicion.
- Unapproved privileged action attempt.
- Update or rollback verification failure.
- Operator containment request.
- LIMA IT or security incident handoff.

## Manual Quarantine

Manual quarantine may be initiated by an operator, supervisor admin, security reviewer, or field IT reviewer.

Manual quarantine requires:

- Reason code.
- Operator/reviewer identity ref.
- Guardian decision.
- Evidence artifact.
- Active task disposition.

## Automatic Quarantine

Automatic quarantine may be recommended by Guardian policy or supervisor health checks.

Automatic quarantine must:

- Stop new task assignment.
- Revoke capability lease.
- Revoke outstanding approval tokens bound to the worker.
- Preserve evidence refs.
- Notify operator dashboard.

## Quarantine States

Allowed policy states:

- `not_quarantined`.
- `quarantine_requested`.
- `quarantined`.
- `release_requested`.
- `released`.
- `revoked`.
- `replaced`.

## Allowed Actions While Quarantined

Allowed actions:

- Read-only health reporting.
- Evidence retry or upload.
- Operator review.
- Security review.
- Field IT diagnostic review.
- Local cache purge planning.
- Re-enrollment preparation.
- Revoke or replace worker.

## Blocked Actions While Quarantined

Blocked actions:

- New task assignment.
- Tool invocation except read-only diagnostics explicitly allowed by Guardian.
- Model calls for customer tasks.
- Connector access.
- File mutation.
- External messages.
- Durable memory writes.
- Approval token consumption.
- LIMA IT remediation.

## Evidence Requirements

Evidence required for:

- Quarantine trigger.
- Guardian decision.
- Worker heartbeat anomaly.
- Capability or policy hash mismatch.
- Approval token revocation.
- Release request.
- Release approval or denial.
- Re-enrollment.
- Revocation or replacement.

## Release Process

Release from quarantine requires:

1. Operator-visible reason for release.
2. Guardian decision allowing release.
3. Identity and channel identity check.
4. Capability manifest hash verification.
5. Policy/model hash verification.
6. Evidence writer healthy.
7. No active unresolved high-risk incident.
8. Approval by required role.
9. Evidence recorded.

If any step is missing or ambiguous, release fails closed.

## Re-Enrollment

Re-enrollment is required when:

- Worker was revoked.
- Device identity changed.
- Capability manifest cannot be verified.
- Local cache purge cannot be confirmed.
- Update/rollback state is unknown.
- Operator chooses replacement flow.

Re-enrollment must use new capability lease and evidence refs. Prior approval tokens must not carry forward.

## Policy / Model Hash Verification

Before release or re-enrollment:

- Verify worker policy version and hash refs match supervisor policy.
- Verify model route policy refs are current.
- Verify tool-pack scope version is expected.
- Verify local model status is policy-allowed.

Any mismatch blocks release.

## Attestation Placeholder

Hardware attestation is not selected in Phase 0.

Until selected, `attestation_status` remains `not_required_phase0` or `pending`. Attestation absence cannot be treated as stronger trust.

## Revocation

Revocation is terminal for that worker enrollment generation.

Revocation requires:

- Capability lease revoked.
- Approval tokens revoked.
- New tasks blocked.
- Active tasks cancelled, blocked, or requeued.
- Evidence recorded.
- Re-enrollment or replacement plan documented.

## MVP Acceptance Gates

- Quarantined worker cannot receive new tasks.
- Quarantined worker cannot consume approval tokens.
- Release requires Guardian, evidence, and role approval.
- Re-enrollment uses new lease and evidence.
- Revoked worker cannot resume without re-enrollment.
- No production remediation is implied.
