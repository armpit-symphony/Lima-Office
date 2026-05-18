# Worker Node Spec

## Purpose

Arc worker nodes are mini PCs that execute bounded office roles under Supervisor Server coordination and Guardian gates.

## Mini PC Requirements

Minimum lab assumptions:

- 4-core CPU.
- 16 GB RAM.
- 256 GB SSD.
- Reliable LAN or Wi-Fi.
- OS account dedicated to the worker process.
- Disk encryption where available.
- TPM or equivalent device identity support preferred.

Local model workloads may require stronger CPU, RAM, GPU, or NPU resources. Hardware selection remains an open Phase 0 question.

## Runtime Components

Planned components:

- Worker identity client.
- Supervisor channel client.
- Capability manifest.
- Task inbox/outbox.
- Guardian request client.
- Model adapter boundary.
- Tool sandbox boundary.
- Local encrypted cache.
- Evidence writer.
- Health and heartbeat reporter.
- Update/rollback agent boundary.

These are planning components, not implementation in this pass.

## Local Encrypted Cache

The worker cache should hold only task-scoped and tenant-scoped data needed for assigned work. It must support:

- Encryption at rest.
- Tenant binding.
- Expiration.
- Clear-on-revoke.
- Redaction-aware evidence references.
- No cross-tenant reuse.

## Model Options

### Local Model

Local models may be used for low-risk or local-first tasks when policy allows. Local model use still requires Guardian classification and evidence.

### Subscription/Cloud Model

Subscription/cloud models may be used when task capability requires it and data classification permits it. Routing requires Guardian decision, tenant boundary, provider class, approval posture, and evidence.

## Heartbeat Behavior

Workers report heartbeat on a configured interval. Heartbeat includes:

- Worker ID.
- Tenant ID.
- Status.
- Last task status.
- Capability manifest version.
- Tool-pack scope version.
- Local model status.
- Evidence writer status.
- Update version.
- CPU, memory, disk, and network posture.
- Timestamp and heartbeat sequence.

Missed heartbeat thresholds:

- `degraded`: first threshold crossed.
- `offline`: second threshold crossed.
- `quarantined`: operator or policy containment.

## Task Inbox And Outbox

The inbox accepts only supervisor-assigned tasks with Guardian decision references. The outbox returns status, draft/result, error, and evidence references.

Workers must reject:

- Unknown tenant IDs.
- Missing Guardian decision IDs.
- Missing approval token for privileged work.
- Tool packs outside capability scope.
- Tasks after revoke.

## Tool Sandbox

Tool access is scoped by:

- Tenant.
- Worker role.
- Task class.
- Approval state.
- Capability manifest.
- Data classification.
- Guardian decision.

Unrestricted browser, file, network, connector, or shell access is blocked for MVP.

## Evidence Capture

Workers capture evidence for:

- Task accepted/rejected.
- Tool request.
- Model route request.
- Draft/result.
- Error/failure.
- Quarantine trigger.
- Heartbeat state changes.

Evidence must use references and redaction status, not raw secrets or sensitive payloads.

## Update And Rollback

Update posture must include:

- Approved update source.
- Version record.
- Pre-update health check.
- Evidence artifact.
- Rollback target.
- Quarantine on failed verification.

Software install/update requires approval.

## Quarantine Behavior

Quarantine stops new assignments and blocks privileged actions. Quarantine triggers include:

- Identity verification failure.
- Unexpected capability change.
- Suspicious tool request.
- Prompt injection suspicion.
- Evidence writer failure.
- Operator containment.
- LIMA IT or security incident handoff.

Release from quarantine requires operator review, Guardian evidence, and documented reason.

## Logs

Logs should include operational state and correlation IDs. Logs must not include plaintext API keys, tokens, raw sensitive connector payloads, or unredacted customer data.

## Open Questions

- Exact mini PC baseline.
- Required hardware attestation level.
- Local model default.
- Cache retention period.
- Network segmentation assumptions.
