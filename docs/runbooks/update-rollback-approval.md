# Update Rollback Approval Runbook

## Purpose

Review update and rollback requests for policy bundles, worker runtime, model
bundles, and config without implementing update automation.

## When To Use

- Policy bundle update is proposed.
- Worker runtime update is proposed.
- Model bundle update is proposed.
- Config change affects access, network, cache, connector, or security posture.
- Rollback is required after failed or suspicious update review.

## Prerequisites

- [Signed Update Rollback Policy](../governance/SIGNED_UPDATE_ROLLBACK_POLICY.md)
- [Update Rollback Blueprint](../deployment/UPDATE_ROLLBACK_BLUEPRINT.md)
- `governance.update_record` record.
- Worker deployment/lifecycle records when workers are affected.

## Steps

1. Confirm update type and target refs.
2. Confirm source ref, version ref, and hash ref.
3. Check signature or verification placeholder.
4. Confirm automatic update is false.
5. Confirm canary/staged rollout posture.
6. Confirm known-good rollback ref.
7. Confirm approval requester and approver separation.
8. Record rollback trigger and evidence when rollback is required.
9. Pause rollout or quarantine affected worker on failed verification,
   attestation failure, evidence failure, or health degradation.

## Approval Requirements

- Worker runtime update requires operator and field IT review.
- Model bundle update requires security review before model runtime expansion.
- Config changes affecting access, network, cache, connector, or security
  posture require independent approval.
- Rollback after failed or suspicious review requires evidence and reviewer
  approval.

## Evidence To Capture

- Update record ID.
- Source, version, hash, and verification refs.
- Target worker/deployment refs.
- Approval request/result refs.
- Known-good rollback ref.
- Rollback reason and evidence refs.
- Quarantine or incident refs when applicable.

## Rollback / Containment

- Pause rollout.
- Mark rollback required.
- Quarantine affected worker when identity, policy, model, evidence, or health
  posture is suspect.
- Keep software install/update execution blocked until future approval.

## Escalation

Escalate to security reviewer for failed verification, attestation failure, or
suspected supply-chain risk. Escalate to field IT reviewer for failed staged
rollout, OS, hardware, or network readiness issues.

## Done Criteria

- Update record has status, evidence, and reviewer refs.
- Automatic update remains disabled.
- Rollback posture is documented.
- No software install/update execution is implied.
