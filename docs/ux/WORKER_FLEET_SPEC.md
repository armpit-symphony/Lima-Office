# Worker Fleet Spec

The worker fleet view shows Arc worker mini PC state for 1 Supervisor Server
and 1-8 Arc workers. It does not implement worker control.

## Worker Inventory

Inventory table columns:

- Worker ID.
- Deployment ID.
- Role.
- Hardware class.
- OS family/version ref.
- Location/asset refs.
- Support owner.
- Field IT reviewer.
- Security reviewer.
- Latest evidence ref.

## Lifecycle And Deployment State

Show:

- `provisioned`.
- `enrolled`.
- `active`.
- `degraded`.
- `quarantined`.
- `revoked`.
- `reenrollment_pending`.
- `retired`.

Deployment state must link to `worker.deployment`.

## Role And Capabilities

Show worker role, capability manifest version/hash, tool-pack scope version,
local model status, and model bundle hash ref when present.

## Heartbeat Age

Show latest heartbeat sequence, age, missed count, boot ID, supervisor receive
time, Guardian reachability, evidence writer status, and network posture.

## Policy And Model Hash

Display policy bundle ref/hash and model bundle ref/hash. Hash mismatch shows
blocked or quarantine review state.

## Attestation Placeholder

Show attestation status:

- `not_required_phase0`.
- `manual_review_only`.
- `pending`.
- `verified_placeholder`.
- `failed`.
- `expired`.
- `revoked`.
- `blocked_mvp`.

Also show trust-root posture metadata (`trust_root_status`) and
`worker_attestation_ref`.

Attestation absence is weak lab trust only and cannot permit automated
re-enrollment or privileged work.

## Update Status

Show update version, rollback version, update status, rollback required state,
known-good ref, and [Update Rollback Approval](../runbooks/update-rollback-approval.md).
When present, show `update_rollback_ref` and reason-code metadata.

## Quarantine/Revoke Controls

Spec-only controls:

- Request quarantine.
- Request revoke.
- Open incident.
- Open evidence.

Controls require Guardian decision, policy refs, evidence, and allowed role.

## Re-Enrollment Controls

Spec-only controls:

- Request re-enrollment review.
- Attach field checklist refs.
- Attach cache purge refs.
- Attach identity/capability/policy hash review refs.

Automated re-enrollment remains blocked.

## Field IT Checklist Links

Each worker detail links to:

- [Worker deployment](../runbooks/worker-deployment.md)
- [Field IT preflight](../runbooks/field-it-preflight.md)
- [Worker quarantine](../runbooks/worker-quarantine.md)
- [Worker re-enrollment](../runbooks/worker-reenrollment.md)
- [Worker attestation failure](../runbooks/worker-attestation-failure.md)
- [Worker attestation review](../runbooks/worker-attestation-review.md)
- [Signed update rollback review](../runbooks/signed-update-rollback-review.md)
