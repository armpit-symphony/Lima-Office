# Contracts

These are Phase 0 planning contracts. They are field-level schemas and examples only; they do not authorize runtime services, live connector access, customer-system mutation, external sends, or production operation.

The schema source of truth is [contracts/README.md](../contracts/README.md) and [contracts/v1](../contracts/v1). Example JSON objects are in [contracts/examples](../contracts/examples).

Phase 0 policies are pre-runtime requirements and are indexed in [docs/policies/README.md](policies/README.md). A contract record is not enough to authorize runtime behavior; Guardian must also link the relevant policy refs, approval state, and evidence.

## Contract Rules

- Every contract includes tenant scope through `tenant_id` and `customer_context_id`.
- Every contract includes a common envelope: `contract_name`, `contract_version`, `schema_version`, `environment`, `correlation_id`, `causation_id`, `idempotency_key`, `producer`, `policy_version`, timestamps, Guardian linkage where applicable, and evidence linkage.
- Automatic means no human approval is required; it does not bypass Guardian.
- Approval-required actions need an `approval.request`, an approved
  `approval.result`, a scoped one-time `approval.token`, a valid
  `token.verification`, and a normalized `approval.binding` before any
  mock/dry-run path can proceed.
- Approval tokens are references and metadata only. They must never contain bearer token material, PINs, OAuth codes, API keys, signatures, or plaintext secrets.
- Evidence is required for allow, deny, approval, failure, quarantine, revoke, incident, connector readiness, memory access, model route, tool invocation, and LIMA IT handoff events.
- Denied, blocked, failed, expired, revoked, and quarantined states are first-class outcomes.
- Examples are sanitized and use opaque refs instead of real customer names, file paths, email addresses, URLs with secrets, raw prompts, raw tool output, connector payloads, or secret values.

## Common Compatibility Rules

- `contract_version` follows semantic versioning. Version `1.0.0` is the Phase 0 baseline.
- Additive optional fields may be introduced in a minor version if old consumers can ignore them.
- Required field changes, enum removals, renamed fields, or state semantic changes require a major version.
- Phase 1A may tighten v1 mock-only schemas before any production consumer
  exists, but those changes still require updated examples, tests, and docs.
  This does not authorize production consumers or live runtime behavior.
- New producers must not emit a contract version unless the relevant schema and example are present.
- Runtime implementation remains blocked until the specific contract it needs is present, reviewed, and mapped to Guardian, approval, and evidence behavior.
- Runtime implementation also remains blocked when the relevant policy or operator runbook is missing or ambiguous.

## Conditional Validity Notes

Version 1 schemas now use JSON Schema draft 2020-12 conditionals for the highest-risk cross-field rules. These rules are contract guardrails, not runtime implementation:

- Denied, blocked-MVP, failed, expired, revoked, quarantined, and evidence-failure states require matching reason, evidence, or failure fields.
- Approved approval requests/results require approver identity, decision time, narrowed scope, token linkage, and evidence.
- Blocked-MVP actions cannot issue approval tokens.
- Token verification and approval binding must fail closed for missing,
  expired, revoked, used, replayed, mismatched, tainted, blocked-MVP,
  ambiguous, wrong-scope, or wider-than-approved tokens and actions.
- Replay-store and replay-artifact metadata must fail closed for replay denial,
  failed-closed atomicity, tenant/action/scope mismatch, or missing denial
  evidence refs where evidence is required.
- Cross-contract linkage fields must fail closed on missing refs, tenant
  mismatch, scope mismatch, nonce mismatch, or reconciliation drift.
- Approval/Guardian reconciliation fields (`reconciliation_status`,
  `reconciliation_failure_reasons`, canonical approval/Guardian IDs, and
  reconciliation evidence refs) must fail closed on missing/mismatched/stale/
  replay/coordinator/evidence/cross-tenant/blocked-MVP outcomes.
- Transaction boundaries must fail closed for ambiguous commit/rollback state,
  missing failure reason on failed-closed status, or missing evidence refs for
  failed-closed transitions.
- Transaction coordinator events must fail closed for invalid transition order,
  duplicate tenant-scoped idempotency keys, missing replay/evidence refs on
  replay/evidence/reconciliation stages, or terminal-state mismatch.
- Evidence ledger entries must remain append-only metadata with chain linkage,
  hash fields, and explicit raw/secret exclusion.
- Evidence-required task/tool paths cannot be represented as completed when evidence failure blocks the action.
- Evidence export manifests must remain refs-only, with redaction/retention
  placeholders and explicit delete-conflict refs for denied/blocked states.
- Reason-bearing contracts now require `taxonomy_version` so reconciliation/
  evidence/conflict semantics remain versioned and fail closed for unknown or
  unsupported taxonomy versions.
- Tainted content must remain data-only unless a later policy review clears it; it cannot directly become tool args, durable memory, approval scope, external sends, or remediation.
- LIMA IT remediation is non-executing in Phase 0; diagnostic handoff remains read-only.

## Cross-Contract Invariant Checkpoint

[Cross-Contract Invariants](CROSS_CONTRACT_INVARIANTS.md) defines the Phase 1A
v2 checkpoint that supersedes the absent `e714310...` invariant branch. The
checkpoint verifies that individually valid records cannot be combined into
unsafe runtime flows.

The runtime invariant checks cover:

- Guardian decision binding to tenant, customer context, task, evidence, and
  reference-time freshness.
- Approval-required task binding to valid token verification for the same
  tenant, customer context, task, approval request, approval token, and Guardian
  decision.
- Approval-required mock task/tool binding to `approval.binding` for the same
  tenant, customer context, task, approval chain, binding, approval result,
  approval token, token verification, Guardian decision, worker where
  applicable, policy snapshot, scope hash, and evidence refs.
- Evidence-required task completion with evidence refs validated by the
  in-memory evidence writer when attached.
- Worker routing that blocks quarantined, revoked, offline, wrong-tenant, stale,
  and capability-mismatched workers.
- Tool, memory, helper, and LIMA IT records that fail closed on taint,
  cross-tenant access, blocked-MVP approval results, remediation execution, or
  helper scope overreach.

These checks remain Phase 1A hardening. They do not add live connectors,
external sends, model calls, remediation, durable persistence, UI, or production
monitoring.

Approval/Guardian reconciliation drill requirements are defined in
[Approval Guardian Reconciliation Drills](APPROVAL_GUARDIAN_RECONCILIATION_DRILLS.md).

## Model Routing Defaults Refinement

Phase 1A now hardens `model.route` for metadata-only routing posture:

- required `taxonomy_version` and route policy versioning;
- explicit `route_mode` (`mock_only`, `local_planned`,
  `subscription_planned`, `blocked_mvp`) and `route_status`
  (`selected`, `degraded`, `denied`, `blocked_mvp`, `unavailable`);
- required route/fallback reason-code arrays bound to taxonomy registry values;
- explicit RBAC/session/device trust references for privileged-path review;
- explicit placeholder-only `provider_ref` and `local_model_bundle_ref` with
  no live provider call and no local inference execution allowed;
- fail-closed conditionals for high-risk approval requirements, tainted
  privileged routes, and blocked-MVP route selection.

This remains docs/contracts/tests/mock-only hardening and does not authorize
provider integration, local inference runtime, or runtime authorization.

## Worker Attestation / Signed Update Rollback Hardening

Phase 1A now adds metadata-only trust posture contracts for worker attestation
and signed update/rollback review:

- `worker.attestation` for attestation status, trust-root placeholder status,
  hash-manifest refs, appraisal-policy refs, and fail-closed reason/evidence
  linkage.
- `update.rollback` for artifact hash/signer/key/provenance refs, update and
  rollback status transitions, model-bundle blocked-MVP posture, and fail-closed
  verification/rollback reason-code linkage.

Related schemas now include stronger trust-aware metadata bindings:

- `worker.deployment` includes trust-root status and attestation linkage refs.
- `worker.heartbeat` includes attestation/update trust drift posture fields.
- `model.route` includes attestation/update refs and blocked trust reason-code
  constraints for privileged routes.

These are design-only metadata controls. No TPM integration, no signing
service, no update runtime, and no rollback automation are implemented.

## Attestation Verifier / Reference-Value Governance Hardening

Phase 1A now adds design-only verifier-governance contracts for appraisal
policy and reference-value lineage:

- `attestation.reference_value` for versioned worker/runtime/policy/model/config
  hash reference metadata and lifecycle states.
- `attestation.endorsement` for trusted-placeholder/untrusted/revoked/expired
  endorsement metadata and evidence linkage.
- `attestation.appraisal_policy` for required reference/endorsement/evidence
  sets, freshness windows, and fail-closed policy toggles.
- `attestation.result` for metadata-only appraisal outcomes (`pass`, `fail`,
  `inconclusive`, `expired`, `blocked_mvp`) and trust effects.

Related worker/device/model-route schemas now require stronger linkage refs
(`attestation_result_ref`, `appraisal_policy_ref`) so privileged metadata paths
can fail closed when attestation appraisal posture is missing, stale, revoked,
or blocked.

These contracts remain docs/tests/mock metadata only. No TPM quote handling, no
certificate/signature validation service, no verifier daemon, and no runtime
authorization expansion are implemented.

## Durable Attestation Lineage and Authority Hardening

Phase 1A now adds metadata-only lineage/authority contracts:

- `attestation.result.lineage` for current/stale/revoked/conflicted/quarantine
  trust lineage posture, revocation propagation status, and cross-contract refs
  (worker/device/model-route/update/transaction/ledger).
- `attestation.authority` for verifier-owner/reference-approver/endorsement
  reviewer/device-trust reviewer lifecycle posture, assurance/MFA/device-trust
  requirements, and SoD-bound quarantine-clearance gating.

Related contracts now carry optional lineage/authority refs so trust posture can
be correlated across attestation, device trust, and model route records without
adding runtime authorization behavior.

## Attestation Revocation Reconciliation Drills

Phase 1A now adds metadata-only reconciliation drift posture:

- `attestation.reconciliation` for reconciled/drift/revocation-pending/
  quarantine-required/failed-closed/blocked-MVP status across lineage,
  authority, reference, endorsement, appraisal, result, route, transaction, and
  ledger refs.
- New drift classes for revoked-reference-with-current-lineage,
  revoked-endorsement-with-trusted-result, revoked-appraisal-with-selected-route,
  expired-result-with-active-worker, pending-propagation-with-privileged-route,
  quarantine mismatch, untrusted-lineage selected route, committed transaction
  with revoked attestation, missing revocation evidence, cross-tenant linkage,
  and revoked verifier authority conflicts.
- Console/supervisor examples now include reconciliation drift signals.

This remains docs/contracts/tests/mock-only hardening. No verifier runtime,
TPM, signing, update, or authorization execution is implemented.

## Connector Provider Risk / Revocation Drill Hardening

Phase 1A now adds metadata-only provider-risk and revocation-drill posture:

- `connector.provider_profile` for provider risk levels, revocation/disable
  method posture, object/property authorization posture, rate-limit and
  prompt-injection exposure posture, and fail-closed evidence linkage.
- `connector.revocation_drill` for tenant-scoped revocation/disable/scope/
  cross-tenant/prompt-injection drill outcomes with explicit expected vs actual
  fail-closed posture and evidence refs.

Related connector contracts now include stronger linkage refs:

- `connector.readiness` requires `provider_profile_ref`,
  `revocation_drill_refs`, and `token_rotation_placeholder_status`.
- `connector.scope_review` requires `provider_profile_ref`.
- `governance.connector_consent` now links provider profile and revocation
  drill refs for revoked and mock-ready pathways.
- `tool.invocation`, `approval.binding`, and `guardian.decision` add optional
  provider-profile/revocation-drill linkage refs for connector access paths.

This remains docs/contracts/tests/mock-only hardening and does not implement
live connectors, OAuth/OIDC/provider wiring, token storage, API clients,
external sends, browser automation, remediation execution, or runtime
authorization expansion.

## Connector Trust-Boundary Reconciliation Hardening

Phase 1A now adds metadata-only connector reconciliation posture:

- `connector.reconciliation` for reconciled/drift/revocation-pending/
  action-blocked/failed-closed/blocked-MVP status across provider/readiness/
  scope/trust/consent/revocation-drill/tool/approval/Guardian/evidence links.
- Drift classes for consent revoked while ready, scope overbroad while
  invocation requested, provider critical while ready, failed revocation drill
  while enabled, missing disable switch while ready, outbound action missing
  approval linkage, tainted connector payload use, cross-tenant linkage,
  missing evidence, and trust-revoked while Guardian allow posture.
- Connector path linkage now requires `connector_revocation_drill_ref` for
  connector access conditions in `tool.invocation`, `approval.binding`, and
  `guardian.decision`.

This remains docs/contracts/tests/mock-only hardening and does not implement
live connector execution, OAuth/token handling, external API calls, or runtime
authorization expansion.

## Connector Acceptance Scoring / Reconciliation SLO Hardening

Phase 1A now adds metadata-only connector acceptance and cadence posture:

- `connector.acceptance_score` for connector acceptance dimensions, score bands,
  failed dimensions, and fail-closed status mapping.
- `connector.reconciliation_slo` for reconciliation cadence placeholders,
  revocation propagation placeholders, disable-switch verification placeholders,
  and stale/missed fail-closed linkage.
- Linkage refs (`acceptance_score_ref`, `reconciliation_slo_ref`,
  `score_status`, `cadence_status`) are now available on connector provider,
  readiness, reconciliation, and revocation drill records for cross-record
  review.

This remains docs/contracts/tests/mock-only hardening and does not implement
live connectors, OAuth/token runtime, external API clients, external sends,
browser automation, or runtime authorization expansion.

## Connector Source-Of-Truth Ownership / Escalation Accountability Hardening

Phase 1A now adds metadata-only connector ownership and escalation posture:

- `connector.ownership` for owner/reviewer/approver/escalation references,
  source-of-truth status, separation-of-duties status, and fail-closed
  ownership lifecycle transitions.
- `connector.escalation` for stale-owner, missing-owner, revocation-overdue,
  disable-switch-failed, SoD, and source-of-truth conflict escalation states
  with evidence and reason-code requirements.
- Optional linkage fields (`connector_ownership_ref`,
  `connector_escalation_refs`, `ownership_status`, `source_of_truth_status`)
  are now available across connector provider/readiness/reconciliation/score/
  SLO/trust/consent/alert/health records for cross-record accountability
  review.

This remains docs/contracts/tests/mock-only hardening and does not implement
live connectors, OAuth/token runtime, external API clients, external sends,
browser automation, or runtime authorization expansion.

## Governance Export/Delete Taxonomy Hardening

Phase 1A now includes:

- `governance.export_delete_review` metadata contract for export/delete review
  outcomes without implementing export/delete services.
- Extended `governance.audit_export`, `evidence.export_manifest`,
  `evidence.ledger.entry`, and `evidence.artifact` fields for taxonomy version,
  reason-code arrays, review status placeholders, and fail-closed conflict
  evidence requirements.
- Refs-only export/delete examples with blocked/denied/fail-closed metadata
  posture and no raw customer content or secret material fields.

## Reason Code Registry Compatibility Hardening

Phase 1A now includes:

- `reason.code.registry` for canonical reason-code category/status/severity/
  visibility/evidence/fail-closed metadata.
- `reason.code.compatibility` for additive/deprecate/alias/block/remove-planned
  compatibility records with migration and affected-contract evidence.
- Registry and compatibility guidance in:
  [Reason Code Registry](taxonomy/REASON_CODE_REGISTRY.md) and
  [Reason Code Compatibility Policy](taxonomy/REASON_CODE_COMPATIBILITY_POLICY.md).

These contracts are governance metadata only and do not authorize runtime
actions.

Reason-code usage conformance is CI-gated by
[scripts/check-reason-codes.py](../scripts/check-reason-codes.py). The gate
scans `contracts/v1` and `contracts/examples` and fails closed on unknown
reason codes, deprecated-code compatibility gaps, blocked-codes in success
contexts, breaking-change coverage gaps, and missing/unsupported
`taxonomy_version` in reason-bearing schemas/examples.

## Common Field Groups

- Envelope: `contract_name`, `contract_version`, `schema_version`, `tenant_id`, `customer_context_id`, `environment`, `correlation_id`, `causation_id`, `idempotency_key`, `producer`, `created_at` or event timestamp.
- Policy and evidence: `policy_version`, `guardian_decision_id`, `evidence_artifact_id` or `evidence_artifact_ids`, `risk_tier`, `data_classification`, `redaction_status` or `redaction_level` where payloads may exist.
- Approval: `approval_required`, `approval_request_id`, `approval_token_id`, token scope binding, expiry, one-time use, revocation, and evidence.
- Phase 0 safety: `mock_only`, `live_access_enabled: false`, `raw_content_allowed: false`, `secret_material_present: false`, `production_commitment: false`, `contractual_sla: false`.

## Worker Lifecycle Contract v1

- Schema: [worker.lifecycle.schema.json](../contracts/v1/worker.lifecycle.schema.json)
- Example object: [worker.lifecycle.example.json](../contracts/examples/worker.lifecycle.example.json)
- Purpose: records Arc worker registration, health posture, quarantine, revoke, and replacement lifecycle.
- Version: `1.0.0`.
- Producer: Supervisor Server, with worker telemetry treated as untrusted input.
- Consumer: Supervisor registry, Guardian, operator dashboard, incident workflow, evidence ledger.
- Required fields: common envelope; `lifecycle_event_id`, `worker_id`, `worker_role`, `lifecycle_state`, `lifecycle_event`, `device_identity_ref`, `channel_identity_ref`, `identity_verification`, `attestation_status`, `capability_lease_id`, `capability_manifest_version`, `capability_manifest_hash_ref`, `tool_pack_scope`, `model_options`, `health_state`, `approval_state`, `quarantine_state`, `revocation_generation`, `active_task_disposition`, `approval_tokens_revoked`, `capability_lease_revoked`, `heartbeat_interval_seconds`, `missed_heartbeat_count`.
- Optional fields: `registered_at`, `approved_by_operator_id`, `last_heartbeat_at`, `quarantine_reason`, `quarantine_reason_code`, `quarantined_at`, `quarantined_by`, `release_required_by_role`, `released_at`, `revoked_at`, `replacement_worker_id`, `failure_reason`.
- Allowed states: `pending_registration`, `pending_operator_approval`, `registered`, `healthy`, `degraded`, `offline`, `quarantined`, `revoked`, `replaced`.
- Terminal states: `revoked`, `replaced`.
- Security requirements: worker identity and channel identity are refs only; unexpected capability changes force degraded or quarantined state; revoke cancels assignment and revokes active leases/tokens.
- Approval requirements: registration and quarantine release require operator or reviewer approval as policy requires; revoke can be Guardian/operator initiated and must be evidenced.
- Evidence requirements: registration, capability change, quarantine, release, revoke, replacement, and evidence-writer failure create evidence artifacts.
- Failure behavior: identity failure, evidence writer failure, suspicious tool request, or update verification failure causes fail-closed quarantine.
- Backwards compatibility notes: new lifecycle events may be added only as optional enum expansion in a minor version; state meaning changes require a major version.
- MVP acceptance gates: one admin Arc worker and one file clerk Arc worker can be represented; quarantine/revoke blocks new tasks; no unrestricted tools are granted.

## Worker Heartbeat Contract v1

- Schema: [worker.heartbeat.schema.json](../contracts/v1/worker.heartbeat.schema.json)
- Example object: [worker.heartbeat.example.json](../contracts/examples/worker.heartbeat.example.json)
- Purpose: records heartbeat telemetry and supervisor-observed health for Arc workers.
- Version: `1.0.0`.
- Producer: Arc worker for reported values; Supervisor Server for receive time, age, missed count, and derived state.
- Consumer: Supervisor registry, operator dashboard, SLO measurement, incident workflow.
- Required fields: common envelope; `heartbeat_id`, `worker_id`, `heartbeat_sequence`, `boot_id`, `reported_at`, `supervisor_received_at`, `heartbeat_due_at`, `heartbeat_age_seconds`, `worker_process_uptime_seconds`, `lifecycle_state`, `health_state`, `current_task_count`, `queue_depth`, `capability_manifest_version`, `capability_manifest_hash_ref`, `tool_pack_scope_version`, `local_model_status`, `update_version`, `rollback_version`, `update_status`, `evidence_writer_status`, `evidence_spool_depth`, `last_evidence_write_at`, `last_evidence_error_code`, `resource_posture`, `network_posture`, `network_reachability`, `guardian_reachability`, `missed_heartbeat_count`.
- Optional fields: `last_task_id`, `last_task_status`, `quarantine_reason`.
- Allowed states: `healthy`, `degraded`, `offline`, `quarantined`, `revoked`.
- Terminal states: none; heartbeat stops after revoke.
- Security requirements: worker self-report is untrusted until supervisor sequence, channel, and capability hash checks pass.
- Approval requirements: none for normal heartbeat; operator/security review is required to release quarantine.
- Evidence requirements: heartbeat anomaly, capability mismatch, evidence writer failure, update failure, and quarantine trigger produce evidence.
- Failure behavior: stale heartbeat, Guardian unreachable, or evidence unavailable causes degraded/offline/quarantine flow and fail-closed task blocking.
- Backwards compatibility notes: new metrics should be optional until dashboard consumers support them.
- MVP acceptance gates: heartbeat age, missed count, evidence writer state, clock skew, and update/rollback posture are visible for 1-8 workers.

## Worker Deployment Contract v1

- Schema: [worker.deployment.schema.json](../contracts/v1/worker.deployment.schema.json)
- Example objects: [worker.deployment.lightweight.example.json](../contracts/examples/worker.deployment.lightweight.example.json), [worker.deployment.local-model.example.json](../contracts/examples/worker.deployment.local-model.example.json), [worker.deployment.quarantined.example.json](../contracts/examples/worker.deployment.quarantined.example.json)
- Purpose: records docs-only Arc worker deployment planning metadata for mini PC hardware, OS, network, Supervisor endpoint, policy/model refs, install state, lifecycle state, encryption, attestation placeholder, update channel, rollback state, and evidence refs.
- Version: `1.0.0`.
- Producer: field IT reviewer, supervisor, operator console, or security reviewer.
- Consumer: Supervisor registry planning, field IT checklist, security review, operator deployment review, evidence ledger.
- Required fields: common envelope; `deployment_id`, `worker_id`, `role`, `hardware_profile`, `os_profile`, `network_profile`, `supervisor_endpoint_ref`, `policy_bundle_ref`, `policy_bundle_hash_ref`, `model_bundle_ref`, `model_bundle_hash_ref`, `install_state`, `lifecycle_state`, `encryption_status`, `attestation_status`, `update_channel`, `rollback_state`, approval fields, Guardian decision, policy version, evidence refs, `created_at`, and `updated_at`.
- Optional fields: support owner, field IT reviewer, security reviewer, and blocked reason.
- Allowed states: install states `planned`, `preflight_ready`, `enrollment_requested`, `enrolled_mock`, `blocked`, `quarantined`, `retired`; lifecycle states `provisioned`, `enrolled`, `active`, `degraded`, `quarantined`, `revoked`, `reenrollment_pending`, `retired`.
- Terminal states: `retired` for deployment planning; `revoked` blocks assignment until replacement or retirement.
- Security requirements: no public inbound worker exposure, no direct cross-worker trust, no automatic updates, refs rather than secrets, and attestation absence is weak lab trust only.
- Approval requirements: enrollment and deployment review are approval-required metadata paths; software install/update execution remains blocked until a future approved runtime plan.
- Evidence requirements: preflight, hardware/OS inventory, network readiness, policy/model refs, enrollment, quarantine, update/rollback planning, and retirement link evidence refs.
- Failure behavior: public inbound exposure, cross-worker trust, missing evidence, failed attestation, blocked install state, or quarantine state fails closed and blocks assignment.
- Backwards compatibility notes: adding deployment metadata is additive; weakening public exposure, cross-worker trust, automatic update, or attestation failure semantics requires major review.
- MVP acceptance gates: lightweight, local-model, and quarantined worker deployment records can be represented without installers, worker daemons, live connectors, external sends, external model calls, or remediation.

## Supervisor Health Contract v1

- Schema: [supervisor.health.schema.json](../contracts/v1/supervisor.health.schema.json)
- Example objects: [supervisor.health.healthy.example.json](../contracts/examples/supervisor.health.healthy.example.json), [supervisor.health.degraded.example.json](../contracts/examples/supervisor.health.degraded.example.json), [supervisor.health.blocked.example.json](../contracts/examples/supervisor.health.blocked.example.json)
- Purpose: records metadata-only mock/lab Supervisor health summaries for one
  Supervisor Server and 1-8 Arc workers.
- Version: `1.0.0`.
- Producer: Supervisor health reporter in the Phase 1A mock runtime.
- Consumer: tests, future operator console planning, evidence review, and
  runbook triage.
- Required fields: common envelope; `supervisor_id`, `generated_at`, `mode`,
  worker/task/Guardian/evidence count maps, stale/quarantined/revoked/blocked
  counts, `health_status`, reason codes, evidence refs, policy refs, related
  contract refs, and metadata-only redaction fields.
- Allowed states: `healthy`, `degraded`, `blocked`.
- Security requirements: health records are metadata-only, internal
  classification, and explicitly mark raw customer content and secret material
  absent.
- Evidence requirements: health records link evidence refs when evidence exists
  and link related contract refs for worker, task, and Guardian context.
- Failure behavior: denied Guardian decisions, blocked tasks, quarantined or
  revoked workers, and pre-action evidence failures produce blocked health;
  stale heartbeat or degraded evidence status produce degraded health.
- MVP acceptance gates: healthy, degraded, and blocked summaries validate
  without adding monitoring services, telemetry daemons, UI, production alerts,
  durable storage, or production SLAs.

## Governance Identity Contract v1

- Schema: [governance.identity.schema.json](../contracts/v1/governance.identity.schema.json)
- Example object: [governance.identity.operator-mfa-required.example.json](../contracts/examples/governance.identity.operator-mfa-required.example.json)
- Purpose: records operator, approver, service, worker, helper, and reviewer identity posture without storing credentials or implementing IdP/MFA.
- Version: `1.0.0`.
- Producer: operator console, supervisor, security reviewer, or compliance reviewer metadata flow.
- Consumer: approval workflow, access review, Guardian policy review, evidence ledger, and operator console spec.
- Required fields: common envelope; identity record ID, subject ref/type, IdP ref placeholder, MFA status, session assurance, device trust status, roles, least-privilege review, access review ref, joiner/mover/leaver state, policy refs, status, Guardian decision, and evidence refs.
- Security requirements: human roles must use named identity refs; service and worker identities cannot approve human approval requests; missing or blocked MFA posture fails closed for privileged runtime expansion.
- MVP acceptance gates: identity/MFA posture can be represented as required but not configured without adding IdP, MFA, OAuth, sessions, or provider wiring. `taxonomy_version` and `reason_codes` are required so blocked identity posture is machine-auditable.

## Governance Access Review Contract v1

- Schema: [governance.access_review.schema.json](../contracts/v1/governance.access_review.schema.json)
- Example object: [governance.access_review.quarterly-placeholder.example.json](../contracts/examples/governance.access_review.quarterly-placeholder.example.json)
- Purpose: records access review cadence placeholder, reviewed subject refs, findings, and separation-of-duties posture.
- Security requirements: self-review is blocked; conflicted access reviews require independent review or fail closed. `taxonomy_version` and `reason_codes` are required.
- MVP acceptance gates: quarterly placeholder and joiner/mover/leaver reviews can be represented without runtime role enforcement.

## Governance Breakglass Contract v1

- Schema: [governance.breakglass.schema.json](../contracts/v1/governance.breakglass.schema.json)
- Example object: [governance.breakglass.blocked-mvp.example.json](../contracts/examples/governance.breakglass.blocked-mvp.example.json)
- Purpose: records breakglass requests as denied or blocked metadata in MVP.
- Security requirements: breakglass cannot bypass Guardian, evidence, incident review, tenant isolation, or blocked-MVP action classes. In MVP this contract is constrained to `environment: blocked_mvp`, `status: denied_mvp|blocked`, and `reason_code: breakglass_blocked_mvp`.
- MVP acceptance gates: breakglass attempts can be evidenced as denied without creating executable emergency access.

## Governance RBAC Matrix Contract v1

- Schema: [governance.rbac_matrix.schema.json](../contracts/v1/governance.rbac_matrix.schema.json)
- Example objects: [governance.rbac_matrix.approver-privileged.example.json](../contracts/examples/governance.rbac_matrix.approver-privileged.example.json), [governance.rbac_matrix.auditor-readonly.example.json](../contracts/examples/governance.rbac_matrix.auditor-readonly.example.json), [governance.rbac_matrix.field-it-remediation-blocked.example.json](../contracts/examples/governance.rbac_matrix.field-it-remediation-blocked.example.json)
- Purpose: records tenant-scoped role/action permission metadata with MFA, session, device trust, and separation-of-duties requirements.
- Security requirements: privileged approvals require stronger MFA and trusted device posture; auditor role is view-only; LIMA IT remediation and breakglass remain blocked-MVP metadata in this phase.

## Governance Session Policy Contract v1

- Schema: [governance.session_policy.schema.json](../contracts/v1/governance.session_policy.schema.json)
- Example objects: [governance.session_policy.step-up-required.example.json](../contracts/examples/governance.session_policy.step-up-required.example.json), [governance.session_policy.revoked-on-role-change.example.json](../contracts/examples/governance.session_policy.revoked-on-role-change.example.json)
- Purpose: records session TTL/idle placeholders, step-up action requirements, and revocation triggers as governance metadata.
- Security requirements: role-change and untrusted-device revocation triggers fail closed for privileged paths.

## Governance Device Trust Contract v1

- Schema: [governance.device_trust.schema.json](../contracts/v1/governance.device_trust.schema.json)
- Example objects: [governance.device_trust.operator-managed.example.json](../contracts/examples/governance.device_trust.operator-managed.example.json), [governance.device_trust.worker-attestation-required.example.json](../contracts/examples/governance.device_trust.worker-attestation-required.example.json), [governance.device_trust.untrusted-blocked.example.json](../contracts/examples/governance.device_trust.untrusted-blocked.example.json)
- Purpose: records operator/worker device trust posture and blocked permission metadata.
- Security requirements: untrusted devices are read-only/blocked; attestation-failed workers cannot receive privileged task metadata.

## Governance Audit Export Contract v1

- Schema: [governance.audit_export.schema.json](../contracts/v1/governance.audit_export.schema.json)
- Example objects: [governance.audit_export.requested-placeholder.example.json](../contracts/examples/governance.audit_export.requested-placeholder.example.json), [governance.audit_export.delete-conflict.example.json](../contracts/examples/governance.audit_export.delete-conflict.example.json), [governance.audit_export.export-denied.example.json](../contracts/examples/governance.audit_export.export-denied.example.json)
- Purpose: records audit-export/delete review metadata posture with taxonomy
  version, reason-code arrays, review statuses, retention/redaction
  placeholders, conflict evidence refs, and fail-closed blocked/denied/failure
  outcomes.
- Privacy requirements: export records use metadata refs and exclude credentials, raw prompts, raw connector payloads, raw tool output, raw customer files, and out-of-scope tenant data.
- MVP acceptance gates: export/delete posture can be represented without adding an export service, delete service, durable database, or customer portal.

## Governance Export/Delete Review Contract v1

- Schema: [governance.export_delete_review.schema.json](../contracts/v1/governance.export_delete_review.schema.json)
- Example objects: [governance.export_delete_review.export-approved-redacted.example.json](../contracts/examples/governance.export_delete_review.export-approved-redacted.example.json), [governance.export_delete_review.delete-conflict-denied.example.json](../contracts/examples/governance.export_delete_review.delete-conflict-denied.example.json), [governance.export_delete_review.blocked-mvp.example.json](../contracts/examples/governance.export_delete_review.blocked-mvp.example.json)
- Purpose: represents metadata-only export/delete review decisions and
  conflict posture without implementing export/delete services.
- Security requirements: blocked-MVP and preservation-hold conflict states
  cannot be represented as completed export/delete outcomes.

## Governance Connector Consent Contract v1

- Schema: [governance.connector_consent.schema.json](../contracts/v1/governance.connector_consent.schema.json)
- Example object: [governance.connector_consent.revoked.example.json](../contracts/examples/governance.connector_consent.revoked.example.json)
- Purpose: records connector owner, consent, scope review, blocked scopes, revocation, rotation placeholder, data class, and prompt-injection review posture.
- Security requirements: `live_access_enabled` and `secret_material_present` remain false; scope expansion requires future independent review.
- MVP acceptance gates: revoked or blocked connector consent can be represented without OAuth, tokens, webhooks, live reads, writes, or sends.

## Governance Update Record Contract v1

- Schema: [governance.update_record.schema.json](../contracts/v1/governance.update_record.schema.json)
- Example object: [governance.update_record.rollback-required.example.json](../contracts/examples/governance.update_record.rollback-required.example.json)
- Purpose: records policy bundle, worker runtime, model bundle, or config update posture; hash/signature placeholders; staged rollout; approval; rollback; attestation; and evidence refs.
- Security requirements: signature or verification is required as policy posture, automatic updates are false, and failed verification or suspicious posture can require rollback or quarantine.
- MVP acceptance gates: update/rollback decisions can be represented without implementing an updater, installer, scheduler, daemon, endpoint control, or software update execution.

## Console View Contract v1

- Schema: [console.view.schema.json](../contracts/v1/console.view.schema.json)
- Example object: [console.view.operator-dashboard.example.json](../contracts/examples/console.view.operator-dashboard.example.json)
- Purpose: records metadata-only operator console view posture for dashboards, worker fleet, task queue, approvals, Guardian decisions, evidence, incidents, LIMA IT, deployment, governance, connectors, and audit/exit views.
- Producer: operator console spec or supervisor metadata flow.
- Consumer: future console planning, audit review, and UX validation.
- Required fields: common envelope; view ID, actor ref, role, view type, view mode, related contract refs, policy refs, risk tier, status, producer, policy version, evidence refs, and created time.
- Security requirements: read-only auditor views are read-only; blocked views require blocked reason; views do not authorize runtime behavior.
- MVP acceptance gates: operator views can be represented without frontend code, web server, live runtime controls, or production operations.

## Console Alert Contract v1

- Schema: [console.alert.schema.json](../contracts/v1/console.alert.schema.json)
- Example objects: [console.alert.worker-stale.example.json](../contracts/examples/console.alert.worker-stale.example.json), [console.alert.evidence-missing.example.json](../contracts/examples/console.alert.evidence-missing.example.json)
- Purpose: records metadata-only console alerts for health reason taxonomy states.
- Required fields: common envelope; alert ID, actor ref, role, alert type, severity, related contract refs, policy refs, risk tier, status, runbook ref, producer, policy version, evidence refs, and created time.
- Security requirements: blocked severity requires blocked reason and blocked risk tier; every alert links evidence and runbook refs.
- MVP acceptance gates: worker stale and evidence missing alerts can be represented without monitoring services or UI implementation.

## Console Action Contract v1

- Schema: [console.action.schema.json](../contracts/v1/console.action.schema.json)
- Example objects: [console.action.approval-denied.example.json](../contracts/examples/console.action.approval-denied.example.json), [console.action.worker-quarantine-requested.example.json](../contracts/examples/console.action.worker-quarantine-requested.example.json)
- Purpose: records metadata-only console review actions such as approval denial, worker quarantine request, connector revocation review, update rollback request, audit export request, LIMA IT remediation block, and breakglass denial.
- Required fields: common envelope; action ID, actor ref, role, action type, action mode, related contract refs, policy refs, risk tier, `runtime_effect: false`, approval request ref, Guardian decision ID, status, producer, policy version, evidence refs, and created time.
- Security requirements: runtime effect is always false; denied and blocked records require denial reason; read-only auditor action attempts are blocked.
- MVP acceptance gates: review actions can be represented without executing sends, connector changes, remediation, software update, endpoint control, or worker control.

## Task Execution Contract v1

- Schema: [task.execution.schema.json](../contracts/v1/task.execution.schema.json)
- Example object: [task.execution.example.json](../contracts/examples/task.execution.example.json)
- Purpose: records task intake, Guardian classification, assignment, status, result summary, approval posture, and evidence.
- Version: `1.0.0`.
- Producer: Supervisor orchestrator; workers produce status events through supervisor-owned records.
- Consumer: Task router, worker inbox/outbox, Guardian, approval workflow, evidence ledger, operator dashboard.
- Required fields: common envelope; `task_id`, `task_class`, `status`, `requested_by`, `assigned_worker_id`, `execution_mode`, `task_scope`, `required_tool_packs`, `model_route_id`, `guardian_decision_id`, `approval_required`, `approval_request_id`, `approval_token_id`, `evidence_artifact_ids`, `retry_policy`, `timeout_at`, `failure_behavior`.
- Optional fields: `result_summary`, `failure_reason`.
- Allowed states: `task_created`, `classified`, `assigned_to_worker`, `accepted`, `rejected`, `in_progress`, `needs_approval`, `draft_ready`, `blocked`, `denied`, `failed`, `blocked_evidence_unavailable`, `completed_mock`, `evidence_recorded`, `cancelled`, `timed_out`.
- Terminal states: `blocked`, `denied`, `failed`, `blocked_evidence_unavailable`, `completed_mock`, `evidence_recorded`, `cancelled`, `timed_out`.
- Security requirements: Guardian classification occurs before assignment; task scope blocks unrestricted file, browser, connector, network, or shell access.
- Approval requirements: high-risk or privileged tasks require approval request and token before execution can leave draft/mock/read-only mode.
- Evidence requirements: task creation, classification, assignment, worker acceptance/rejection, approval need, result, failure, and blocked states produce evidence.
- Failure behavior: approval timeout blocks or escalates; worker offline requeues or blocks; evidence failure blocks and may quarantine the worker.
- Backwards compatibility notes: new task classes must default to `blocked_mvp` until policy and schema examples exist.
- MVP acceptance gates: one IT helper task can complete in mock/read-only mode; external effects remain draft-only or blocked.

## Guardian Decision Contract v1

- Schema: [guardian.decision.schema.json](../contracts/v1/guardian.decision.schema.json)
- Example object: [guardian.decision.example.json](../contracts/examples/guardian.decision.example.json)
- Purpose: records Guardian policy decisions for model calls, tools, file actions, network actions, connectors, outbound messages, scheduled work, privileged operations, memory access, worker lifecycle, and LIMA IT handoff.
- Version: `1.0.0`.
- Producer: Guardian.
- Consumer: Supervisor, workers, helper agents, approval workflow, tool/model/memory/connector boundaries, evidence ledger.
- Required fields: common envelope; `decision_id`, `guardian_decision_id`,
  `request_id`, `requested_by`, `subject`, `action_class`, `resource_ref`,
  `policy_refs`, `policy_snapshot_hash`, `valid_for_action_ref`, `decision`,
  `approval_required`, approval refs, `denial_reason`, `redaction_level`,
  `evidence_required`, evidence refs, `prompt_injection`, `issued_at`,
  `effective_at`, `expires_at`, `max_age_seconds`,
  `clock_skew_allowance_seconds`, `decision_nonce`, `replay_policy`,
  `decision_scope_hash`, bound tenant/task/worker/action/tool scope,
  approval binding/token verification refs, replay status, and revoke/consume
  metadata.
- Optional fields: nullable approval, denial, worker, consume, and revoke fields
  are explicit.
- Allowed decisions: `allow`, `allow_with_evidence`, `requires_approval`, `deny`, `block_mvp`, `quarantine_subject`.
- Terminal states: `deny`, `block_mvp`, `quarantine_subject`.
- Security requirements: decision is bound to tenant, task/action/resource/input
  refs and cannot be reused across changed inputs. Runtime invariants require
  `guardian_decision_id` to equal `decision_id`, enforce UTC-aware timestamp
  windows, consume one-time decision nonces in memory for tests, and block
  stale, replayed, revoked, tainted, or mismatched decisions. Blocked-MVP
  actions cannot become approval-required actions.
- Approval requirements: `requires_approval` creates or links an `approval.request`; it is not execution authorization.
- Evidence requirements: every decision, including allow and deny, links evidence.
- Failure behavior: no valid Guardian decision means fail closed.
- Backwards compatibility notes: policy refs and decision meanings are compatibility-sensitive and require review before changes.
- MVP acceptance gates: unauthorized file deletion, external sends, live connector writes, and remediation without approval are denied or blocked.

## Guardian Replay Contract v1

- Schema: [guardian.replay.schema.json](../contracts/v1/guardian.replay.schema.json)
- Example objects: [guardian.replay.valid-first-use.example.json](../contracts/examples/guardian.replay.valid-first-use.example.json), [guardian.replay.replay-denied.example.json](../contracts/examples/guardian.replay.replay-denied.example.json), [guardian.replay.expired.example.json](../contracts/examples/guardian.replay.expired.example.json), [guardian.replay.scope-mismatch.example.json](../contracts/examples/guardian.replay.scope-mismatch.example.json), [guardian.replay.blocked-mvp.example.json](../contracts/examples/guardian.replay.blocked-mvp.example.json)
- Purpose: records metadata-only Guardian decision replay-check outcomes.
- Version: `1.0.0`.
- Producer: Guardian or Supervisor mock verifier.
- Consumer: invariant tests, future operator console planning, evidence review,
  and runbook triage.
- Required fields: common envelope; `replay_check_id`,
  `guardian_decision_id`, `decision_nonce`, approval binding/token verification
  refs, `replay_record_id`, `replay_artifact_id`, task/worker/action/tool
  scope, `decision_scope_hash`, `policy_snapshot_hash`, `expires_at`,
  `replay_check_result`, `checked_at`, evidence refs, mismatch reasons,
  data classification, redaction level, retention placeholder,
  `raw_content_included: false`, `secret_material_included: false`, export
  eligibility, and delete policy ref.
- Allowed outcomes: `valid_first_use`, `replay_denied`, `expired`, `stale`,
  `revoked`, `scope_mismatch`, `tenant_mismatch`, `blocked_mvp`.
- Security requirements: records use refs only, carry no secret material, and
  do not authorize execution. A `valid_first_use` record is evidence metadata
  for a mock check, not a durable runtime capability.
- Evidence requirements: replay, expiry, stale, mismatch, and blocked-MVP
  outcomes require evidence refs.
- Failure behavior: any failed replay check blocks the requested action and
  should become incident-review input if repeated.
- MVP acceptance gates: valid first-use and denial examples validate without
  adding durable replay storage, live connectors, external sends, remediation,
  UI, or production monitoring.

## Replay Store Record Contract v1

- Schema: [replay.store.record.schema.json](../contracts/v1/replay.store.record.schema.json)
- Example objects: [replay.store.record.consumed.example.json](../contracts/examples/replay.store.record.consumed.example.json), [replay.store.record.replay-denied.example.json](../contracts/examples/replay.store.record.replay-denied.example.json), [replay.store.record.failed-closed.example.json](../contracts/examples/replay.store.record.failed-closed.example.json)
- Purpose: represents future durable nonce reservation/consumption posture as metadata-only records without implementing storage.
- Version: `1.0.0`.
- Producer: Guardian or Supervisor replay verifier.
- Consumer: invariant checks, evidence review, incident triage, and future durable replay-store design review.
- Required fields: common envelope; `replay_record_id`, `decision_nonce`,
  `guardian_decision_id`, approval binding/token/verification refs,
  `action_type`, `tool_scope`, `nonce_status`, `atomicity_status`,
  `checked_at`, `created_at`, `raw_content_included: false`,
  `secret_material_included: false`, and evidence refs where required.
- Allowed `nonce_status` values: `reserved`, `consumed`, `replay_denied`, `expired`, `revoked`, `failed`.
- Allowed `atomicity_status` values: `pending`, `committed`, `rolled_back`, `failed_closed`.
- Security requirements: records are refs-only; they do not include raw payload
  or secret material and do not authorize execution.
- Evidence requirements: replay-denied and failed-closed records require
  evidence refs; failed-closed records also require `failure_reason`.
- Failure behavior: `failed_closed`, tenant mismatch, or action/scope mismatch
  blocks authorization.
- MVP acceptance gates: consumed/replay-denied/failed-closed examples validate
  and remain metadata-only with no durable database, queue, or runtime service.

## Transaction Boundary Contract v1

- Schema: [transaction.boundary.schema.json](../contracts/v1/transaction.boundary.schema.json)
- Example objects: [transaction.boundary.guardian-replay-consume.example.json](../contracts/examples/transaction.boundary.guardian-replay-consume.example.json), [transaction.boundary.failed-closed.example.json](../contracts/examples/transaction.boundary.failed-closed.example.json), [transaction.boundary.export-manifest-prepare.example.json](../contracts/examples/transaction.boundary.export-manifest-prepare.example.json)
- Purpose: models future atomic transaction boundaries for replay/token
  consumption, evidence append, export-manifest prepare, and delete-review
  posture without implementing transaction engines.
- Version: `1.0.0`.
- Producer: supervisor, Guardian, or operator-console metadata flow.
- Consumer: future transaction orchestration design, invariant checks, and
  audit/evidence review.
- Required fields: common envelope; `transaction_id`, `transaction_type`,
  participant set, required operations, idempotency key, preconditions,
  postconditions, status, evidence refs, failure reason, and lifecycle
  timestamps.
- Allowed statuses: `planned`, `pending`, `committed`, `rolled_back`,
  `failed_closed`, `blocked_mvp`.
- Security requirements: transaction metadata is fail-closed; ambiguous or
  partial outcomes cannot imply authorization.
- Evidence requirements: failed-closed transitions require evidence refs and
  explicit failure reason.
- Failure behavior: failed-closed blocks action authorization; blocked-MVP
  status requires blocked environment posture.
- MVP acceptance gates: examples validate as metadata-only records with no real
  database/queue/service/transaction coordinator.

## Transaction Coordinator Event Contract v1

- Schema: [transaction.coordinator.event.schema.json](../contracts/v1/transaction.coordinator.event.schema.json)
- Example objects: [transaction.coordinator.event.started.example.json](../contracts/examples/transaction.coordinator.event.started.example.json), [transaction.coordinator.event.nonce-reserved.example.json](../contracts/examples/transaction.coordinator.event.nonce-reserved.example.json), [transaction.coordinator.event.committed.example.json](../contracts/examples/transaction.coordinator.event.committed.example.json), [transaction.coordinator.event.failed-closed.example.json](../contracts/examples/transaction.coordinator.event.failed-closed.example.json), [transaction.coordinator.event.duplicate-request.example.json](../contracts/examples/transaction.coordinator.event.duplicate-request.example.json), [transaction.coordinator.event.reconciliation-completed.example.json](../contracts/examples/transaction.coordinator.event.reconciliation-completed.example.json)
- Purpose: models append-only coordinator lifecycle events for future atomic
  replay/token/evidence transactions and reconciliation posture without
  implementing a coordinator service.
- Version: `1.0.0`.
- Producer: supervisor/Guardian/operator metadata flow for future coordinator
  design.
- Consumer: transaction coordinator design review, invariant tests, audit
  sequence review, and runbook reconciliation planning.
- Required fields: common envelope; `transaction_id`, `coordinator_event_id`,
  `idempotency_scope`, `event_type`, `event_status`, `previous_event_id`,
  `next_expected_event_types`, `transaction_status`, replay/ledger/evidence
  refs, `failure_reason`, and `created_at`.
- Allowed event types: start, precondition check, replay reserve, token verify,
  pre-action evidence append, decision consume, post-action evidence append,
  committed, rolled back, failed closed, duplicate request detected,
  reconciliation start/completion.
- Security requirements: transition ordering is explicit and fail-closed;
  duplicate idempotency metadata is tenant-scoped; records are metadata-only
  and immutable by event ID.
- Evidence requirements: failed-closed, rolled-back, and evidence-appended
  paths require evidence refs; replay-touching events require replay record refs.
- Failure behavior: invalid transition ordering, duplicate tenant-scoped
  idempotency conflicts, or missing required refs fail closed.
- MVP acceptance gates: examples validate as metadata-only records with no
  database/queue/service implementation and no authorization for real actions.

## Approval Request Contract v1

- Schema: [approval.request.schema.json](../contracts/v1/approval.request.schema.json)
- Example object: [approval.request.example.json](../contracts/examples/approval.request.example.json)
- Purpose: records human approval requests for privileged or high-risk actions.
- Version: `1.0.0`.
- Producer: Supervisor approval service after Guardian says approval is required.
- Consumer: Operator dashboard, approvers, Guardian, task orchestrator, evidence ledger.
- Required fields: common envelope; `approval_request_id`, `task_id`, `guardian_decision_id`, `requested_by`, `action_class`, `requested_scope`, `scope_hash`, `reason`, `status`, `approval_result`, `approver_roles`, `evidence_required`, `evidence_artifact_ids`, `expires_at`.
- Optional fields: `approver_operator_id`, `decided_at`, `denial_reason`, `approval_token_id`.
- Allowed states: `requested`, `pending_review`, `approved`, `denied`, `expired`, `cancelled`, `superseded`.
- Terminal states: `approved`, `denied`, `expired`, `cancelled`, `superseded`.
- Security requirements: requested scope is resource-bound and one-use; approval request cannot include secret material or raw sensitive payloads.
- Approval requirements: only designated roles may approve; blocked MVP actions remain denied and do not get tokens.
- Evidence requirements: request creation, approval, denial, expiry, cancellation, and supersession produce evidence.
- Failure behavior: timeout expires the request and blocks the task.
- Backwards compatibility notes: new approval action classes require autonomy-boundary and threat-model mapping.
- MVP acceptance gates: approval-required external email draft can be represented without performing a live send; software install/update, remediation execution, production server touch, and regulated-system use remain denied blocked-MVP request outcomes.

## Approval Result Contract v1

- Schema: [approval.result.schema.json](../contracts/v1/approval.result.schema.json)
- Example objects: [approval.result.approved.example.json](../contracts/examples/approval.result.approved.example.json), [approval.result.denied-blocked-mvp.example.json](../contracts/examples/approval.result.denied-blocked-mvp.example.json)
- Purpose: records the approval outcome as a separate decision event, including denied blocked-MVP outcomes.
- Version: `1.0.0`.
- Producer: Supervisor approval service or operator console.
- Consumer: Guardian, task orchestrator, tool boundary, evidence ledger, operator dashboard.
- Required fields: common envelope; `approval_result_id`, `approval_request_id`, `task_id`, `guardian_decision_id`, `result`, `result_reason_code`, approver fields, `action_class`, `risk_tier`, `data_classification`, requested/approved scope hashes, `approval_token_id`, `blocked_mvp_action`, `denial_reason`, `fresh_operator_intent_ref`, evidence refs, `decided_at`.
- Optional fields: nullable approver/token/scope/denial refs where the result is denied, expired, cancelled, superseded, or partial.
- Allowed states: `approved`, `denied`, `expired`, `cancelled`, `superseded`, `partial_approved`.
- Terminal states: all result states are terminal for the referenced approval request event.
- Security requirements: approval cannot broaden requested scope; blocked-MVP denial cannot produce a token; partial approval requires a new request before action.
- Approval requirements: approver role and fresh operator intent are required for approved results.
- Evidence requirements: every result links evidence.
- Failure behavior: missing or contradictory approval result means the privileged action fails closed.
- Backwards compatibility notes: result semantics and reason codes are compatibility-sensitive.
- MVP acceptance gates: external email draft approval and blocked-MVP denials can be represented without live execution; software install/update, remediation execution, production server touch, and regulated-system use cannot produce approval-result tokens.

## Approval Token Contract v1

- Schema: [approval.token.schema.json](../contracts/v1/approval.token.schema.json)
- Example object: [approval.token.example.json](../contracts/examples/approval.token.example.json)
- Purpose: records scoped approval metadata after an approval request is granted.
- Version: `1.0.0`.
- Producer: Supervisor approval service.
- Consumer: Guardian, task orchestrator, tool boundary, evidence ledger.
- Required fields: common envelope; `approval_token_id`, `approval_request_id`, `guardian_decision_id`, `task_id`, `bound_task_id`, `bound_action_class`, `bound_resource_refs`, `approver_operator_id`, `approver_role_ref`, `action_class`, `scope`, `scope_hash`, `status`, `issued_at`, `expires_at`, `single_use`, `token_digest_ref`, `replay_nonce_ref`, `token_binding_ref`, `max_uses`, `used_count`, `evidence_artifact_id`, `evidence_artifact_ids`.
- Optional fields: `used_at`, `revoked_at`, `revocation_reason`.
- Allowed states: `issued`, `active`, `used`, `expired`, `revoked`.
- Terminal states: `used`, `expired`, `revoked`.
- Security requirements: token is metadata only, single-use, expiring, revocable, task/action/resource/tenant-bound, and replay-protected.
- Approval requirements: token exists only after an approved `approval.request`; it cannot approve `blocked_mvp` actions. Phase 0 v1 conditionals do not allow approval-token records for software install/update, remediation, production server touch, or regulated system use.
- Evidence requirements: issue, use, expiry, revoke, and replay rejection produce evidence.
- Failure behavior: expired, missing, mismatched, reused, or revoked tokens fail closed.
- Backwards compatibility notes: token binding semantics cannot be weakened without a major version.
- MVP acceptance gates: external effect tokens can be represented only as dry-run/mock metadata unless future contracts approve live execution.

## Token Verification Contract v1

- Schema: [token.verification.schema.json](../contracts/v1/token.verification.schema.json)
- Example objects: [token.verification.valid.example.json](../contracts/examples/token.verification.valid.example.json), [token.verification.expired.example.json](../contracts/examples/token.verification.expired.example.json), [token.verification.revoked.example.json](../contracts/examples/token.verification.revoked.example.json)
- Purpose: records scoped token verification results before any approval-required path can proceed.
- Version: `1.0.0`.
- Producer: Supervisor approval boundary or Guardian policy gate.
- Consumer: Task orchestrator, tool boundary, evidence ledger, operator dashboard.
- Required fields: common envelope; `token_verification_id`, approval request/token refs, task/action/actor refs, presented and approved scope hashes, `scope_match_result`, `token_status_observed`, `verification_result`, `fail_closed`, `can_proceed`, `denial_reason`, Guardian/policy/evidence refs, `checked_at`.
- Optional fields: nullable token/request/scope refs for missing-token failures.
- Allowed states: `valid`, `expired`, `revoked`, `used`, `mismatched`, `missing`, `ambiguous`, `wrong_scope`.
- Terminal states: each verification record is point-in-time; invalid outcomes are terminal for that action attempt.
- Security requirements: valid requires active token, matching scope, evidence, and `can_proceed: true`; all invalid outcomes require `fail_closed: true`.
- Approval requirements: verification does not approve work; it only checks a previously approved token.
- Evidence requirements: every verification links evidence.
- Failure behavior: missing, expired, revoked, used, mismatched, ambiguous, or wrong-scope token blocks the action.
- Backwards compatibility notes: verification result semantics cannot be weakened without a major version.
- MVP acceptance gates: valid, expired, and revoked metadata records can be represented without bearer token material.

## Approval Binding Contract v1

- Schema: [approval.binding.schema.json](../contracts/v1/approval.binding.schema.json)
- Example objects: [approval.binding.bound-valid.example.json](../contracts/examples/approval.binding.bound-valid.example.json), [approval.binding.consumed-one-time.example.json](../contracts/examples/approval.binding.consumed-one-time.example.json), [approval.binding.replay-denied.example.json](../contracts/examples/approval.binding.replay-denied.example.json), [approval.binding.scope-mismatch.example.json](../contracts/examples/approval.binding.scope-mismatch.example.json), [approval.binding.blocked-mvp.example.json](../contracts/examples/approval.binding.blocked-mvp.example.json)
- Purpose: normalizes the approval request/result/token/verification/Guardian/task/tool/worker/evidence chain so a valid-looking token cannot be replayed, widened, copied across tenants, used after expiry, or used for the wrong action.
- Version: `1.0.0`.
- Producer: Guardian or supervisor in mock/dry-run verification flow.
- Consumer: Phase 1A invariant checks, task queue mock assignment, future operator review, and evidence review.
- Required fields: common envelope; `approval_chain_id`, `binding_id`, approval request/result/token/verification refs, Guardian decision, task/tool/worker refs, requester/approver refs, approver role, separation result, identity assurance refs, action type, tool scope, requested/approved scope hashes, policy snapshot hash, token use policy, nonce ref, status, verification result, blocked-MVP and taint state, mismatch reasons, evidence refs, `created_at`, `checked_at`, `expires_at`, `consumed_at`, and `revoked_at`.
- Allowed states: `pending`, `bound`, `consumed`, `denied`, `expired`, `revoked`, `mismatched`, `blocked_mvp`.
- Security requirements: only `one_time` bindings can be valid in MVP; `bounded_window` is represented but cannot authorize; blocked-MVP action types cannot issue usable tokens; requester and approver must be separated; identity assurance and evidence refs are required for bound use.
- Approval requirements: a binding exists only after request/result/token/verification metadata agree. It never stores bearer token material or secrets.
- Evidence requirements: request, result, token issuance, verification, consumption, replay denial, scope mismatch, expiry, revocation, taint, and blocked-MVP outcomes link evidence refs.
- Failure behavior: missing, expired, revoked, consumed, replayed, mismatched, tainted, wider-than-approved, blocked-MVP, missing-evidence, self-approval, or wrong-scope bindings fail closed.
- MVP acceptance gates: mock helper tests prove valid one-time use passes once; replay, expiry, revocation, tenant/task/worker/action/scope/Guardian mismatch, missing evidence, taint, live connector, external send, remediation, and blocked-MVP paths fail closed.

## Approval Chain Example Bundle Contract v1

- Schema: [approval.chain.schema.json](../contracts/v1/approval.chain.schema.json)
- Example objects: [approval.chain.valid-one-time.example.json](../contracts/examples/approval.chain.valid-one-time.example.json), [approval.chain.denied-blocked-mvp.example.json](../contracts/examples/approval.chain.denied-blocked-mvp.example.json), [approval.chain.expired-token-denied.example.json](../contracts/examples/approval.chain.expired-token-denied.example.json), [approval.chain.revoked-token-denied.example.json](../contracts/examples/approval.chain.revoked-token-denied.example.json), [approval.chain.scope-mismatch-denied.example.json](../contracts/examples/approval.chain.scope-mismatch-denied.example.json), [approval.chain.tenant-mismatch-denied.example.json](../contracts/examples/approval.chain.tenant-mismatch-denied.example.json), [approval.chain.replay-denied.example.json](../contracts/examples/approval.chain.replay-denied.example.json), [approval.chain.lima-it-remediation-blocked.example.json](../contracts/examples/approval.chain.lima-it-remediation-blocked.example.json), [approval.chain.tainted-input-denied.example.json](../contracts/examples/approval.chain.tainted-input-denied.example.json)
- Purpose: validates sanitized approval-chain scenario bundles for review and documentation. These are examples only and do not authorize runtime behavior.
- Security requirements: valid bundles are mock/dry-run only; denied and blocked bundles must stay fail-closed.
- MVP acceptance gates: every bundle maps to a schema and preserves blocked work for live connectors, external sends, remediation, production operation, model provider calls, OAuth wiring, browser automation, and durable services.

## Model Route Contract v1

- Schema: [model.route.schema.json](../contracts/v1/model.route.schema.json)
- Example object: [model.route.example.json](../contracts/examples/model.route.example.json)
- Purpose: records local/subscription/cloud provider-class routing decisions without binding to a provider SDK.
- Version: `1.0.0`.
- Producer: Supervisor model router after Guardian decision.
- Consumer: Workers, helper agents, Guardian, evidence ledger, operator dashboard.
- Required fields: common envelope; `model_route_id`, `task_id`, `requested_by`, `route_state`, `prompt_sensitivity`, `model_capability_required`, `allowed_provider_classes`, `provider_class`, `selected_provider_class`, `routing_policy_ref`, `data_residency_preference`, `data_egress_allowed`, `cloud_allowed`, `fallback_allowed`, `prompt_ref`, `response_ref`, `redaction_required`, `guardian_decision_id`, `approval_required`, `approval_token_id`, `evidence_artifact_id`, `evidence_artifact_ids`, `prompt_injection`, `failure_behavior`.
- Optional fields: none for core route; `response_ref` may be null before completion.
- Allowed states: `requested`, `allowed`, `routed`, `denied`, `failed`, `fallback_required`.
- Terminal states: `denied`, `failed`, `routed` for a completed route record.
- Security requirements: raw prompts and outputs are refs only; cloud routing is blocked when policy or data classification disallows egress; local model calls still require Guardian and evidence.
- Approval requirements: sensitive/high-risk routes require approval only if policy says so; secrets never enter prompts.
- Evidence requirements: route allow/deny/fallback/failure creates evidence.
- Failure behavior: provider unavailable falls back only when policy allows; evidence failure blocks task.
- Backwards compatibility notes: provider-specific fields are deferred; new provider classes require review.
- MVP acceptance gates: local model and subscription/cloud class decisions can be represented without making model calls.

## Tool Invocation Contract v1

- Schema: [tool.invocation.schema.json](../contracts/v1/tool.invocation.schema.json)
- Example object: [tool.invocation.example.json](../contracts/examples/tool.invocation.example.json)
- Purpose: records preflight, policy result, scope, and outcome metadata for tool requests.
- Version: `1.0.0`.
- Producer: Worker, helper agent, or supervisor through Guardian-gated request flow.
- Consumer: Guardian, tool boundary, supervisor, evidence ledger, operator dashboard.
- Required fields: common envelope; `tool_invocation_id`, `task_id`, `actor`, `requested_tool`, `execution_mode`, `dry_run`, `side_effect_class`, `sandbox_profile`, `capability_lease_id`, `tool_scope`, `policy_result`, `guardian_decision_id`, `approval_required`, `approval_token_id`, `evidence_required`, `evidence_artifact_ids`, `input_artifact_refs`, `output_artifact_refs`, `timeout_seconds`, `rollback_available`, `status`, `requested_at`.
- Optional fields: `denial_reason`, `completed_at`.
- Allowed states: `requested`, `policy_checked`, `approved_to_run`, `denied`, `blocked_mvp`, `in_progress`, `completed`, `failed`, `blocked_evidence_unavailable`, `evidence_failed`.
- Terminal states: `denied`, `blocked_mvp`, `completed`, `failed`, `blocked_evidence_unavailable`, `evidence_failed`.
- Security requirements: no unrestricted tools; file, network, browser, connector, and sandbox scope are explicit; raw args and outputs are artifact refs.
- Approval requirements: side-effecting tools require scoped approval tokens; blocked MVP tools cannot run.
- Evidence requirements: preflight, approval need, denial, dry-run, completion, failure, and evidence failure produce evidence.
- Failure behavior: missing decision, missing approval, scope mismatch, timeout, or evidence failure blocks execution.
- Backwards compatibility notes: new tool types require tool-pack review and Guardian policy mapping.
- MVP acceptance gates: unauthorized file deletion is denied; read-only diagnostics and draft work can be represented.

## Helper Scope Contract v1

- Schema: [helper.scope.schema.json](../contracts/v1/helper.scope.schema.json)
- Example objects: [helper.scope.file-helper.example.json](../contracts/examples/helper.scope.file-helper.example.json), [helper.scope.memory-helper.example.json](../contracts/examples/helper.scope.memory-helper.example.json), [helper.scope.it-helper-readonly.example.json](../contracts/examples/helper.scope.it-helper-readonly.example.json)
- Purpose: bounds supervisor-side helper agents before any helper runtime work exists.
- Version: `1.0.0`.
- Producer: Supervisor after Guardian policy check.
- Consumer: Supervisor delegation layer, Guardian, tool boundary, memory boundary, evidence ledger.
- Required fields: common envelope; `helper_scope_id`, `helper_agent_id`, `helper_role`, `parent_supervisor_id`, delegation actor, `supervisor_side_only`, `independent_worker`, allowed task/tool/data/memory scope, blocked capabilities, lease expiry, status, Guardian/policy/evidence refs.
- Optional fields: revoke timestamp and reason.
- Allowed states: `draft`, `active`, `suspended`, `revoked`.
- Terminal states: `revoked`.
- Security requirements: helper agents are not workers, cannot request approval tokens, cannot use live connectors, cannot access cross-tenant memory, and cannot execute unrestricted tools.
- Approval requirements: helper scopes are Guardian-gated and operator-visible; privileged capabilities remain approval-required or blocked.
- Evidence requirements: creation, scope change, suspension, and revoke link evidence.
- Failure behavior: missing helper scope or expired/revoked scope blocks helper action.
- Backwards compatibility notes: new helper roles/capabilities require MVP and threat-model review.
- MVP acceptance gates: file, memory, and read-only IT helpers can be represented with narrow scopes.

## Taint Reference Contract v1

- Schema: [taint.ref.schema.json](../contracts/v1/taint.ref.schema.json)
- Example object: [taint.ref.prompt-injection-email.example.json](../contracts/examples/taint.ref.prompt-injection-email.example.json)
- Purpose: carries taint state and source refs across Guardian, model, task, tool, memory, approval, and evidence records.
- Version: `1.0.0`.
- Producer: Guardian or supervisor prompt-injection review.
- Consumer: Guardian, model router, tool boundary, memory boundary, approval workflow, evidence ledger.
- Required fields: common envelope; `taint_ref_id`, source type/ref/origin, `taint_status`, `severity`, injection signals, propagation chain, `raw_content_stored: false`, blocked/allowed uses, containment action, Guardian/policy/evidence refs, `detected_at`.
- Optional fields: sanitized summary and clearing operator refs.
- Allowed states: `untrusted`, `suspected`, `confirmed`, `cleared`.
- Terminal states: none; taint may be cleared only by policy and evidence.
- Security requirements: suspected/confirmed taint blocks privileged tool use, durable memory writes, external sends, remediation, and approval scope.
- Approval requirements: taint clearance requires operator/security review policy; tainted content cannot create fresh approval intent.
- Evidence requirements: detection, containment, and clearing link evidence.
- Failure behavior: unresolved taint fails closed for privileged paths.
- Backwards compatibility notes: taint status and blocked-use meanings are compatibility-sensitive.
- MVP acceptance gates: prompt-injection email taint can be represented without raw customer content.

## Memory Access Contract v1

- Schema: [memory.access.schema.json](../contracts/v1/memory.access.schema.json)
- Example object: [memory.access.example.json](../contracts/examples/memory.access.example.json)
- Purpose: records tenant-bound memory retrieval, summary writes, delete/export requests, and retention reviews.
- Version: `1.0.0`.
- Producer: Supervisor memory service or helper agent through Guardian.
- Consumer: Guardian, model router, task orchestrator, evidence ledger, operator dashboard.
- Required fields: common envelope; `memory_access_id`, `task_id`, `actor`, `memory_namespace`, `tenant_namespace`, `tenant_match_required`, `cross_tenant_access`, `cross_tenant_check_result`, `access_type`, `operation`, `classification_source`, `purpose`, `retention_class`, `retention_rule`, `delete_export_posture`, `source_refs`, `retrieval_scope`, `retrieved_record_refs`, `raw_content_allowed`, `prompt_injection_scan_status`, `policy_result`, `guardian_decision_id`, `approval_required`, `approval_token_id`, `evidence_artifact_id`, `status`, `requested_at`.
- Optional fields: `denial_reason`, `completed_at`.
- Allowed states: `requested`, `allowed`, `denied`, `blocked_mvp`, `completed`, `failed`.
- Terminal states: `denied`, `blocked_mvp`, `completed`, `failed`.
- Security requirements: `tenant_match_required` is true and `cross_tenant_access` is false; raw content is prohibited in contract records; retrieved content is treated as untrusted input.
- Approval requirements: sensitive data access, delete, and export require approval or remain blocked by policy.
- Evidence requirements: read, write summary, deny, delete/export request, retention review, and prompt-injection scan result produce evidence.
- Failure behavior: tenant mismatch, raw content request, injection suspicion, or evidence failure blocks access.
- Backwards compatibility notes: retention/delete/export semantics are compatibility-sensitive and require review.
- MVP acceptance gates: tenant-scoped memory access can be recorded without cross-tenant sharing or raw payload storage.

## Connector Trust Contract v1

- Schema: [connector.trust.schema.json](../contracts/v1/connector.trust.schema.json)
- Example object: [connector.trust.example.json](../contracts/examples/connector.trust.example.json)
- Purpose: records mock/readiness-only connector trust posture and future live-review blockers.
- Version: `1.0.0`.
- Producer: Supervisor connector registry after Guardian review.
- Consumer: Guardian, task router, operator dashboard, evidence ledger.
- Required fields: common envelope; `connector_id`, `connector_type`, `connector_state`, `mock_only`, `live_access_enabled`, `allowed_scopes`, `blocked_scopes`, `data_classifications`, `secrets_ref`, `secret_material_present`, `consent_status`, `consent_ref`, `scope_review_status`, `scope_review_ref`, `prompt_injection_exposure`, `revocation_status`, `guardian_decision_id`, `evidence_artifact_id`, `evidence_artifact_ids`.
- Optional fields: `failure_behavior`.
- Allowed states: `not_configured`, `mock_ready`, `consent_needed`, `scope_review_needed`, `disabled`, `blocked`, `future_live_candidate`.
- Terminal states: `disabled`, `blocked`.
- Security requirements: `mock_only` is true, `live_access_enabled` is false, `secret_material_present` is false, and `secrets_ref` is nullable in Phase 0.
- Approval requirements: live access, write scopes, admin scopes, and secret use require future approval and are blocked for Phase 0.
- Evidence requirements: readiness changes, scope mismatch, consent review, revocation status, and block decisions produce evidence.
- Failure behavior: scope mismatch, missing consent, or secret exposure blocks connector and creates incident evidence.
- Backwards compatibility notes: live connector fields must be added in a later reviewed version; do not reinterpret mock states as live readiness.
- MVP acceptance gates: mock email/file/ticket connectors can be represented without OAuth, tokens, webhooks, live reads, or writes.

## Connector Readiness Contract v1

- Schema: [connector.readiness.schema.json](../contracts/v1/connector.readiness.schema.json)
- Example objects: [connector.readiness.email-approved-for-lab.example.json](../contracts/examples/connector.readiness.email-approved-for-lab.example.json), [connector.readiness.browser-blocked-mvp.example.json](../contracts/examples/connector.readiness.browser-blocked-mvp.example.json), [connector.readiness.rmm-it-approval-required.example.json](../contracts/examples/connector.readiness.rmm-it-approval-required.example.json), [connector.readiness.revoked.example.json](../contracts/examples/connector.readiness.revoked.example.json)
- Purpose: defines metadata-only connector lifecycle/readiness gating before any future lab-live implementation lane.
- Required fields: common envelope; `connector_readiness_id`, `connector_id`, `connector_type`, `lifecycle_state`, `readiness_status`, owner/consent/scope refs, data classes, allowed/blocked actions, outbound/rate-limit/prompt-injection/approval policy refs, revocation refs, export-delete impact refs, reason codes, and evidence refs.
- Security requirements: no secret values; only `secrets_ref` placeholders. Missing consent/scope/revocation/evidence fails closed.
- MVP requirements: blocked connector classes remain non-usable (`browser`, `rmm_it`, `payment`, `legal_regulated`, `cloud_provider`) and external-send/form-submit/customer mutation actions remain blocked metadata posture.

## Connector Scope Review Contract v1

- Schema: [connector.scope_review.schema.json](../contracts/v1/connector.scope_review.schema.json)
- Example objects: [connector.scope_review.least-privilege-satisfied.example.json](../contracts/examples/connector.scope_review.least-privilege-satisfied.example.json), [connector.scope_review.overbroad-denied.example.json](../contracts/examples/connector.scope_review.overbroad-denied.example.json), [connector.scope_review.object-auth-missing-failed-closed.example.json](../contracts/examples/connector.scope_review.object-auth-missing-failed-closed.example.json)
- Purpose: defines metadata-only scope/object/property authorization review posture and fail-closed outcomes for overbroad or missing mappings.
- Required fields: common envelope; `scope_review_id`, connector refs, requested/approved/denied scopes, least-privilege status, object/property authorization status, reviewer/evidence refs, reason codes.
- Security requirements: overbroad/denied/missing object-property authorization mappings require reason codes and evidence refs.

## Evidence Export Manifest Contract v1

- Schema: [evidence.export_manifest.schema.json](../contracts/v1/evidence.export_manifest.schema.json)
- Example objects: [evidence.export_manifest.prepared-redacted.example.json](../contracts/examples/evidence.export_manifest.prepared-redacted.example.json), [evidence.export_manifest.denied-delete-conflict.example.json](../contracts/examples/evidence.export_manifest.denied-delete-conflict.example.json), [evidence.export_manifest.blocked-delete-conflict.example.json](../contracts/examples/evidence.export_manifest.blocked-delete-conflict.example.json), [evidence.export_manifest.exported-redacted-metadata-only.example.json](../contracts/examples/evidence.export_manifest.exported-redacted-metadata-only.example.json)
- Purpose: represents refs-only export metadata for evidence packages and
  delete-conflict posture without implementing export/delete services.
- Version: `1.0.0`.
- Producer: governance export review metadata flow.
- Consumer: compliance/security review, customer exit planning, and invariant checks.
- Required fields: common envelope; `export_manifest_id`, `export_request_id`,
  requester/approver refs, `export_status`, included/excluded evidence refs,
  review/status placeholders, reason-code arrays, linkage refs/status/canonical
  IDs, `raw_content_included: false`, `secret_material_included: false`,
  `created_at`, and evidence refs.
- Conditional requirements: prepared/exported manifests require
  `redaction_profile_ref` and `retention_policy_refs`; denied/blocked manifests
  require `delete_conflict_refs`.
- Security requirements: manifests must contain references only and cannot
  embed customer payloads or secret material.
- Evidence requirements: export decisions and conflict outcomes are evidenced.
- Failure behavior: missing redaction/retention placeholders, raw/secret flags,
  or unresolved conflict posture fails closed.
- MVP acceptance gates: manifest records validate for prepared-redacted and
  denied-delete-conflict scenarios without export tooling or customer portals.

## Evidence Ledger Entry Contract v1

- Schema: [evidence.ledger.entry.schema.json](../contracts/v1/evidence.ledger.entry.schema.json)
- Example objects: [evidence.ledger.entry.pre-action.example.json](../contracts/examples/evidence.ledger.entry.pre-action.example.json), [evidence.ledger.entry.replay-denial.example.json](../contracts/examples/evidence.ledger.entry.replay-denial.example.json), [evidence.ledger.entry.export-manifest.example.json](../contracts/examples/evidence.ledger.entry.export-manifest.example.json), [evidence.ledger.entry.rollback.example.json](../contracts/examples/evidence.ledger.entry.rollback.example.json), [evidence.ledger.entry.delete-review.example.json](../contracts/examples/evidence.ledger.entry.delete-review.example.json), [evidence.ledger.entry.failed-closed-export.example.json](../contracts/examples/evidence.ledger.entry.failed-closed-export.example.json)
- Purpose: models append-only evidence-ledger metadata for pre-action,
  post-action, denial, replay-denial, export, delete-review, and rollback
  entries without storing raw content.
- Version: `1.0.0`.
- Producer: supervisor, Guardian, operator-console, or worker metadata flow.
- Consumer: evidence integrity review, export/delete review, and future ledger
  runtime design.
- Required fields: common envelope; `ledger_entry_id`, `evidence_id`,
  parent-entry refs, hash metadata, chain position, linkage refs/status/
  canonical IDs, retention refs, redaction profile ref, export-manifest refs,
  and raw/secret exclusion flags.
- Security requirements: `raw_content_included` and
  `secret_material_included` are always `false`; chain progression requires
  parent linkage for non-root entries.
- Evidence requirements: replay-denial, export-manifest, and rollback entries
  must be represented as first-class ledger metadata.
- Failure behavior: broken chain metadata, missing required hash linkage, or
  raw/secret inclusion fails validation.
- MVP acceptance gates: ledger entries validate as metadata-only records with
  no evidence blob-store implementation.

## Evidence Artifact Contract v1

- Schema: [evidence.artifact.schema.json](../contracts/v1/evidence.artifact.schema.json)
- Example object: [evidence.artifact.example.json](../contracts/examples/evidence.artifact.example.json)
- Purpose: records redaction-aware, integrity-linked evidence metadata for important actions and decisions.
- Version: `1.0.0`.
- Producer: Guardian, supervisor, worker, helper agent, operator console, or LIMA IT bridge through supervisor ledger.
- Consumer: Audit/evidence ledger, operator dashboard, incident workflow, export/delete process.
- Required fields: common envelope; `artifact_id`, `artifact_type`, `actor`, `subject`, `action_class`, `guardian_decision_id`, `approval_request_id`, `approval_token_id`, `policy_snapshot_hash`, `redaction_status`, `redaction_profile`, `redacted_fields`, `retention_class`, `retention_policy_ref`, `retention_expires_at`, `delete_eligible`, `storage_ref`, `payload_hash`, `integrity_ref`, `previous_artifact_id`, `access_control_ref`, `export_eligible`, `export_redaction_profile`, `summary`.
- Required linkage hardening fields: related transaction/coordinator/replay/
  ledger/artifact/export refs plus `linkage_status` and
  `linkage_failure_reasons`.
- Optional fields: nullable parent/approval refs where not applicable.
- Allowed artifact types: Guardian decisions, approvals, worker lifecycle/heartbeat, task transitions, tools, model routes, memory access, connector trust, incidents, LIMA IT handoff, SLO measurement, denial, and quarantine.
- Terminal states: not stateful; artifacts are immutable records with retention/delete posture.
- Security requirements: no secret material; sensitive payloads are stored only by protected refs; evidence chain has integrity and access-control refs.
- Approval requirements: approval artifacts must link request/token state without exposing token material.
- Evidence requirements: this contract is the evidence record; every high-risk contract links to one or more artifact IDs.
- Failure behavior: evidence write failure blocks related task/model/tool/approval/remediation path.
- Backwards compatibility notes: artifact integrity and retention semantics cannot be weakened without a major version.
- MVP acceptance gates: denial, quarantine, approval, route, tool, memory, connector, incident, and LIMA IT evidence can be represented as metadata-only records.

## Evidence Failure Contract v1

- Schema: [evidence.failure.schema.json](../contracts/v1/evidence.failure.schema.json)
- Example objects: [evidence.failure.pre-action-blocked.example.json](../contracts/examples/evidence.failure.pre-action-blocked.example.json), [evidence.failure.post-action-degraded.example.json](../contracts/examples/evidence.failure.post-action-degraded.example.json)
- Purpose: records evidence writer failures, pre-action blocks, post-action degraded states, retry/reconciliation posture, and incident/quarantine linkage.
- Version: `1.0.0`.
- Producer: Supervisor, Guardian, or worker evidence writer through supervisor-owned records.
- Consumer: Task/tool boundaries, incident workflow, operator dashboard, runbooks, evidence ledger reconciliation.
- Required fields: common envelope; `evidence_failure_id`, `failure_stage`, `failure_code`, affected contract/action, `evidence_required`, action block/degrade booleans, task/worker/tool refs, last successful artifact, failure/spool/hash refs, retry/reconciliation state, incident/quarantine/token revoke fields, Guardian/policy refs, `detected_at`.
- Optional fields: nullable task/worker/tool/incident/spool refs where not applicable.
- Allowed states: failure stages `pre_action`, `post_action`, `reconciliation`; retry states `not_started`, `queued`, `retrying`, `exhausted`, `not_allowed`; reconciliation states `not_started`, `pending`, `reconciled`, `failed`.
- Terminal states: `reconciled` or `failed` reconciliation.
- Security requirements: if evidence is required and pre-action evidence cannot be written, the privileged action is blocked.
- Approval requirements: evidence failure does not grant approval; it may revoke or block token use.
- Evidence requirements: the failure record uses refs/hashes and may create incident evidence when the normal writer fails.
- Failure behavior: pre-action failures block; post-action failures degrade, spool, reconcile, and may quarantine.
- Backwards compatibility notes: failure code and reconciliation semantics are compatibility-sensitive.
- MVP acceptance gates: pre-action block and post-action degraded records can be represented with no runtime remediation.

## Incident Operations Contract v1

- Schema: [incident.ops.schema.json](../contracts/v1/incident.ops.schema.json)
- Example object: [incident.ops.example.json](../contracts/examples/incident.ops.example.json)
- Purpose: records security, operational, worker, connector, evidence, model/tool, update, network, and LIMA IT misuse incidents.
- Version: `1.0.0`.
- Producer: Supervisor, Guardian, operator console, worker, helper agent, or LIMA IT bridge.
- Consumer: Operator dashboard, security reviewer, field IT reviewer, runbooks, evidence ledger.
- Required fields: common envelope; `incident_id`, `incident_type`, `severity`, `severity_rubric`, `status`, `detected_by`, `first_detected_at`, `detected_signal`, `customer_impact`, `affected_subjects`, `affected_scope`, `containment_actions`, `containment_started_at`, `containment_completed_at`, `handoff_mode`, `remediation_authorized`, `post_review_required`, `runbook_ref`, `guardian_decision_id`, `approval_required`, `approval_request_id`, `approval_token_id`, `evidence_artifact_ids`.
- Optional fields: `lima_it_handoff_id`, `operator_owner`.
- Allowed states: `reported`, `triaged`, `contained`, `quarantined`, `escalated`, `resolved`, `post_review_needed`, `closed`.
- Terminal states: `resolved`, `closed`.
- Security requirements: containment actions are explicit; remediation authorization is always false in Phase 0 incident records.
- Approval requirements: remediation handoff can be represented only as request or denial metadata; worker quarantine can be Guardian/operator containment with evidence.
- Evidence requirements: detection, containment, escalation, LIMA IT handoff, remediation request, and post-review produce evidence.
- Failure behavior: unresolved containment escalates; evidence failure blocks remediation and raises a separate incident.
- Backwards compatibility notes: new incident types require threat-model mapping.
- MVP acceptance gates: rogue worker, prompt injection, unauthorized file mutation, stolen key suspicion, evidence failure, and LIMA IT misuse can be tracked without runtime remediation.

## Lab SLO Contract v1

- Schema: [sla.slo.schema.json](../contracts/v1/sla.slo.schema.json)
- Example object: [sla.slo.example.json](../contracts/examples/sla.slo.example.json)
- Purpose: records lab service objectives and health measurements without production guarantees.
- Version: `1.0.0`.
- Producer: Supervisor health monitor, Guardian, or worker telemetry through supervisor.
- Consumer: Operator dashboard, incident workflow, field IT reviewer.
- Required fields: common envelope; `measurement_id`, `service_level_type`, `lab_target`, `contractual_sla`, `production_commitment`, `metric_name`, `measurement_source`, `target_type`, `target_value`, `measurement_window`, `observed_value`, `status`, `breach_severity`, `owner_role`, `alert_route`, `guardian_decision_id`, `evidence_artifact_id`, `evidence_artifact_ids`, `evidence_required_on_breach`, `failure_behavior`, `measured_at`.
- Optional fields: none for core measurement.
- Allowed states: `within_target`, `warning`, `breach`, `no_data`.
- Terminal states: not stateful; each measurement is a point-in-time record.
- Security requirements: worker-reported telemetry is marked as untrusted until supervisor observed; no production SLA claim is allowed.
- Approval requirements: none for measurement; remediation generated by a breach requires separate approval.
- Evidence requirements: breaches and no-data states create evidence and incident linkage.
- Failure behavior: warning shows operator warning; breach or no data creates incident or field IT review.
- Backwards compatibility notes: metric names and target semantics should remain stable within v1.
- MVP acceptance gates: heartbeat age, evidence writer success, Guardian latency, approval queue age, quarantine count, mock connector readiness, and LIMA IT handoff age are measurable as lab targets only.

## LIMA IT Handoff Contract v1

- Schema: [lima_it.handoff.schema.json](../contracts/v1/lima_it.handoff.schema.json)
- Example object: [lima_it.handoff.example.json](../contracts/examples/lima_it.handoff.example.json)
- Purpose: records read-only diagnostics, helpdesk triage, incident escalation, and approval-required remediation handoff boundaries.
- Version: `1.0.0`.
- Producer: Supervisor or operator console after Guardian decision.
- Consumer: LIMA IT bridge, field IT reviewer, operator dashboard, incident workflow, evidence ledger.
- Required fields: common envelope; `handoff_id`, `task_id`, `incident_id`, `handoff_type`, `status`, `requested_by`, `operator_owner`, `handoff_owner_role`, `target_system_ref`, `read_only_diagnostic`, `diagnostic_scope`, `remediation_authorized`, `remediation_scope`, `guardian_decision_id`, `approval_required`, `approval_request_id`, `approval_token_id`, `evidence_artifact_ids`.
- Optional fields: nullable `task_id` or `incident_id` when the handoff is not tied to one.
- Allowed states: `draft`, `requested`, `awaiting_approval`, `diagnostic_ready`, `remediation_approval_required`, `blocked`, `denied`, `completed_mock`, `failed`, `cancelled`.
- Terminal states: `blocked`, `denied`, `completed_mock`, `failed`, `cancelled`.
- Security requirements: diagnostic scope is read-only; remediation is separate, approval-gated, and cannot touch production systems in MVP.
- Approval requirements: Phase 0 remediation request metadata requires Guardian decision, approval request/result posture, operator owner, and evidence. Remediation execution and production touch do not receive execution authorization or approval tokens in v1.
- Evidence requirements: diagnostic handoff, remediation request, denial, approval, closure, and incident escalation produce evidence.
- Failure behavior: missing approval, production touch, or evidence failure blocks remediation.
- Backwards compatibility notes: future remediation execution contracts require a major review and must not reuse diagnostic states.
- MVP acceptance gates: one LIMA IT health-check handoff can be represented as read-only diagnostics with no remediation execution.
