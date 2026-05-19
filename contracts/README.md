# LIMA Office Contract Schemas

This directory contains Phase 0 contract schemas and sanitized example objects for LIMA Office OS. These files are planning artifacts only. They do not implement runtime services, live connectors, model calls, tool execution, external messaging, or remediation.

## Versioning

- Contract versions use semantic versioning in `contract_version`.
- Schema files live under versioned folders such as [v1](v1).
- The Phase 0 baseline is `1.0.0`.
- Additive optional fields may be added in a minor version when existing consumers can ignore them.
- Required fields, enum removals, state semantic changes, or renamed fields require a major version.

## Compatibility Rules

- Producers must emit only fields allowed by the schema. Schemas default to `additionalProperties: false`.
- A new runtime behavior is blocked until the matching contract schema and example exist.
- Runtime must fail closed when a contract is missing, policy is missing, state is ambiguous, evidence cannot be written, a token verification fails, or taint is unresolved for a privileged path.
- Guardian, approval, evidence, tenant isolation, and failure behavior are compatibility-sensitive. They cannot be weakened in a minor version.
- Consumers must fail closed on unknown contract versions, missing Guardian decisions, missing approval tokens, missing evidence, tenant mismatches, expired approvals, or evidence writer failure.
- Approval token records are metadata only. They must never contain bearer token material, OAuth codes, API keys, signatures, passwords, PINs, cookies, or plaintext secrets.

## Schema Location

Version 1 schemas are in [v1](v1):

- [worker.lifecycle.schema.json](v1/worker.lifecycle.schema.json)
- [worker.heartbeat.schema.json](v1/worker.heartbeat.schema.json)
- [task.execution.schema.json](v1/task.execution.schema.json)
- [guardian.decision.schema.json](v1/guardian.decision.schema.json)
- [approval.request.schema.json](v1/approval.request.schema.json)
- [approval.result.schema.json](v1/approval.result.schema.json)
- [approval.token.schema.json](v1/approval.token.schema.json)
- [token.verification.schema.json](v1/token.verification.schema.json)
- [model.route.schema.json](v1/model.route.schema.json)
- [tool.invocation.schema.json](v1/tool.invocation.schema.json)
- [memory.access.schema.json](v1/memory.access.schema.json)
- [helper.scope.schema.json](v1/helper.scope.schema.json)
- [taint.ref.schema.json](v1/taint.ref.schema.json)
- [connector.trust.schema.json](v1/connector.trust.schema.json)
- [evidence.artifact.schema.json](v1/evidence.artifact.schema.json)
- [evidence.failure.schema.json](v1/evidence.failure.schema.json)
- [incident.ops.schema.json](v1/incident.ops.schema.json)
- [sla.slo.schema.json](v1/sla.slo.schema.json)
- [lima_it.handoff.schema.json](v1/lima_it.handoff.schema.json)

## Example Location

Sanitized example objects are in [examples](examples):

- [worker.lifecycle.example.json](examples/worker.lifecycle.example.json)
- [worker.heartbeat.example.json](examples/worker.heartbeat.example.json)
- [task.execution.example.json](examples/task.execution.example.json)
- [guardian.decision.example.json](examples/guardian.decision.example.json)
- [approval.request.example.json](examples/approval.request.example.json)
- [approval.result.approved.example.json](examples/approval.result.approved.example.json)
- [approval.result.denied-blocked-mvp.example.json](examples/approval.result.denied-blocked-mvp.example.json)
- [approval.token.example.json](examples/approval.token.example.json)
- [token.verification.valid.example.json](examples/token.verification.valid.example.json)
- [token.verification.expired.example.json](examples/token.verification.expired.example.json)
- [token.verification.revoked.example.json](examples/token.verification.revoked.example.json)
- [model.route.example.json](examples/model.route.example.json)
- [tool.invocation.example.json](examples/tool.invocation.example.json)
- [tool.invocation.tainted-input-denied.example.json](examples/tool.invocation.tainted-input-denied.example.json)
- [memory.access.example.json](examples/memory.access.example.json)
- [helper.scope.file-helper.example.json](examples/helper.scope.file-helper.example.json)
- [helper.scope.memory-helper.example.json](examples/helper.scope.memory-helper.example.json)
- [helper.scope.it-helper-readonly.example.json](examples/helper.scope.it-helper-readonly.example.json)
- [taint.ref.prompt-injection-email.example.json](examples/taint.ref.prompt-injection-email.example.json)
- [connector.trust.example.json](examples/connector.trust.example.json)
- [evidence.artifact.example.json](examples/evidence.artifact.example.json)
- [evidence.failure.pre-action-blocked.example.json](examples/evidence.failure.pre-action-blocked.example.json)
- [evidence.failure.post-action-degraded.example.json](examples/evidence.failure.post-action-degraded.example.json)
- [incident.ops.example.json](examples/incident.ops.example.json)
- [sla.slo.example.json](examples/sla.slo.example.json)
- [lima_it.handoff.example.json](examples/lima_it.handoff.example.json)
- [lima_it.handoff.remediation-denied-mvp.example.json](examples/lima_it.handoff.remediation-denied-mvp.example.json)
- [task.execution.evidence-required-blocked.example.json](examples/task.execution.evidence-required-blocked.example.json)

Examples are sample records only. Runtime may not treat an example object as authorization, approval, evidence, policy, identity, token validity, connector readiness, or remediation permission.

## Shared Envelope

Every v1 schema requires a shared envelope:

- `contract_name`
- `contract_version`
- `schema_version`
- `tenant_id`
- `customer_context_id`
- `environment`
- `correlation_id`
- `causation_id`
- `idempotency_key`
- `producer`
- `policy_version`
- timestamps relevant to the event or record

Most action-bearing schemas also require:

- `data_classification`
- `risk_tier`
- `guardian_decision_id`
- `approval_required`
- `approval_request_id`
- `approval_token_id`
- `evidence_artifact_id` or `evidence_artifact_ids`

## Conditional Hardening

The v1 schemas use JSON Schema draft 2020-12 conditionals to block unsafe state combinations:

- `approval.request`, `approval.result`, `approval.token`, and `token.verification` bind approval status, approver identity, token state, token verification, denial, expiry, revoke, and blocked-MVP outcomes.
- `guardian.decision`, `task.execution`, `tool.invocation`, `memory.access`, and `model.route` bind policy result, approval state, taint refs, evidence failure, terminal states, and denial/failure reasons.
- `worker.lifecycle` and `worker.heartbeat` bind identity failure, quarantine, revoke, evidence-writer failure, and healthy states.
- `lima_it.handoff` keeps diagnostics read-only and keeps remediation non-executing for Phase 0.
- `evidence.artifact` and `evidence.failure` bind redaction, evidence-writer failure, emergency spool refs, reconciliation, incident, and quarantine fields.

See [Schema Hardening Notes](../docs/SCHEMA_HARDENING_NOTES.md) for the reasoning and Phase 1A test expectations.

## Schema-Hardening Rules

- Blocked-MVP actions produce denial metadata, not approval tokens.
- Approval tokens are never bearer tokens and never broaden the approved scope.
- Token verification fails closed for missing, expired, revoked, used, mismatched, ambiguous, or wrong-scope tokens.
- Tainted content cannot directly authorize tool use, durable memory writes, external sends, approval scope, or remediation.
- Evidence-required privileged actions cannot proceed when evidence cannot be written.
- Helper scopes are supervisor-side, leased, narrow, visible, and cannot inherit worker trust.
- LIMA IT remediation remains request/denial metadata only in Phase 0; diagnostics are read-only.

## Review Process

Before a schema can unlock runtime design:

1. Confirm the contract stays inside the 1 Supervisor Server and 1-8 Arc worker MVP frame.
2. Confirm Guardian is the syscall gate for the action.
3. Confirm approval-required and blocked actions match [Autonomy Boundaries](../docs/AUTONOMY_BOUNDARIES.md).
4. Confirm evidence capture, redaction, retention, and export/delete posture are explicit.
5. Confirm no schema allows unrestricted tool execution, live connector use, external sends without approval, cross-tenant memory access, direct production remediation, or plaintext secrets.
6. Confirm the relevant threat scenario in [Threat Model](../docs/THREAT_MODEL.md) has a matching schema/control.
7. Validate JSON syntax for schemas and examples.

## Policy References

Phase 0 policies are indexed in [docs/policies/README.md](../docs/policies/README.md). Contract consumers must treat these policies as pre-runtime requirements:

- [Approval Token Lifecycle](../docs/policies/approval-token-lifecycle.md)
- [Evidence Writer Failure](../docs/policies/evidence-writer-failure.md)
- [Retention And Redaction Matrix](../docs/policies/retention-redaction-matrix.md)
- [Prompt Injection Handling](../docs/policies/prompt-injection-handling.md)
- [Worker Quarantine And Re-Enrollment](../docs/policies/worker-quarantine-reenrollment.md)
- [LIMA IT Diagnostic And Remediation Handoff](../docs/policies/lima-it-diagnostic-remediation-handoff.md)

Guardian decisions must link to relevant `policy_refs`, `policy_version`, approval state, and evidence artifact refs. If the needed policy is missing or ambiguous, consumers fail closed.

## Runtime Block Rule

Runtime cannot be built for a behavior until the relevant contract is present, reviewed, and linked to Guardian, approval, evidence, failure, and MVP acceptance gates.

Phase 0 schemas are not permission to implement services. They are the minimum interface boundary future runtime work must satisfy.
