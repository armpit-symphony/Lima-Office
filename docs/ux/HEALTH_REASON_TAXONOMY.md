# Health Reason Taxonomy

This is initial taxonomy scaffolding for console status and alert labels. It is
not production monitoring, an alerting service, or production runtime
implementation. Phase 1A v2 uses these codes in metadata-only
`supervisor.health` mock reports.

| Reason code | Category | Meaning | Expected UX state | Primary records | Runbook |
| --- | --- | --- | --- | --- | --- |
| `worker_stale` | Worker | Heartbeat age or missed heartbeat count exceeded planning threshold | High alert, task assignment blocked or review-required | `worker.heartbeat`, `worker.lifecycle`, `console.alert` | [Health checks](../runbooks/health-checks.md) |
| `worker_quarantined` | Worker | Worker is quarantined by Guardian/operator/security review | Blocked for new assignments | `worker.lifecycle`, `incident.ops`, `console.action` | [Worker quarantine](../runbooks/worker-quarantine.md) |
| `worker_revoked` | Worker | Worker identity or lease is revoked | Blocked and terminal until replacement | `worker.lifecycle`, `worker.deployment` | [Worker re-enrollment](../runbooks/worker-reenrollment.md) |
| `evidence_missing` | Evidence | Required evidence ref is absent | Blocked for privileged action | `evidence.failure`, `task.execution`, `console.alert` | [Evidence writer failure](../runbooks/evidence-writer-failure.md) |
| `evidence_writer_degraded` | Evidence | Evidence writer degraded or failed | High alert; pre-action privileged work blocked when evidence is required | `evidence.failure`, `worker.heartbeat` | [Evidence writer failure](../runbooks/evidence-writer-failure.md) |
| `guardian_denied` | Guardian | Guardian decision is deny, block-MVP, or quarantine | Blocked | `guardian.decision` | [Approval flow](../runbooks/approval-flow.md) |
| `guardian_decision_expired` | Guardian | Guardian decision expired before use | Blocked; new decision required | `guardian.decision`, `guardian.replay` | [Approval token lifecycle](../runbooks/approval-token-lifecycle.md) |
| `guardian_decision_stale` | Guardian | Guardian decision exceeded max age or clock-skew window | Blocked; triage queue and worker clock posture | `guardian.decision`, `guardian.replay`, `worker.heartbeat` | [Health checks](../runbooks/health-checks.md) |
| `guardian_replay_denied` | Guardian | One-time Guardian decision nonce was reused or replay status is non-authorizing | Blocked; review for incident threshold | `guardian.replay`, `incident.ops` | [Security incident](../runbooks/security-incident.md) |
| `approval_expired` | Approval | Approval request or token expired | Blocked; new request required | `approval.request`, `approval.token`, `token.verification` | [Approval token lifecycle](../runbooks/approval-token-lifecycle.md) |
| `approval_revoked` | Approval | Approval token or decision authority revoked | Blocked | `approval.token`, `token.verification` | [Approval token lifecycle](../runbooks/approval-token-lifecycle.md) |
| `token_mismatch` | Approval | Token verification fails scope, task, tenant, resource, or action binding | Blocked | `token.verification`, `approval.token` | [Approval token lifecycle](../runbooks/approval-token-lifecycle.md) |
| `tainted_input` | Guardian | Prompt-injection or untrusted input detected | Warning/high; privileged actions blocked or require review | `taint.ref`, `guardian.decision` | [Prompt injection response](../runbooks/prompt-injection-response.md) |
| `connector_revoked` | Connector | Connector consent/trust state revoked | Blocked for connector use | `connector.trust`, `governance.connector_consent` | [Connector revocation](../runbooks/connector-revocation.md) |
| `connector_consent_missing` | Connector | Connector readiness record lacks valid consent linkage | Blocked/fail-closed | `connector.readiness`, `governance.connector_consent` | [Live connector readiness review](../runbooks/live-connector-readiness-review.md) |
| `connector_scope_overbroad` | Connector | Requested connector scope exceeds least-privilege policy | Blocked/review-required | `connector.scope_review`, `connector.readiness` | [Live connector readiness review](../runbooks/live-connector-readiness-review.md) |
| `connector_object_auth_missing` | Connector | Object-level authorization mapping is missing or failed-closed | Blocked/fail-closed | `connector.scope_review`, `connector.readiness` | [Live connector readiness review](../runbooks/live-connector-readiness-review.md) |
| `connector_property_auth_missing` | Connector | Property-level authorization mapping is missing or failed-closed | Blocked/fail-closed | `connector.scope_review`, `connector.readiness` | [Live connector readiness review](../runbooks/live-connector-readiness-review.md) |
| `connector_live_blocked_mvp` | Connector | Connector type/action remains blocked for MVP live execution | Blocked-MVP | `connector.readiness`, `console.alert` | [Live connector readiness review](../runbooks/live-connector-readiness-review.md) |
| `attestation_failed` | Worker/deployment | Worker attestation, identity, policy hash, or model hash failed | High alert; quarantine/re-enrollment review | `worker.deployment`, `worker.lifecycle`, `governance.update_record` | [Worker attestation failure](../runbooks/worker-attestation-failure.md) |
| `attestation_expired` | Worker/deployment | Attestation freshness window expired | Blocked/review-required | `worker.attestation`, `worker.heartbeat`, `governance.device_trust` | [Worker attestation review](../runbooks/worker-attestation-review.md) |
| `trust_root_unknown` | Worker/deployment | Trust-root provenance is unknown or unresolved placeholder | Degraded/blocked review | `worker.attestation`, `worker.deployment` | [Worker attestation review](../runbooks/worker-attestation-review.md) |
| `trust_root_failed` | Worker/deployment | Trust-root posture failed appraisal | Blocked | `worker.attestation`, `worker.lifecycle`, `console.alert` | [Worker attestation review](../runbooks/worker-attestation-review.md) |
| `reference_value_missing` | Attestation/appraisal | Required reference value metadata is missing for appraisal | Blocked | `attestation.reference_value`, `attestation.appraisal_policy`, `attestation.result` | [Attestation verifier review](../runbooks/attestation-verifier-review.md) |
| `reference_value_stale` | Attestation/appraisal | Reference value metadata is present but stale/expired for policy window | Blocked | `attestation.reference_value`, `attestation.result` | [Attestation verifier review](../runbooks/attestation-verifier-review.md) |
| `reference_value_revoked` | Attestation/appraisal | Reference value lifecycle is revoked and cannot be trusted | Blocked | `attestation.reference_value`, `attestation.result` | [Attestation verifier review](../runbooks/attestation-verifier-review.md) |
| `endorsement_missing` | Attestation/appraisal | Required endorsement metadata is missing | Blocked | `attestation.endorsement`, `attestation.appraisal_policy`, `attestation.result` | [Attestation verifier review](../runbooks/attestation-verifier-review.md) |
| `endorsement_revoked` | Attestation/appraisal | Endorsement metadata is revoked and cannot be trusted | Blocked | `attestation.endorsement`, `attestation.result` | [Attestation verifier review](../runbooks/attestation-verifier-review.md) |
| `endorsement_expired` | Attestation/appraisal | Endorsement validity window expired | Blocked/degraded | `attestation.endorsement`, `attestation.result` | [Attestation verifier review](../runbooks/attestation-verifier-review.md) |
| `appraisal_policy_missing` | Attestation/appraisal | No active appraisal policy metadata is available for worker/action scope | Blocked | `attestation.appraisal_policy`, `attestation.result` | [Attestation verifier review](../runbooks/attestation-verifier-review.md) |
| `appraisal_policy_revoked` | Attestation/appraisal | Appraisal policy is revoked/deprecated for this scope | Blocked | `attestation.appraisal_policy`, `attestation.result` | [Attestation verifier review](../runbooks/attestation-verifier-review.md) |
| `appraisal_failed` | Attestation/appraisal | Attestation appraisal failed policy checks | Blocked/quarantine-required | `attestation.result`, `worker.lifecycle`, `console.alert` | [Attestation verifier review](../runbooks/attestation-verifier-review.md) |
| `appraisal_inconclusive` | Attestation/appraisal | Appraisal could not conclude pass/fail with required metadata | Degraded/blocked review | `attestation.result`, `supervisor.health` | [Attestation verifier review](../runbooks/attestation-verifier-review.md) |
| `attestation_result_expired` | Attestation/appraisal | Attestation result freshness/expiry window elapsed | Blocked/review-required | `attestation.result`, `worker.heartbeat`, `model.route` | [Attestation verifier review](../runbooks/attestation-verifier-review.md) |
| `attestation_quarantine_required` | Attestation/appraisal | Appraisal outcome requires quarantine before privileged work | Blocked/quarantined | `attestation.result`, `worker.lifecycle`, `incident.ops` | [Worker quarantine](../runbooks/worker-quarantine.md) |
| `attestation_reference_mismatch` | Attestation/appraisal | Worker evidence hash and approved reference value differ | Blocked | `attestation.result`, `worker.attestation`, `worker.deployment` | [Attestation verifier review](../runbooks/attestation-verifier-review.md) |
| `update_rollback_required` | Deployment/update | Update review requires rollback or pause | High alert; no automatic update | `governance.update_record`, `worker.heartbeat` | [Update rollback approval](../runbooks/update-rollback-approval.md) |
| `update_signature_missing` | Deployment/update | Required signing metadata missing | Blocked | `update.rollback`, `governance.update_record` | [Signed update rollback review](../runbooks/signed-update-rollback-review.md) |
| `update_signature_invalid` | Deployment/update | Signing metadata appraisal failed | Blocked | `update.rollback`, `governance.update_record` | [Signed update rollback review](../runbooks/signed-update-rollback-review.md) |
| `update_provenance_missing` | Deployment/update | Provenance metadata missing for update record | Blocked | `update.rollback`, `governance.update_record` | [Signed update rollback review](../runbooks/signed-update-rollback-review.md) |
| `update_blocked_mvp` | Deployment/update | Update execution path remains blocked in MVP | Blocked-MVP | `update.rollback`, `governance.update_record` | [Signed update rollback review](../runbooks/signed-update-rollback-review.md) |
| `model_bundle_untrusted` | Model route/update | Model bundle trust check failed or unresolved | Blocked | `update.rollback`, `model.route`, `console.alert` | [Model routing review](../runbooks/model-routing-review.md) |
| `policy_bundle_untrusted` | Model route/update | Policy bundle trust check failed or unresolved | Blocked | `update.rollback`, `model.route`, `console.alert` | [Signed update rollback review](../runbooks/signed-update-rollback-review.md) |
| `runtime_bundle_untrusted` | Model route/update | Runtime bundle trust check failed or unresolved | Blocked | `update.rollback`, `model.route`, `worker.heartbeat` | [Signed update rollback review](../runbooks/signed-update-rollback-review.md) |
| `lima_it_remediation_blocked` | LIMA IT | Remediation request is blocked or non-executing metadata only | Blocked-MVP label | `lima_it.handoff`, `approval.result` | [LIMA IT handoff](../runbooks/lima-it-handoff.md) |
| `retention_policy_missing` | Governance/data | Retention posture missing for record or action | Blocked for durable write/export/delete | `governance.audit_export`, `evidence.artifact`, `memory.access` | [Customer exit delete](../runbooks/customer-exit-delete.md) |
| `export_delete_policy_missing` | Governance/data | Export/delete posture missing or preservation conflict unresolved | Blocked for export/delete | `governance.audit_export` | [Customer exit delete](../runbooks/customer-exit-delete.md) |
| `idp_mfa_missing` | Governance/identity | Identity provider or MFA posture missing for privileged role | Blocked for approval-capable view | `governance.identity`, `governance.access_review` | [Access review](../runbooks/access-review.md) |
| `task_blocked` | Task | Task is blocked, denied, or evidence-unavailable after policy/invariant review | Blocked | `task.execution`, `supervisor.health` | [Approval flow](../runbooks/approval-flow.md) |
| `model_route_unavailable` | Model route | Route classification cannot select safe planned path | High/block review | `model.route`, `supervisor.health`, `console.alert` | [Model routing review](../runbooks/model-routing-review.md) |
| `model_route_blocked_mvp` | Model route | Route path is blocked by MVP boundary | Blocked-MVP | `model.route`, `console.alert` | [Model routing review](../runbooks/model-routing-review.md) |
| `model_route_tainted_input_denied` | Model route/Guardian | Tainted privileged input denied for route classification | Blocked | `model.route`, `guardian.decision` | [Model routing review](../runbooks/model-routing-review.md) |
| `model_route_privileged_requires_approval` | Model route/Governance | High-risk route requires approval posture or denial | Blocked/review-required | `model.route`, `task.execution` | [Model routing review](../runbooks/model-routing-review.md) |
| `model_route_provider_blocked_mvp` | Model route | Subscription/provider path blocked in MVP | Blocked-MVP | `model.route`, `console.alert` | [Model routing review](../runbooks/model-routing-review.md) |
| `model_route_local_execution_blocked_mvp` | Model route | Local inference execution remains blocked in MVP | Blocked-MVP | `model.route`, `console.alert` | [Model routing review](../runbooks/model-routing-review.md) |
| `model_route_rbac_blocked` | Model route/Governance | RBAC posture blocks privileged route | Blocked | `model.route`, `governance.rbac_matrix` | [RBAC IdP MFA access review](../runbooks/rbac-idp-mfa-access-review.md) |
| `model_route_device_untrusted` | Model route/Governance | Device trust posture blocks privileged route | Blocked | `model.route`, `governance.device_trust` | [RBAC IdP MFA access review](../runbooks/rbac-idp-mfa-access-review.md) |
| `model_route_fallback_denied` | Model route | Fallback policy denies secondary path | Blocked | `model.route`, `console.alert` | [Model routing review](../runbooks/model-routing-review.md) |
| `health_unknown` | Health | Health domain cannot be classified safely | Review-required | `supervisor.health`, `console.alert` | [Health taxonomy review](../runbooks/health-taxonomy-review.md) |
| `health_degraded` | Health | Domain is operating in degraded but observable mode | Warning/high | `supervisor.health`, `worker.heartbeat` | [Health taxonomy review](../runbooks/health-taxonomy-review.md) |
| `health_blocked` | Health | Domain is fail-closed blocked | Blocked | `supervisor.health`, `console.alert` | [Health taxonomy review](../runbooks/health-taxonomy-review.md) |

## Connector Provider-Risk Additions

The connector provider-risk lane adds these fail-closed connector codes:

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

Primary records: `connector.provider_profile`, `connector.revocation_drill`,
`connector.readiness`, `connector.scope_review`, `console.alert`,
`supervisor.health`. Runbook:
[Connector revocation disable drill](../runbooks/connector-revocation-disable-drill.md).

## UX Rules

- Missing data is not healthy.
- Blocked-MVP states cannot be converted to approval-capable states by the
  console.
- Every reason code must map to a runbook and evidence or evidence-failure ref.
- Future runtime must treat unknown reason codes as review-required or blocked.
- Health/status reason arrays serialized in contracts/examples must include
  `taxonomy_version`; missing or unsupported taxonomy versions fail closed.
- Governance/export/delete reason-code alignment is defined in
  [Reconciliation Reason Taxonomy](../taxonomy/RECONCILIATION_REASON_TAXONOMY.md)
  and [Evidence Reason Taxonomy](../taxonomy/EVIDENCE_REASON_TAXONOMY.md).
- Registry versioning/deprecation/alias handling is defined in
  [Reason Code Registry](../taxonomy/REASON_CODE_REGISTRY.md) and
  [Reason Code Compatibility Policy](../taxonomy/REASON_CODE_COMPATIBILITY_POLICY.md).

## Attestation Lineage Additions

The attestation-lineage authority lane adds these health/alert codes:

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

These remain metadata-only, fail-closed governance signals. They do not
authorize runtime actions.

Attestation revocation reconciliation drills add:

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

These codes are metadata-only fail-closed reconciliation signals and do not
authorize runtime action.
