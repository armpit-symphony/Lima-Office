# Supervisor Spec

## Purpose

The Supervisor Server is the LIMA Office OS control plane for one small-business tenant. It coordinates workers, applies policy, requests Guardian decisions, manages approvals, records evidence, and reports status.

## Orchestrator

The orchestrator owns task intake, state transitions, worker assignment, retry posture, timeout handling, and degraded-mode behavior. It cannot bypass Guardian.

## Task Router

The task router matches tasks to workers using:

- Worker role.
- Capability manifest.
- Health state.
- Tool-pack scope.
- Model options.
- Data classification.
- Current load.
- Guardian decision.
- Approval state.

## Policy Engine

The policy engine stores planning rules for:

- Autonomy boundaries.
- Risk tiers.
- Approval requirements.
- Blocked MVP actions.
- Connector readiness.
- Tenant isolation.
- LIMA IT handoff.

Guardian remains the syscall gate for action decisions.

## Approval Service

The approval service manages requests for privileged or high-risk work. Approval records include approver identity, scope, action class, risk tier, expiration, replay protection, and evidence references.

Approval review must also account for the governance policy scaffolding in
[Governance Docs](governance/README.md): identity/MFA posture, access review,
approver separation, breakglass denial, export/delete review, connector consent,
attestation, and update/rollback posture. Missing or ambiguous governance
posture blocks privileged runtime expansion.

## Worker Registry

The worker registry tracks:

- Deployment ID.
- Worker ID.
- Device identity reference.
- Channel identity reference.
- Role.
- Hardware and OS profile refs.
- Supervisor endpoint ref.
- Capability manifest.
- Policy and model bundle refs.
- Health state.
- Last heartbeat timestamp.
- Missed heartbeat count.
- Assigned tasks.
- Quarantine/revoke status.
- Update version.
- Rollback state.
- Evidence refs.

## Model Router

The model router selects local or subscription/cloud provider class based on policy. It must record:

- Tenant.
- Task.
- Worker/helper identity.
- Data classification.
- Provider class.
- Guardian decision ID.
- Evidence artifact ID.

It does not make direct model calls without Guardian approval.

## Audit/Evidence Ledger

The ledger records references to evidence artifacts for:

- Guardian decisions.
- Approvals.
- Worker lifecycle events.
- Task transitions.
- Incidents.
- Connector readiness.
- LIMA IT handoff.

Evidence must be redaction-aware, export-aware, and retention-aware.
Audit export and customer exit/delete posture is defined as metadata-only in
[Audit Export And Customer Exit Policy](governance/AUDIT_EXPORT_AND_CUSTOMER_EXIT_POLICY.md).

## Tenant Memory Service

Tenant memory is scoped to one tenant and one customer context at a time. It must support:

- Tenant namespace.
- Source reference.
- Retention rule.
- Delete/export posture.
- Prompt injection handling for retrieved content.
- No cross-tenant sharing.

## Helper Agents

The supervisor may use 1-4 helper agents for memory review, file organization, background review, or LIMA IT assistance. Helper agents:

- Stay supervisor-side.
- Use scoped tasks.
- Require Guardian decisions for actions.
- Produce evidence.
- Do not receive unrestricted tools.
- Cannot directly mutate customer systems.

## Operator Dashboard

The dashboard should show:

- Supervisor health.
- Worker status.
- Last heartbeat age.
- Active task count.
- Pending approvals.
- Guardian allow/deny/approval counts.
- Evidence write status.
- Mock connector readiness.
- Quarantine incidents.
- LIMA IT handoff status.

## LIMA IT Bridge

The bridge is future-facing and contract-only in Phase 0. It supports:

- Health-check context.
- Diagnostic handoff.
- Helpdesk triage.
- Approved remediation request.
- Incident evidence sharing.

Remediation requires human approval.

## Health Checks

Supervisor health checks should cover:

- Service state.
- Worker heartbeat freshness.
- Queue depth.
- Evidence writer status.
- Approval queue age.
- Guardian decision flow.
- Disk, memory, CPU, and network posture.
- Mock connector readiness.
- Worker deployment record completeness.
- Policy/model bundle ref mismatch.
- Public inbound exposure or cross-worker trust flags in deployment records.

## Failure Modes

Planned failure modes:

- Worker offline.
- Worker degraded.
- Worker quarantined.
- Guardian unavailable.
- Evidence writer failure.
- Approval timeout.
- Model provider unavailable.
- Mock connector disabled.
- Supervisor restart.
- LIMA IT handoff unavailable.

Each failure must have visible status, evidence, and a runbook or open question.

## Deployment Planning

The Supervisor Server owns the worker deployment registry posture for lab and
planned local deployments. It must treat `worker.deployment` records as planning
metadata only, not execution permission. A deployment record cannot authorize
worker services, live connectors, external sends, external model calls,
remediation, software install/update execution, or production-system access.
