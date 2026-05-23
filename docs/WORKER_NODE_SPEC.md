# Worker Node Spec

## Purpose

Arc worker nodes are mini PCs that execute bounded office roles under Supervisor Server coordination and Guardian gates.

## Mini PC Requirements

Minimum lab assumptions are defined in the [Worker Hardware Baseline](deployment/WORKER_HARDWARE_BASELINE.md). The baseline remains vendor-neutral:

- 4-core CPU.
- 16 GB RAM.
- 256 GB SSD.
- Reliable LAN or Wi-Fi.
- OS account dedicated to the worker process.
- Disk encryption where available.
- TPM or equivalent device identity support preferred.

Local model workloads may require stronger CPU, RAM, GPU, or NPU resources.
Exact product SKU and local-model sizing thresholds remain open planning
questions.

The [Worker Deployment Blueprint](deployment/WORKER_DEPLOYMENT_BLUEPRINT.md)
separates lightweight, standard, local-model, and supervisor/helper-capable
machine classes. The blueprint does not recommend exact consumer products and
does not authorize production deployment.

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

The proposed install layout is documented in [Worker Install Layout](deployment/WORKER_INSTALL_LAYOUT.md). It is a filesystem and naming convention only; it does not create services, daemons, updater agents, or endpoint control.

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

For MVP planning, cloud/subscription model workers are contract-only. External model API calls and provider account wiring remain blocked until model-routing defaults, data classification, egress, redaction, and approval gates are resolved.

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

- `degraded`: planning default is 2 missed heartbeats or evidence writer degradation.
- `offline`: planning default is 5 missed heartbeats or supervisor unreachable.
- `quarantined`: operator or policy containment.

These are planning defaults from [Worker Deployment Blueprint](deployment/WORKER_DEPLOYMENT_BLUEPRINT.md). Runtime thresholds remain policy-controlled and must be tested before lab expansion.

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

Update and rollback planning is expanded in [Update Rollback Blueprint](deployment/UPDATE_ROLLBACK_BLUEPRINT.md). Automatic update execution remains blocked; update channels are policy bundle, worker runtime, model bundle, and config metadata refs only.
Governance details are in [Signed Update Rollback Policy](governance/SIGNED_UPDATE_ROLLBACK_POLICY.md)
and [Update Rollback Approval](runbooks/update-rollback-approval.md). These
docs do not implement an updater, installer, scheduler, or rollback service.

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

- Required hardware attestation method, trust root, and key lifecycle beyond
  the placeholder in [Worker Attestation Policy](governance/WORKER_ATTESTATION_POLICY.md).
- Local model default.
- Cache retention period.
- Network segmentation assumptions.
- Exact product SKU remains intentionally undecided.
