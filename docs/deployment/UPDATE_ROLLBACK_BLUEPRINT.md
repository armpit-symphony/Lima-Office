# Update Rollback Blueprint

## Purpose

Define the planning posture for Arc worker updates and rollbacks. This blueprint
does not install software, stage files, run updates, or implement rollback
automation.

This lane also adds metadata-only trust contracts:
`governance.update_record` and `update.rollback`, plus
[Signed Update Rollback Trust](../architecture/SIGNED_UPDATE_ROLLBACK_TRUST.md).
Attestation-result and appraisal linkage posture is further defined in
[ATTESTATION_VERIFIER_POLICY_REFERENCE_VALUES.md](../architecture/ATTESTATION_VERIFIER_POLICY_REFERENCE_VALUES.md).

## Update Channels

### Policy Bundle

Policy bundle changes affect Guardian routing, tool-pack scope, evidence
requirements, and blocked action behavior. They require hash refs, operator
visibility, and evidence.

### Worker Runtime

Worker runtime updates are future implementation work. Software install/update
execution requires approval and remains blocked by this blueprint.

### Model Bundle

Model bundle changes affect local model availability and cache/storage posture.
They require model bundle refs, policy checks, and data-classification review.
External provider credentials are not part of model bundle records.

### Config

Config changes use refs and placeholders only. Config must not contain API keys,
OAuth codes, passwords, cookies, bearer tokens, signatures, or private keys.

## Signed Update Expectation

Future update execution must require signed or otherwise verified update source.
Until that gate exists, updates are planning records only.

## Staged Rollout

Recommended future rollout shape:

1. Stage on one lab worker.
2. Validate heartbeat, policy refs, model refs, evidence writer status, and
   rollback state.
3. Keep other workers on known-good refs.
4. Expand only after operator review and evidence capture.

## Rollback Trigger

Rollback should be triggered by:

- Failed update verification.
- Worker heartbeat degradation after update.
- Evidence writer failure.
- Capability manifest mismatch.
- Policy/model hash mismatch.
- Operator or Guardian containment.

## Rollback Evidence

Rollback records should include:

- Worker ID.
- Deployment ID.
- Previous known-good refs.
- Failed update ref.
- Guardian decision ID.
- Operator approval/refusal where required.
- Evidence refs.
- Result state.

## Blocked Automatic Update Behavior

Automatic update execution is blocked for MVP. Workers must not self-update,
install packages, fetch unreviewed model bundles, or alter config without
approval, Guardian decision, and evidence.

## MVP Acceptance Gates

- Update channels are documented as refs.
- Known-good rollback refs are recorded.
- Failed update paths quarantine or degrade rather than continue silently.
- Evidence refs exist for update planning, failure, rollback, and release.
- No update automation is implemented.
