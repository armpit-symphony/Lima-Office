# MVP Scope

## MVP Frame

The lab MVP starts with 1 Supervisor Server and 1-3 Arc worker mini PCs. The design path extends to 1-8 workers for one small business tenant.

The MVP is governed, visible, and evidence-producing. It is not a production deployment.

## Lab MVP

Required lab capabilities:

- Worker deployment planning record.
- Supervisor Server inventory and status.
- 1-3 registered Arc workers.
- Worker heartbeat and health state.
- Worker capability manifest.
- Task assignment record.
- Task status/result record.
- Guardian risk tiering record.
- Approval token record for privileged tasks.
- Evidence artifact record.
- Quarantine/revoke state.
- Basic operator dashboard specification.
- Mock connector readiness states.

## Designed Path To 1-8 Workers

The architecture should scale from 1-3 lab workers to 1-8 office workers by adding:

- Deployment IDs and hardware/OS/network inventory.
- Worker identity enrollment.
- Capability versioning.
- Heartbeat age and missed heartbeat count.
- Queue depth and assignment limits.
- Quarantine and replacement flow.
- Role-scoped tool packs.
- Evidence correlation across supervisor and worker.

## Worker Registration

Worker registration must capture:

- `deployment_id`
- `worker_id`
- `tenant_id`
- `device_identity`
- `role`
- `capability_manifest_version`
- `model_options`
- `tool_pack_scope`
- `registered_at`
- `approved_by`
- `status`

Registration is not active until the supervisor accepts the worker and Guardian records the registration decision.

Deployment records are metadata-only planning records. They do not authorize
worker services, software installation, external model calls, live connectors,
external sends, remediation, or production operation.

## Heartbeat

Heartbeat must capture:

- Timestamp.
- Worker status.
- Capability version.
- Current task count.
- Queue depth.
- Local model status.
- Update version.
- Disk, memory, CPU, and network posture.
- Evidence writer status.
- Missed heartbeat count.

## Capability Manifest

The capability manifest declares what the worker may do. It must not grant unrestricted tools.

Minimum fields:

- Role.
- Supported task classes.
- Allowed tool packs.
- Allowed model routes.
- Data classifications allowed.
- Connector posture.
- Approval-required capabilities.
- Blocked capabilities.

## Task Assignment

Task assignment requires:

- Tenant and task identifiers.
- Worker identifier.
- Task class.
- Risk tier.
- Data classification.
- Required tool packs.
- Guardian decision ID.
- Approval token ID when required.
- Evidence artifact ID.
- Timeout and retry posture.

## Task Status And Result

Workers report:

- Accepted.
- Rejected.
- In progress.
- Needs approval.
- Draft ready.
- Blocked.
- Failed.
- Completed in lab/mock mode.
- Quarantined.

Results must include evidence references and must not imply external writes unless a future approved contract allows them.

## Evidence Capture

Evidence capture is required for:

- Worker registration.
- Guardian allow/deny decisions.
- Approval request/result.
- Task assignment.
- Worker result.
- Quarantine/revoke.
- Connector readiness changes.
- LIMA IT handoff.

## Guardian Risk Tiering

Initial tiers:

- `low`: read-only or draft-only work with no sensitive data.
- `medium`: sensitive context, connector read, file organization, or diagnostic gathering.
- `high`: external write, customer record mutation, software update, remediation, regulated system, or sensitive HR/finance/legal/medical access.
- `blocked`: MVP-denied actions.

## Approval Token For Privileged Tasks

Approval token records must include:

- Approver identity.
- Tenant.
- Task.
- Action class.
- Risk tier.
- Expiration.
- Scope.
- Replay protection.
- Guardian decision ID.
- Evidence artifact ID.

## Quarantine And Revoke

The supervisor must be able to quarantine or revoke a worker when:

- Heartbeat fails.
- Capability manifest changes unexpectedly.
- Worker identity cannot be verified.
- Evidence writing fails.
- Prompt injection or tool misuse is suspected.
- Operator requests containment.

## Basic Operator Dashboard Spec

The dashboard should show:

- Supervisor health.
- Worker list and status.
- Last heartbeat timestamp and age.
- Missed heartbeat count.
- Active tasks.
- Pending approvals.
- Guardian allow/deny/approval counts.
- Quarantine state.
- Mock connector readiness.
- Evidence write status.
- Open incidents.
- Worker deployment completeness.
- Policy/model bundle ref mismatch.

## Mock Connectors First

Connector work is mock/readiness-only until contracts and threat model are approved. Mock connector states:

- Not configured.
- Mock ready.
- Consent needed.
- Scope review needed.
- Disabled.
- Blocked.
- Future live candidate.

## Out Of Scope

- Live customer connectors.
- OAuth/token handling for real systems.
- External sends.
- Customer-system writes.
- Hidden background jobs.
- Production server changes.
- Autonomous financial decisions.
- Autonomous employee discipline or monitoring decisions.
- Cross-tenant memory sharing.
- Unrestricted browser, file, or network access.
- Runtime implementation beyond explicitly approved tiny scaffolding.
- Worker installers, daemons, endpoint control, automatic updates, or production
  deployment.
