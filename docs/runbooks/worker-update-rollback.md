# Worker Update Rollback Runbook

## Purpose

Plan and review Arc worker update or rollback posture without implementing
automatic update execution.

## When To Use

Use when a policy bundle, worker runtime, model bundle, or config change is
proposed for a worker.

## Prerequisites

- Worker is enrolled and visible to the Supervisor Server.
- Current policy/model/config refs are recorded.
- Known-good rollback refs are recorded.
- Operator can review the update request.
- No automatic install/update execution is being attempted.

## Procedure

1. Identify update channel: policy bundle, worker runtime, model bundle, or
   config.
2. Record proposed update ref and current known-good ref.
3. Confirm signed or verified source expectation is satisfied or mark update
   blocked.
4. Request Guardian decision for the update plan.
5. Capture operator approval if the update affects software, model bundle,
   policy scope, or config.
6. Stage rollout as a planning record for one lab worker only.
7. Monitor heartbeat, evidence writer status, policy/model hash refs, and
   resource posture.
8. If verification fails, quarantine or degrade the worker and record rollback
   evidence.
9. Keep automatic update execution blocked until a later approved runtime plan
   exists.

## Approval Requirements

Software install/update execution requires approval and is not implemented here.
Policy, model, and config changes require operator visibility, Guardian
decision, and evidence refs.

## Evidence To Capture

- Worker ID and deployment ID.
- Update channel.
- Proposed update ref.
- Previous known-good ref.
- Guardian decision ID.
- Operator approval/refusal.
- Heartbeat before and after planned update.
- Rollback or quarantine result.

## Rollback/Containment

- Verification failure: quarantine or degrade worker.
- Policy/model hash mismatch: stop assignment and request review.
- Evidence failure: block privileged work and follow
  [Evidence writer failure](evidence-writer-failure.md).
- Suspicious update source: raise [Security incident](security-incident.md).

## Escalation Path

- Update verification failure: field IT reviewer and security reviewer.
- Capability change outside scope: security reviewer.
- Suspected supply-chain issue: security incident.
- Remediation request: LIMA IT handoff metadata only; execution remains blocked
  for MVP.

## Done Criteria

- Update/rollback record is captured.
- Worker state is active, degraded, quarantined, or revoked with evidence.
- Known-good rollback ref remains available as metadata.
- No automatic update execution was performed by this runbook.
