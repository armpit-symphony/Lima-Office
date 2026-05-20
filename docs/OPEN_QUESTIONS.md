# Open Questions

## Product And Deployment

- What is the first target vertical / ICP?
- Is the intended first deployment on-prem, hybrid, or managed private cloud?
- What is the first pilot acceptance threshold after lab mode?
- Who is the human approver role in a small business?

## Compliance And Privacy

- What compliance target matters first?
- What data retention policy should apply to evidence, memory, logs, and task records?
- What customer exit/delete process is required?
- What audit export format is needed?
- Are phone/call consent requirements in scope for the first workflows?

## Identity And Access

- What identity provider assumptions should be used for operators?
- What operator identity provider should Phase 1A assume?
- What identity assurance or MFA level is required for approvers?
- Is hardware attestation required for mini PCs?
- What attestation method should be used for Arc worker mini PCs?
- What breakglass process is acceptable?
- What breakglass policy is acceptable, and which actions remain blocked even during breakglass?
- How often should access reviews happen?
- Who can approve LIMA IT remediation requests, and what separation of duties is required?

## Connectors

- What are the first real connectors to evaluate after mock mode?
- What consent and scope review process is required?
- Which connector actions remain read-only for the first pilot?
- What revocation evidence is required?

## Models And Runtime

- What are the model provider defaults?
- What tasks are allowed to use local models?
- What tasks are allowed to use subscription/cloud models?
- What data classifications block cloud routing?
- What prompt-injection evaluation is required before connector handling?

## Worker Hardware And Operations

- What is the mini PC hardware baseline?
- What operating system baseline should be assumed?
- What heartbeat interval and missed-heartbeat thresholds are acceptable?
- What update channel and rollback mechanism should be used?
- What small-business LAN assumptions are realistic?

## Contract Schema Follow-Ups

- What redaction matrix and retention schedule should bind evidence, memory, task, incident, and worker-cache records?
- What runbooks are required before runtime for evidence-writer failure, approval timeout, worker replacement, update rollback, LIMA IT handoff, and customer exit/delete?

Resolved in [Schema Hardening Notes](SCHEMA_HARDENING_NOTES.md) and [contracts/v1](../contracts/v1):

- `approval.result` is a separate v1 schema.
- `helper.scope` is a separate v1 schema.
- v1 schemas include conditionals for approval token lifecycle states, blocked-MVP denial, LIMA IT remediation constraints, evidence-required completion, evidence failure, token verification, and taint refs.

Resolved in [Phase 0 Validation](VALIDATION.md) and [Phase 0 validation workflow](../.github/workflows/phase0-validation.yml):

- CI uses Python `jsonschema>=4.18,<5` for JSON Schema draft 2020-12 validation with format checks.

## Policy Follow-Ups

- What concrete default retention periods should replace placeholders in [Retention And Redaction Matrix](policies/retention-redaction-matrix.md)?
- What redaction profile taxonomy should apply by record type and data classification?
- What redaction strategy should apply to free-text reason fields such as `denial_reason`, `failure_reason`, `summary`, and `result_summary`?
- What audit export manifest format is required?
- What customer exit/delete/reset process and proof fields are required?
- What local emergency evidence spool depth, retry/backoff, disk-full threshold, and reconciliation process should be approved?
- What update rollback runbook and policy are required before runtime?
- What connector consent, scope review, and revocation policy is required before any live connector review?
- What access role/RBAC matrix should be enforced once the operator identity provider is selected?
- What operator identity provider and MFA level should be assumed for approval and token verification?
- What worker attestation method should be used before re-enrollment can be automated?
- What breakglass policy is acceptable, and which actions remain blocked during breakglass?
- Who can approve LIMA IT remediation requests, and what separation of duties is required?
