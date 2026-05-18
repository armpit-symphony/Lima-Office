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
- Is hardware attestation required for mini PCs?
- What breakglass process is acceptable?
- How often should access reviews happen?

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

- Should `approval.result` become a separate v1 schema, or remain represented by `approval.request` status/result fields and `approval.token` lifecycle fields?
- Should supervisor-side helper agents get a dedicated `helper.scope` schema before any helper runtime work?
- What JSON Schema validator should be used in CI for draft 2020-12 validation?
- What redaction matrix and retention schedule should bind evidence, memory, task, incident, and worker-cache records?
- What runbooks are required before runtime for evidence-writer failure, approval timeout, worker replacement, update rollback, LIMA IT handoff, and customer exit/delete?
