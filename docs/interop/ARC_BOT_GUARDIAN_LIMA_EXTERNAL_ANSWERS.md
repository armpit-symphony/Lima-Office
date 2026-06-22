# Arc Bot Guardian / LIMA Office External Answers

Status: handoff answer, docs/contracts only.

This document answers the Arc Bot completion-gate blockers that require
Guardian/LIMA Office ownership decisions. It does not add runtime behavior,
durable services, sockets, local model execution, model-provider wiring,
connector behavior, operator-console UI, background workers, queues, databases,
or production-readiness claims.

The direct answer is: the static contracts can satisfy the metadata and owner
references below, but the seven runtime dependencies remain blocked until later
implementation gates explicitly approve them.

## Requested Answers

| Arc Bot blocker | LIMA Office answer | Canonical source | Owner | Boundary |
| --- | --- | --- | --- | --- |
| Canonical approval-token reference format | Use `approval_token_id` as the canonical token record identifier. When Arc Bot needs a typed reference string in a refs list, use `approval.token:<approval_token_id>`. The value is an opaque record ref only and must never carry bearer token material. | `contracts/v1/approval.token.schema.json`, `contracts/v1/approval.binding.schema.json`, [Approval Token Runtime Binding](../APPROVAL_TOKEN_RUNTIME_BINDING.md) | LIMA Office Supervisor approval plane with Guardian verification | Metadata only; no live token store or token material is provided. |
| Required approval binding fields | Required binding context is `tenant_id`, `customer_context_id`, `approval_chain_id`, `binding_id`, `approval_request_id`, `approval_result_id`, `approval_token_id`, `token_verification_id`, `guardian_decision_id`, `task_id`, `tool_invocation_id`, `worker_id`, `requester_ref`, `approver_ref`, `approver_role_ref`, `action_type`, `tool_scope`, `requested_scope_hash`, `approved_scope_hash`, `policy_snapshot_hash`, `token_use_policy`, `nonce_ref`, `status`, `verification_result`, `mismatch_reasons`, `evidence_required`, `evidence_refs`, and timestamps. | `contracts/v1/approval.binding.schema.json`, [Approval Token Runtime Binding](../APPROVAL_TOKEN_RUNTIME_BINDING.md) | Guardian approval-binding verifier with Supervisor approval records | Arc Bot may consume binding state; it must not mint or widen approval bindings. |
| Signature and replay verification owner | Replay verification is owned by the LIMA Office Guardian plane with Supervisor-produced replay/evidence metadata. Signature verification for future signed artifacts belongs to the relevant LIMA Office verifier authority; Arc Bot consumes result refs, not raw signatures or verifier internals. | `contracts/v1/guardian.replay.schema.json`, `contracts/v1/replay.store.record.schema.json`, [Guardian Expiry and Replay Policy](../GUARDIAN_EXPIRY_REPLAY_POLICY.md), [Durable Replay and Evidence Posture](../DURABLE_REPLAY_EVIDENCE_POSTURE.md), [Signed Update Rollback Trust](../architecture/SIGNED_UPDATE_ROLLBACK_TRUST.md) | LIMA Office Guardian verifier and future durable replay/evidence plane | Current replay checks are mock/in-memory metadata. Durable replay/signature services remain blocked. |
| Canonical `RuntimeStateSnapshot` fields | No dedicated `RuntimeStateSnapshot` schema exists yet. For Arc Bot, the canonical state snapshot is a composite of `supervisor.health`, `worker.heartbeat`, `worker.lifecycle`, `model.route`, `guardian.decision`, evidence refs, and console refs. Required projection fields should include `contract_version`, `tenant_id`, `customer_context_id`, `snapshot_id`, `snapshot_generated_at`, `supervisor_id`, `supervisor_health_ref`, worker counts/states, route status counts, Guardian decision refs, evidence refs, policy refs, and blocked runtime capability flags. | `contracts/v1/supervisor.health.schema.json`, `contracts/v1/worker.heartbeat.schema.json`, `contracts/v1/worker.lifecycle.schema.json`, `contracts/v1/model.route.schema.json`, `contracts/v1/console.view.schema.json` | LIMA Office Supervisor health/state plane | Docs-only projection for Arc Bot. A dedicated schema is a future open question, not required for this handoff. |
| Durable evidence writer / audit-Spine owner | LIMA Office owns the evidence writer and audit-Spine lineage. Arc Bot should carry `evidence_refs`, `evidence_artifact_ids`, ledger refs, and failure refs only. | `contracts/v1/evidence.artifact.schema.json`, `contracts/v1/evidence.ledger.entry.schema.json`, `contracts/v1/evidence.failure.schema.json`, [Durable Replay and Evidence Posture](../DURABLE_REPLAY_EVIDENCE_POSTURE.md), [Durable Storage Architecture](../architecture/DURABLE_STORAGE_ARCHITECTURE.md) | LIMA Office Supervisor evidence plane with Guardian evidence requirements | Current evidence writer is metadata-only/in-memory. Durable audit-Spine implementation remains blocked. |
| Operator-console server-state owner | LIMA Office Supervisor/operator plane owns canonical console server state. Arc Bot may display read-only projections or related refs, but it must not become the source of truth for server state. | `contracts/v1/console.view.schema.json`, `contracts/v1/console.alert.schema.json`, `contracts/v1/console.action.schema.json`, `contracts/v1/supervisor.health.schema.json`, [Operator Console Spec](../ux/OPERATOR_CONSOLE_SPEC.md) | LIMA Office Supervisor and operator-console plane | No UI or server-state runtime is added by this answer. |
| Guardian-owned local-model executor boundary | Guardian owns the future local-model executor boundary as the syscall gate. Today there is no approved local-model executor. `model.route` can represent `mock_only` or `local_planned` metadata; `local_model_bundle_ref.execution_enabled` remains `false`. | `contracts/v1/model.route.schema.json`, [Model Routing Defaults](../architecture/MODEL_ROUTING_DEFAULTS.md), [Runtime Boundaries](../RUNTIME_BOUNDARIES.md), [Arc Bot Ollama/Qwen Readiness Handoff](ARC_BOT_OLLAMA_QWEN_READINESS_HANDOFF.md) | LIMA Office Guardian plane plus Supervisor model-route policy | Arc Bot must not execute local inference, call Ollama/Qwen, probe endpoints, or treat route metadata as execution authority. |

## Approval Token Reference

Canonical token references are metadata records, not bearer capabilities.

Use:

- `approval_token_id`: plain canonical identifier on approval/token/binding
  records.
- `approval.token:<approval_token_id>`: typed ref form for generic refs arrays.
- `token_verification_id`: verification result ref.
- `binding_id` or `approval.binding:<binding_id>`: approval binding ref.
- `approval_chain_id`: approval-chain correlation ref.

Do not use:

- bearer tokens,
- API keys,
- provider tokens,
- OAuth codes,
- raw signatures,
- cookies,
- PINs,
- credential strings,
- plaintext nonces,
- cert or TPM quote material.

Arc Bot must fail closed when the token ref is missing, unknown, expired,
revoked, consumed, mismatched, replayed, cross-tenant, outside scope, missing
evidence, or attached to a blocked-MVP action.

## Approval Binding Fields

For a usable mock/dry-run approval binding, Arc Bot should expect these fields
to agree across the approval chain:

- Tenant and customer context: `tenant_id`, `customer_context_id`.
- Request chain: `approval_chain_id`, `binding_id`, `approval_request_id`,
  `approval_result_id`, `approval_token_id`, `token_verification_id`.
- Guardian chain: `guardian_decision_id`, optional `replay_record_id`,
  optional `replay_artifact_id`.
- Work identity: `task_id`, `tool_invocation_id`, `worker_id`,
  `requester_ref`, `approver_ref`, `approver_role_ref`.
- Scope: `action_type`, `tool_scope`, `requested_scope_hash`,
  `approved_scope_hash`, `policy_snapshot_hash`.
- Replay/expiry: `token_use_policy`, `nonce_ref`, `expires_at`,
  `consumed_at`, `revoked_at`.
- Outcome: `status`, `verification_result`, `blocked_mvp_action`,
  `mismatch_reasons`.
- Evidence: `evidence_required`, `evidence_refs`, denial/pre/post-action refs
  where present.

Only `status: bound`, `verification_result: valid`,
`token_use_policy: one_time`, matching scope, unexpired timestamps, and required
evidence can be treated as a valid mock/dry-run binding. Even then, it does not
authorize live connectors, external sends, remediation, provider-token use, or
local model execution.

## Runtime State Snapshot

LIMA Office does not currently define a standalone `RuntimeStateSnapshot`
contract. Arc Bot should treat runtime state as a read-only projection over
existing contracts:

- `supervisor.health`: supervisor identity, generated time, mode, worker
  counts, task counts, Guardian decision counts, evidence status counts,
  route status counts, health status, reasons, policy refs, related contract
  refs.
- `worker.heartbeat`: worker identity, heartbeat age, lifecycle/health state,
  local model status, attestation status, evidence-writer status, Guardian
  reachability, network posture, model route status.
- `worker.lifecycle`: worker identity, lifecycle state, quarantine/revocation
  state, capability lease, model route posture, attestation refs, evidence refs.
- `model.route`: route mode/status, model role, policy refs, evidence refs,
  fallback policy, local model bundle ref with execution disabled.
- `console.view` and `console.alert`: operator-visible projections and alert
  refs, not canonical execution state.

If Arc Bot needs a synthetic snapshot packet before a schema exists, use a
docs-only projection with:

- `contract_version`
- `tenant_id`
- `customer_context_id`
- `snapshot_id`
- `snapshot_generated_at`
- `supervisor_id`
- `supervisor_health_ref`
- `worker_refs`
- `worker_state_counts`
- `task_state_counts`
- `model_route_status_counts`
- `guardian_decision_refs`
- `evidence_refs`
- `policy_refs`
- `blocked_capabilities`
- `reason_codes`

That projection is non-authoritative unless all source refs are present and
same-tenant.

## Evidence And Console Ownership

The durable evidence writer, future audit-Spine, and canonical operator-console
server state are LIMA Office owned.

Arc Bot may consume:

- `evidence_refs`
- `evidence_artifact_ids`
- `related_ledger_entry_ids`
- `related_evidence_artifact_ids`
- `replay_record_id`
- `replay_artifact_id`
- `console.view` refs
- `console.alert` refs
- `supervisor.health` refs

Arc Bot must not create canonical LIMA Office evidence, mutate console server
state, declare evidence durable, or use local display state as authorization.

## Local Model Executor Boundary

The future local-model executor, if approved, must be Guardian-owned. The
boundary is:

1. Supervisor model-route policy selects a route candidate.
2. Guardian evaluates tenant, task, RBAC/session, device trust, attestation,
   taint, approval, fallback, evidence, and MVP scope.
3. Evidence is required before and after any future execution boundary.
4. Execution is denied when the route is `blocked_mvp`, `denied`,
   `unavailable`, mismatched, missing evidence, untrusted, or outside policy.

Current handoff state:

- `route_mode` may be `mock_only` or `local_planned`.
- `local_planned` does not mean local inference execution.
- `route_status: selected` on a mock route is metadata only.
- `blocked_mvp` cannot be treated as selected.
- `fallback_allowed` must remain `false` for the Arc Bot local Ollama/Qwen
  packet.
- `local_model_bundle_ref.execution_enabled` must remain `false`.

## Arc Bot Fail-Closed Rules

Arc Bot must fail closed when:

- any required ref is missing,
- tenant/customer context differs across records,
- approval binding and Guardian decision disagree,
- token verification is missing or not valid,
- replay status is not first-use/valid for the intended mock/dry-run path,
- evidence refs are missing,
- worker lifecycle is quarantined/revoked/offline for the operation,
- route status is `denied`, `blocked_mvp`, or `unavailable`,
- route mode is `subscription_planned` for this local packet,
- provider fallback or provider-token fields appear,
- the packet implies live model execution, connector behavior, external sends,
  remediation, or endpoint probing.

## What This Unblocks

This handoff unblocks Arc Bot's static-consumption question for canonical refs,
field ownership, and failure posture. It does not unblock runtime execution.

The Arc Bot completion gate should still report runtime-dependent criteria as
blocked until LIMA Office separately approves and implements:

- durable approval-token consumption,
- durable replay store,
- durable evidence writer/audit-Spine,
- operator-console server-state runtime,
- RuntimeStateSnapshot schema if needed,
- Guardian-owned local-model executor,
- any local inference runtime.

## Open Questions

- Should `RuntimeStateSnapshot` become a first-class contract, or remain a
  projection over `supervisor.health`, worker state, model routes, Guardian
  decisions, evidence, and console refs?
- Should approval-token typed refs such as
  `approval.token:<approval_token_id>` be formalized as a shared ref-string
  convention across all contracts?
- Which future implementation lane owns the durable evidence writer and
  audit-Spine: storage/transaction planning, supervised lab orchestration, or a
  separate evidence-runtime lane?
- What exact Guardian local-model executor contract is required before any
  Ollama/Qwen execution can be represented?

## Non-Goals

- No Ollama integration.
- No Qwen inference.
- No local model executor.
- No model-provider runtime.
- No endpoint probing.
- No provider fallback.
- No provider-token handling.
- No connector behavior.
- No OAuth/OIDC/SAML wiring.
- No runtime authorization expansion.
- No background workers, queues, daemons, databases, or operator-console UI.
- No production-readiness claim.
