# Signed Update Rollback Policy

## Purpose

Define the governance requirements for policy bundle, worker runtime, model
bundle, and config updates before any update or rollback mechanism exists.

Policy ref: `policy.signed_update_rollback.phase0`

Status: draft scaffold. No update agent, installer, service, scheduler, or
rollback automation is implemented.

Metadata records for this policy lane are represented by:

- [governance.update_record.schema.json](../../contracts/v1/governance.update_record.schema.json)
- [update.rollback.schema.json](../../contracts/v1/update.rollback.schema.json)
- [attestation.result.schema.json](../../contracts/v1/attestation.result.schema.json)
- [Signed Update Rollback Review Runbook](../runbooks/signed-update-rollback-review.md)

## Signed Update Expectation

Future updates must have:

- Source ref.
- Version ref.
- Hash ref.
- Signature or verification ref.
- Approval refs where required.
- Known-good rollback ref.
- Evidence refs.

Signing format and trust root are unresolved.

## Update Types

### Policy Bundle

- Changes Guardian decision behavior.
- Requires policy review, hash verification, staged rollout, and evidence.
- Ambiguous policy bundle state fails closed.

### Worker Runtime

- Changes worker execution behavior.
- Software install/update execution remains blocked in MVP.
- Future update requires approval, attestation posture, known-good version, and
  rollback evidence.

### Model Bundle

- Changes local model package or model route posture.
- Requires model hash ref, data-classification review, prompt-injection review,
  and rollback plan.
- External provider calls remain blocked.

### Config

- Changes runtime configuration, network refs, cache posture, or feature flags.
- Requires owner, diff summary, policy refs, and rollback ref.

## Staged Rollout

Planning sequence:

1. Review update record.
2. Verify hash/signature placeholder.
3. Select one canary worker in lab mode.
4. Observe heartbeat, evidence writer status, policy/model hash, and rollback
   posture.
5. Pause rollout on mismatch, degradation, evidence failure, or suspicious
   behavior.

No automatic rollout is authorized by this policy.

## Rollback Proof

Rollback proof must include:

- Known-good ref.
- Rollback reason.
- Operator approval refs where required.
- Health check evidence.
- Policy/model/runtime hash after rollback.
- Incident or evidence failure refs when applicable.

## Rollback Evidence

Rollback evidence must capture:

- Update record ID.
- Affected worker/deployment refs.
- Trigger reason.
- Previous and target refs.
- Guardian decision.
- Approval refs.
- Evidence refs.
- Completion or failure status.

## Update Failure Handling

Update failure causes:

- Pause rollout.
- Block new assignments where risk requires it.
- Quarantine worker when identity, capability, policy hash, model hash, evidence
  writer, or runtime integrity posture is suspect.
- Record incident/evidence refs.

## No Automatic High-Risk Update In MVP

- No automatic high-risk update.
- No software install/update execution.
- No endpoint control.
- No production touch.
- No remediation execution.
- No hidden background updater.

## Operator Approval Requirements

Operator or reviewer approval is required for:

- Worker runtime update.
- Model bundle change.
- Config change that alters access, network, cache, connector, or security
  posture.
- Rollback after failed or suspicious update.

## Acceptance Gates

- `governance.update_record` can represent update and rollback posture.
- `update.rollback` and `attestation.result.lineage` can represent rollback to
  attestation trust propagation linkage.
- Update/rollback runbook exists.
- Signed/verified source format is marked open.
- Known-good, rollback trigger, approval, evidence, and quarantine behavior are
  documented.
- Missing signature/hash/approval/evidence posture fails closed.
