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
- [approval.token.schema.json](v1/approval.token.schema.json)
- [model.route.schema.json](v1/model.route.schema.json)
- [tool.invocation.schema.json](v1/tool.invocation.schema.json)
- [memory.access.schema.json](v1/memory.access.schema.json)
- [connector.trust.schema.json](v1/connector.trust.schema.json)
- [evidence.artifact.schema.json](v1/evidence.artifact.schema.json)
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
- [approval.token.example.json](examples/approval.token.example.json)
- [model.route.example.json](examples/model.route.example.json)
- [tool.invocation.example.json](examples/tool.invocation.example.json)
- [memory.access.example.json](examples/memory.access.example.json)
- [connector.trust.example.json](examples/connector.trust.example.json)
- [evidence.artifact.example.json](examples/evidence.artifact.example.json)
- [incident.ops.example.json](examples/incident.ops.example.json)
- [sla.slo.example.json](examples/sla.slo.example.json)
- [lima_it.handoff.example.json](examples/lima_it.handoff.example.json)

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
