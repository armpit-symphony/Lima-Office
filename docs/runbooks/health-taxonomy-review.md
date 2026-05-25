# Health Taxonomy Review

## Purpose

Review health-status and reason-code consistency across supervisor/worker/task/
Guardian/replay/evidence/model-route/governance metadata.

## When To Use

- Health status is `unknown`, `degraded`, `blocked`, or `blocked_mvp`.
- Console alerts and supervisor health summaries disagree.
- New health-domain reason codes are introduced.

## Review Areas

- supervisor health summaries
- worker lifecycle/heartbeat health posture
- model-route health posture
- Guardian/replay/evidence health posture
- governance retention/export-delete posture for health outcomes

## Review Steps

1. Confirm `health_domain`, `health_status`, and taxonomy version values.
2. Confirm reason codes are valid registry codes for the health context.
3. Confirm blocked/unknown/degraded paths include evidence refs.
4. Verify console alerts and supervisor health reason sets are consistent.
5. Verify blocked-MVP classes are explicitly represented as blocked.
6. Verify no raw customer content or secrets are present in health payloads.
7. If `model_route_privileged_requires_approval` appears, verify linked
   approval accountability records exist and requester/approver separation is
   represented.
8. If `retention_policy_missing` or `export_delete_policy_missing` appears,
   verify the outcome remains degraded/blocked with governance evidence refs and
   an explicit follow-up review owner.

## Reason-Code Checks

- Unknown codes => fail closed.
- Blocked codes in successful/completed contexts => fail closed.
- Deprecated codes require compatibility coverage.

## Evidence To Capture

- health record ID and alert ID
- related contract refs
- reason codes and taxonomy version
- policy refs and evidence refs
- approval accountability refs where required
- governance review owner/ref for retention or export/delete conflicts

## Escalation

- Security reviewer for taint, replay, or Guardian-policy conflicts.
- SRE/Field IT reviewer for stale/worker/degraded operational patterns.
- Compliance reviewer for evidence or taxonomy governance drift.

## Done Criteria

- Health domain/status taxonomy is consistent and machine-validated.
- Evidence coverage is complete for fail-closed outcomes.
- Required runbook and contract references are present.
