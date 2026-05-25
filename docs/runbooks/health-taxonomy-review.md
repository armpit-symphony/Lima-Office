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

## Review Steps

1. Confirm `health_domain`, `health_status`, and taxonomy version values.
2. Confirm reason codes are valid registry codes for the health context.
3. Confirm blocked/unknown/degraded paths include evidence refs.
4. Verify console alerts and supervisor health reason sets are consistent.
5. Verify blocked-MVP classes are explicitly represented as blocked.
6. Verify no raw customer content or secrets are present in health payloads.

## Reason-Code Checks

- Unknown codes => fail closed.
- Blocked codes in successful/completed contexts => fail closed.
- Deprecated codes require compatibility coverage.

## Evidence To Capture

- health record ID and alert ID
- related contract refs
- reason codes and taxonomy version
- policy refs and evidence refs

## Escalation

- Security reviewer for taint, replay, or Guardian-policy conflicts.
- SRE/Field IT reviewer for stale/worker/degraded operational patterns.
- Compliance reviewer for evidence or taxonomy governance drift.

## Done Criteria

- Health domain/status taxonomy is consistent and machine-validated.
- Evidence coverage is complete for fail-closed outcomes.
- Required runbook and contract references are present.
