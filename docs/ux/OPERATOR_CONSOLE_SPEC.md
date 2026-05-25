# Operator Console Spec

## Purpose

Define the operator-facing control room for the LIMA Office Supervisor Server.
The console makes Supervisor health, Arc worker state, Guardian decisions,
approval requests, evidence, incidents, deployment posture, governance posture,
connector readiness, and LIMA IT handoffs understandable to a small-business
operator or SparkPit field operator.

This is a specification only. It does not implement UI code or runtime controls.

## Target Users

- SparkPit operator: supervises lab/customer context, reviews queue health, and
  coordinates field runbooks.
- Customer admin: views customer-scoped status and requests review actions.
- Approver: approves or denies assigned approval requests when policy allows.
- Field IT operator: reviews worker deployment, heartbeat, network, update,
  rollback, and attestation posture.
- Read-only auditor/reviewer: reviews evidence, decisions, incidents, and
  governance records without approving or mutating.

## Primary Dashboard Areas

| Area | Purpose | Primary contracts |
| --- | --- | --- |
| Supervisor health | Show Guardian, evidence, queue, worker, connector-readiness, LIMA IT, and governance status | `sla.slo`, `guardian.decision`, `evidence.failure`, `incident.ops` |
| Worker fleet | Show worker lifecycle, deployment state, heartbeat age, policy/model hashes, quarantine, revoke, and re-enrollment posture | `worker.lifecycle`, `worker.heartbeat`, `worker.deployment` |
| Task queue | Show task intake, assignment, status, approval need, evidence state, and blocked reasons | `task.execution`, `guardian.decision` |
| Approval inbox | Show approval requests and allow approve/deny metadata flow only | `approval.request`, `approval.result`, `approval.token`, `token.verification` |
| Guardian decisions | Show allow, approval-required, deny, block-MVP, and quarantine decisions | `guardian.decision`, `taint.ref` |
| Evidence/artifact viewer | Show evidence refs, hashes, redaction, retention, export posture, and failure states | `evidence.artifact`, `evidence.failure` |
| Incidents | Show security, operational, evidence, worker, connector, LIMA IT, and update incidents | `incident.ops` |
| LIMA IT handoffs | Show read-only diagnostic handoff and blocked remediation metadata | `lima_it.handoff`, `approval.result` |
| Deployment/update/attestation | Show worker deployment records, update/rollback records, attestation placeholders, and field checklists | `worker.deployment`, `worker.attestation`, `governance.update_record`, `update.rollback` |
| Governance/access review | Show identity/MFA placeholders, role review, separation checks, and breakglass denial | `governance.identity`, `governance.access_review`, `governance.breakglass` |
| Connector readiness | Show mock connector readiness, consent, scope, provider risk profile, revocation/disable drill posture, least-privilege object/property authorization mapping, prompt-injection posture, and cross-record reconciliation drift | `connector.trust`, `connector.readiness`, `connector.scope_review`, `connector.provider_profile`, `connector.revocation_drill`, `connector.reconciliation`, `governance.connector_consent` |
| Audit/export/delete requests | Show export/delete scope, redaction profile, non-exportable classes, and preservation conflict state | `governance.audit_export` |

## Navigation Model

Top-level navigation:

1. Overview.
2. Workers.
3. Tasks.
4. Approvals.
5. Guardian.
6. Evidence.
7. Incidents.
8. LIMA IT.
9. Deployment.
10. Governance.
11. Connectors.
12. Audit / Exit.
13. Runbooks.

Every page includes tenant/customer context, environment label, current role,
last refreshed record time, active blocked states, and links to relevant
runbooks.

## Alert Severity Model

- `info`: normal status, draft-only state, or pending review.
- `warning`: degraded health, missing optional metadata, stale review, or soon
  expiring approval.
- `high`: stale worker, evidence writer degraded, attestation failed, update
  rollback required, connector revoked, or approval expired.
- `blocked`: missing evidence, Guardian denied, blocked-MVP action, token
  mismatch, LIMA IT remediation blocked, missing retention/export policy, or
  missing IdP/MFA posture.

## Read-Only Vs Approval-Capable Views

Read-only views may inspect status, evidence refs, decisions, and runbook links.
They cannot approve, deny, request export/delete, quarantine/re-enroll workers,
change connector posture, or review update/rollback requests.

Approval-capable views show decision controls only when:

- The actor role is allowed by [Console Permission Model](CONSOLE_PERMISSION_MODEL.md).
- Policy refs are present.
- Guardian decision is present and current enough for future runtime rules.
- Evidence refs are present or the flow is explicitly blocked on evidence.
- The actor is not self-approving a high-risk action.

## Fail-Closed UX Behavior

The console must show blocked state when any required item is missing:

- Guardian decision.
- Policy refs.
- Approval request/result where required.
- Evidence refs.
- Token verification where required.
- Tenant/customer context.
- Model-route status/reason taxonomy for high-risk task paths.
- Worker identity or deployment refs.
- Connector consent or revocation posture.
- Provider risk profile or revocation-drill evidence linkage.
- Connector trust-boundary reconciliation drift.
- Connector acceptance score posture and reconciliation SLO posture.
- Governance identity/MFA/access review posture for privileged views.
- Retention/export/delete posture for export or delete requests.

Blocked states must show the reason, required runbook, related contract refs,
and next safe manual review lane.

## Blocked MVP Actions

The console must label these as blocked:

- Live connectors, OAuth/provider wiring, connector tokens, webhooks, live reads,
  or live writes.
- External email/text/chat sends or form submissions.
- External model provider calls.
- Browser automation.
- Remediation execution, endpoint control, network changes, software
  install/update execution, or production server touch.
- Databases, queues, web servers, schedulers, daemons, UI frameworks, or
  production operations.
- Breakglass runtime behavior.
- Cross-tenant memory sharing.

## Acceptance Gates

- Console spec stays inside one Supervisor Server and 1-8 Arc workers.
- Every command view names required Guardian, policy, approval, evidence, and
  runbook refs.
- High-risk actions show approve, deny, expired, revoked, token mismatch,
  tainted input, and blocked-MVP states.
- Worker quarantine/revoke/re-enrollment controls are spec-only and
  evidence-gated.
- LIMA IT remediation remains non-executing and blocked or approval-required
  metadata only.
- No screen implies live connector readiness, external sends, remediation, or
  production operation.
