# Health Status Taxonomy

## Purpose

Define a consistent health-status vocabulary across supervisor, workers, tasks,
Guardian, approval, replay, transaction, evidence, model-route, connector,
governance, LIMA IT, and console metadata.

Status: taxonomy scaffolding for contracts/tests/docs only.

## Naming Conventions

- Reason codes use lower_snake_case.
- Health status values are normalized and fail closed on unknown values.
- Reason semantics align with the reason-code registry and taxonomy versioning.

## Canonical Health Status Values

- `healthy`
- `degraded`
- `blocked`
- `unknown`
- `blocked_mvp`

## Health Domains

- `supervisor`
- `worker`
- `task`
- `guardian`
- `approval`
- `evidence`
- `replay`
- `transaction`
- `model_route`
- `connector`
- `governance`
- `lima_it`
- `console`

## Canonical Model-Route / Health Reason Codes

- `model_route_unavailable`
- `model_route_blocked_mvp`
- `model_route_tainted_input_denied`
- `model_route_privileged_requires_approval`
- `model_route_provider_blocked_mvp`
- `model_route_local_execution_blocked_mvp`
- `model_route_rbac_blocked`
- `model_route_device_untrusted`
- `model_route_fallback_denied`
- `attestation_required`
- `attestation_failed`
- `attestation_expired`
- `trust_root_unknown`
- `trust_root_failed`
- `update_signature_missing`
- `update_signature_invalid`
- `update_provenance_missing`
- `update_rollback_required`
- `update_blocked_mvp`
- `model_bundle_untrusted`
- `policy_bundle_untrusted`
- `runtime_bundle_untrusted`
- `reference_value_missing`
- `reference_value_stale`
- `reference_value_revoked`
- `endorsement_missing`
- `endorsement_revoked`
- `endorsement_expired`
- `appraisal_policy_missing`
- `appraisal_policy_revoked`
- `appraisal_failed`
- `appraisal_inconclusive`
- `attestation_result_expired`
- `attestation_quarantine_required`
- `attestation_reference_mismatch`
- `attestation_lineage_stale`
- `attestation_lineage_revoked`
- `attestation_lineage_conflicted`
- `attestation_result_trust_conflict`
- `revocation_propagation_pending`
- `revocation_propagation_failed`
- `verifier_authority_missing`
- `verifier_authority_revoked`
- `reference_authority_missing`
- `endorsement_authority_missing`
- `quarantine_clearance_sod_required`
- `health_unknown`
- `health_degraded`
- `health_blocked`

## Domain-Family Expectations

- `model_route` domain should primarily use `health`, `guardian`,
  `blocked_mvp`, and `governance` reason families.
- `worker/supervisor` domain should primarily use `health`, `evidence`,
  `guardian`, and `transaction` families.
- Cross-cutting `tenant_isolation` and `blocked_mvp` codes are allowed only for
  explicit blocked/degraded/unknown outcomes.

## Operator Visibility

- Operator-visible alerts must include domain, status, reason code, severity,
  and runbook reference.
- Internal-only details can remain in evidence refs and linked records.

## Evidence Requirements

- `blocked`, `blocked_mvp`, and fail-closed `degraded` outcomes require evidence
  references.
- `unknown` health states require evidence or explicit evidence-failure refs.

## Alert Mapping

- `healthy` => informational/no active block
- `degraded` => warning/high (review required)
- `blocked` and `blocked_mvp` => blocked/high (action prevented)
- `unknown` => fail-closed review-required

## Non-Goals

- No production monitoring implementation.
- No telemetry backend implementation.
- No runtime authorization decisions.
