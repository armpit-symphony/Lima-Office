# Contracts

These are Phase 0 planning contracts. They are field-level schemas and examples only; they do not authorize runtime services, live connector access, customer-system mutation, external sends, or production operation.

The schema source of truth is [contracts/README.md](../contracts/README.md) and [contracts/v1](../contracts/v1). Example JSON objects are in [contracts/examples](../contracts/examples).

Phase 0 policies are pre-runtime requirements and are indexed in [docs/policies/README.md](policies/README.md). A contract record is not enough to authorize runtime behavior; Guardian must also link the relevant policy refs, approval state, and evidence.

## Contract Rules

- Every contract includes tenant scope through `tenant_id` and `customer_context_id`.
- Every contract includes a common envelope: `contract_name`, `contract_version`, `schema_version`, `environment`, `correlation_id`, `causation_id`, `idempotency_key`, `producer`, `policy_version`, timestamps, Guardian linkage where applicable, and evidence linkage.
- Automatic means no human approval is required; it does not bypass Guardian.
- Approval-required actions need an `approval.request` and, after approval, a scoped one-time `approval.token` metadata record.
- Approval tokens are references and metadata only. They must never contain bearer token material, PINs, OAuth codes, API keys, signatures, or plaintext secrets.
- Evidence is required for allow, deny, approval, failure, quarantine, revoke, incident, connector readiness, memory access, model route, tool invocation, and LIMA IT handoff events.
- Denied, blocked, failed, expired, revoked, and quarantined states are first-class outcomes.
- Examples are sanitized and use opaque refs instead of real customer names, file paths, email addresses, URLs with secrets, raw prompts, raw tool output, connector payloads, or secret values.

## Common Compatibility Rules

- `contract_version` follows semantic versioning. Version `1.0.0` is the Phase 0 baseline.
- Additive optional fields may be introduced in a minor version if old consumers can ignore them.
- Required field changes, enum removals, renamed fields, or state semantic changes require a major version.
- New producers must not emit a contract version unless the relevant schema and example are present.
- Runtime implementation remains blocked until the specific contract it needs is present, reviewed, and mapped to Guardian, approval, and evidence behavior.
- Runtime implementation also remains blocked when the relevant policy or operator runbook is missing or ambiguous.

## Conditional Validity Notes

Version 1 schemas now use JSON Schema draft 2020-12 conditionals for the highest-risk cross-field rules. These rules are contract guardrails, not runtime implementation:

- Denied, blocked-MVP, failed, expired, revoked, quarantined, and evidence-failure states require matching reason, evidence, or failure fields.
- Approved approval requests/results require approver identity, decision time, narrowed scope, token linkage, and evidence.
- Blocked-MVP actions cannot issue approval tokens.
- Token verification must fail closed for missing, expired, revoked, used, mismatched, ambiguous, or wrong-scope tokens.
- Evidence-required task/tool paths cannot be represented as completed when evidence failure blocks the action.
- Tainted content must remain data-only unless a later policy review clears it; it cannot directly become tool args, durable memory, approval scope, external sends, or remediation.
- LIMA IT remediation is non-executing in Phase 0; diagnostic handoff remains read-only.

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
- Required fields: common envelope; `decision_id`, `request_id`, `requested_by`, `subject`, `action_class`, `resource_ref`, `policy_refs`, `policy_snapshot_hash`, `valid_for_action_ref`, `decision`, `approval_required`, `approval_request_id`, `approval_token_id`, `denial_reason`, `redaction_level`, `evidence_required`, `evidence_artifact_id`, `evidence_artifact_ids`, `prompt_injection`, `expires_at`.
- Optional fields: none for the core decision; nullable approval and denial fields are explicit.
- Allowed decisions: `allow`, `allow_with_evidence`, `requires_approval`, `deny`, `block_mvp`, `quarantine_subject`.
- Terminal states: `deny`, `block_mvp`, `quarantine_subject`.
- Security requirements: decision is bound to tenant, task/action/resource/input refs and cannot be reused across changed inputs; blocked MVP actions cannot become approval-required actions.
- Approval requirements: `requires_approval` creates or links an `approval.request`; it is not execution authorization.
- Evidence requirements: every decision, including allow and deny, links evidence.
- Failure behavior: no valid Guardian decision means fail closed.
- Backwards compatibility notes: policy refs and decision meanings are compatibility-sensitive and require review before changes.
- MVP acceptance gates: unauthorized file deletion, external sends, live connector writes, and remediation without approval are denied or blocked.

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

## Evidence Artifact Contract v1

- Schema: [evidence.artifact.schema.json](../contracts/v1/evidence.artifact.schema.json)
- Example object: [evidence.artifact.example.json](../contracts/examples/evidence.artifact.example.json)
- Purpose: records redaction-aware, integrity-linked evidence metadata for important actions and decisions.
- Version: `1.0.0`.
- Producer: Guardian, supervisor, worker, helper agent, operator console, or LIMA IT bridge through supervisor ledger.
- Consumer: Audit/evidence ledger, operator dashboard, incident workflow, export/delete process.
- Required fields: common envelope; `artifact_id`, `artifact_type`, `actor`, `subject`, `action_class`, `guardian_decision_id`, `approval_request_id`, `approval_token_id`, `policy_snapshot_hash`, `redaction_status`, `redaction_profile`, `redacted_fields`, `retention_class`, `retention_policy_ref`, `retention_expires_at`, `delete_eligible`, `storage_ref`, `payload_hash`, `integrity_ref`, `previous_artifact_id`, `access_control_ref`, `export_eligible`, `export_redaction_profile`, `summary`.
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
