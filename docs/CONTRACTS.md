# Contracts

These are Phase 0 planning contracts. They are not runtime implementation and do not authorize live connector access, customer-system mutation, or production operation.

## Contract Rules

- Every contract must include tenant scope.
- Every privileged action must include Guardian decision and approval posture.
- Every important action must produce evidence.
- Automatic means no human approval is required; it does not bypass Guardian.
- Denied and blocked actions must be recorded.
- Examples must be sanitized and free of secrets.

## WorkerLifecycleContract v1

### Purpose

Defines Arc worker registration, health, heartbeat, quarantine, revoke, and replacement posture.

### States

- `pending_registration`
- `registered`
- `pending_operator_approval`
- `healthy`
- `degraded`
- `offline`
- `quarantined`
- `revoked`
- `replaced`

### Required Fields

- `contract_version`
- `tenant_id`
- `worker_id`
- `device_identity_ref`
- `role`
- `capability_manifest_version`
- `tool_pack_scope`
- `model_options`
- `heartbeat_interval_seconds`
- `last_heartbeat_at`
- `missed_heartbeat_count`
- `health_state`
- `quarantine_reason`
- `revoked_at`
- `guardian_decision_id`
- `evidence_artifact_id`

### Guards

- Registration requires supervisor acceptance and Guardian evidence.
- Unexpected capability changes force degraded or quarantined state.
- Failed identity verification forces quarantine.
- Revoke prevents task assignment until re-enrollment.

## TaskExecutionContract v1

### Purpose

Defines task intake, Guardian classification, assignment, worker status, draft/result, approval, and evidence posture.

### States

- `task_created`
- `classified`
- `assigned_to_worker`
- `accepted`
- `in_progress`
- `needs_approval`
- `draft_ready`
- `blocked`
- `failed`
- `completed_mock`
- `evidence_recorded`

### Required Fields

- `contract_version`
- `tenant_id`
- `task_id`
- `task_class`
- `assigned_worker_id`
- `data_classification`
- `required_tool_packs`
- `model_route`
- `risk_tier`
- `guardian_decision_id`
- `approval_token_id`
- `status`
- `result_summary`
- `evidence_artifact_id`
- `timeout_at`
- `retry_policy`

### Guards

- Guardian classification happens before assignment.
- Approval token is required before high-risk or privileged task execution.
- Results must reference evidence.
- External writes remain blocked for MVP.

## GuardianDecisionContract v1

### Purpose

Defines Guardian classification and action decision for model, tool, file, network, connector, outbound, scheduled, and privileged requests.

### Decisions

- `allow`
- `allow_with_evidence`
- `requires_approval`
- `deny`
- `block_mvp`
- `quarantine_subject`

### Required Fields

- `contract_version`
- `tenant_id`
- `decision_id`
- `requested_by_type`
- `requested_by_id`
- `subject_type`
- `subject_id`
- `action_class`
- `resource_ref`
- `data_classification`
- `risk_tier`
- `policy_refs`
- `decision`
- `approval_required`
- `approval_token_id`
- `denial_reason`
- `redaction_level`
- `evidence_artifact_id`
- `created_at`

### Guards

- No model/provider/tool call can execute without a decision ID.
- Blocked MVP actions cannot be converted to approval-required actions.
- Denials and quarantines require evidence.

## IncidentOpsContract v1

### Purpose

Defines incident handling for suspicious worker behavior, prompt injection, connector overreach, failed evidence writes, compromised device, or LIMA IT handoff.

### States

- `reported`
- `triaged`
- `contained`
- `quarantined`
- `escalated`
- `resolved`
- `post_review_needed`

### Required Fields

- `contract_version`
- `tenant_id`
- `incident_id`
- `incident_type`
- `detected_by`
- `affected_worker_id`
- `affected_connector_ref`
- `severity`
- `containment_action`
- `lima_it_handoff_id`
- `approval_token_id`
- `evidence_artifact_ids`
- `operator_owner`
- `status`

### Guards

- Containment can quarantine or disable mock connector readiness.
- Remediation requires approval.
- LIMA IT handoff must distinguish diagnostics from remediation.

## SLA/SLOContract v1

### Purpose

Defines lab MVP service targets without production guarantees.

### Metrics

- Supervisor health status.
- Worker heartbeat age.
- Missed heartbeat count.
- Task queue age.
- Evidence write success/failure.
- Guardian decision latency.
- Approval queue age.
- Quarantine count.
- Mock connector readiness status.

### Required Fields

- `contract_version`
- `tenant_id`
- `metric_id`
- `metric_name`
- `target`
- `measurement_window`
- `alert_threshold`
- `evidence_artifact_id`
- `owner_role`

### Guards

- Metrics are lab targets, not production SLAs.
- Breaches create evidence and operator visibility.

## ConnectorTrustContract v1

### Purpose

Defines mock connector readiness and future live connector trust posture.

### States

- `not_configured`
- `mock_ready`
- `consent_needed`
- `scope_review_needed`
- `disabled`
- `blocked`
- `future_live_candidate`

### Required Fields

- `contract_version`
- `tenant_id`
- `connector_id`
- `connector_type`
- `state`
- `allowed_scopes`
- `blocked_scopes`
- `data_classifications`
- `secret_ref`
- `consent_ref`
- `risk_tier`
- `revocation_status`
- `guardian_decision_id`
- `evidence_artifact_id`

### Guards

- Phase 0 permits mock/readiness states only.
- No plaintext API keys or hardcoded secrets.
- Future live connectors require threat model, consent, scope review, revocation, and approval posture.

## EvidenceArtifactContract v1

### Purpose

Defines evidence records for decisions, approvals, worker events, task transitions, incidents, connector readiness, and LIMA IT handoff.

### Required Fields

- `contract_version`
- `tenant_id`
- `artifact_id`
- `correlation_id`
- `artifact_type`
- `actor_type`
- `actor_id`
- `operator_id`
- `worker_id`
- `helper_agent_id`
- `task_id`
- `action_class`
- `risk_tier`
- `guardian_decision_id`
- `approval_result_id`
- `summary`
- `redaction_status`
- `retention_rule`
- `export_eligible`
- `integrity_ref`
- `created_at`

### Guards

- Evidence proves decisions without exposing secrets.
- Sensitive payloads are redacted or referenced by protected location.
- Export/delete/customer exit posture must be documented before runtime use.

## Supporting Contract Notes

Future contract work should add separate detail for:

- Approval request/result.
- Model route request/result.
- Tool invocation request/result.
- Memory access request/result.
- Helper-agent scope.
- Audit export and customer exit.
- LIMA IT diagnostic/remediation handoff.
