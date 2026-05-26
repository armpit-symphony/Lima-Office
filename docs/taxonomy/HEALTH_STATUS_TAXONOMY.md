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
- `connector_consent_missing`
- `connector_scope_overbroad`
- `connector_scope_denied`
- `connector_revoked`
- `connector_revocation_missing`
- `connector_object_auth_missing`
- `connector_property_auth_missing`
- `connector_outbound_action_blocked`
- `connector_live_blocked_mvp`
- `connector_prompt_injection_risk`
- `connector_rate_limit_missing`
- `connector_secret_policy_missing`
- `connector_export_delete_impact_unknown`
- `connector_provider_high_risk`
- `connector_provider_critical_risk`
- `connector_disable_switch_missing`
- `connector_disable_switch_failed`
- `connector_revocation_unverified`
- `connector_revocation_drill_failed`
- `connector_token_rotation_missing`
- `connector_outbound_capability_blocked`
- `connector_prompt_injection_blocked`
- `connector_cross_tenant_blocked`
- `connector_reconciliation_drift`
- `consent_revoked_but_ready`
- `scope_overbroad_but_invocation_requested`
- `provider_critical_but_ready`
- `revocation_drill_failed_but_enabled`
- `disable_switch_missing_but_ready`
- `outbound_missing_approval`
- `tainted_connector_payload_blocked`
- `connector_cross_tenant_linkage`
- `connector_evidence_missing`
- `connector_trust_revoked_but_allowed`
- `connector_score_below_threshold`
- `connector_score_failed_closed`
- `connector_score_degraded`
- `connector_slo_missed`
- `connector_slo_stale`
- `connector_reconciliation_stale`
- `connector_revocation_propagation_pending`
- `connector_revocation_propagation_missed`
- `connector_disable_verification_missed`
- `connector_source_of_truth_missing`
- `connector_source_of_truth_conflict`
- `connector_owner_missing`
- `connector_owner_stale`
- `connector_owner_conflict`
- `connector_sod_violation`
- `connector_escalation_overdue`
- `connector_revocation_owner_missing`
- `connector_disable_owner_missing`
- `connector_accountability_failed_closed`
- `connector_acceptance_blocked_mvp`
- `connector_defaults_missing`
- `connector_defaults_stale`
- `connector_defaults_override_review_required`
- `connector_slo_target_missing`
- `connector_slo_target_missed`
- `connector_score_threshold_missing`
- `connector_score_threshold_stale`
- `connector_threshold_blocked_mvp`
- `connector_default_outbound_blocked`
- `connector_provider_category_blocked_mvp`
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
- `attestation_reconciliation_drift`
- `attestation_revocation_pending`
- `attestation_revocation_not_propagated`
- `attestation_quarantine_mismatch`
- `attestation_cross_tenant_linkage`
- `verifier_authority_conflict`
- `appraisal_policy_revoked_but_active`
- `trusted_result_with_revoked_endorsement`
- `trusted_result_with_revoked_reference`
- `model_route_selected_with_untrusted_lineage`
- `transaction_committed_with_revoked_attestation`
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
