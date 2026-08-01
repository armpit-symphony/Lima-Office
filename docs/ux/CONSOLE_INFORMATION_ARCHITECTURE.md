# Console Information Architecture

## Top-Level Navigation

| Navigation item | Primary panels | Default audience |
| --- | --- | --- |
| Overview | Supervisor health, active alerts, blocked states, recent evidence, runbook queue | All roles |
| Workers | Fleet table, worker detail, heartbeat, deployment, quarantine/revoke, re-enrollment | Operators, field IT, security |
| Tasks | Queue table, task detail, Guardian decision, approval status, evidence | Operators, approvers, auditors |
| Approvals | Approval inbox, request detail, decision history, token metadata | Approvers, operators, security |
| Guardian | Decision table, taint review, policy refs, blocked-MVP decisions | Operators, security, auditors |
| Evidence | Artifact viewer, evidence failure, redaction/export posture | Operators, security, compliance, auditors |
| Incidents | Incident table, containment, runbooks, affected refs | Operators, security, field IT |
| LIMA IT | Diagnostic handoffs, remediation blocked states, incident links | Operators, field IT, auditors |
| Deployment | Worker deployment, hardware/OS/network, attestation, update/rollback | Field IT, operators |
| Governance | Identity/MFA, access review, breakglass blocked, separation checks | Security, compliance, operators |
| Connectors | Mock readiness, consent, scope, revocation, prompt-injection posture | Operators, security |
| Audit / Exit | Export/delete requests, redaction, preservation conflicts | Compliance, operators, auditors |
| Runbooks | Linked procedures by state and reason code | All roles |

## Page And Panel Hierarchy

- Overview: summary bands for health, alerts, approvals, stale workers, evidence
  failures, incidents, and blocked-MVP attempts.
- Detail pages: each entity page shows summary, status timeline, related
  contracts, Guardian decision, evidence refs, runbook links, and allowed
  spec-only actions.
- Drawers/modals are not required by this spec; future UI may choose layout, but
  evidence and policy context must remain visible before any approval action.

## Data Cards

Data cards summarize one entity and must include:

- Entity ID/ref.
- Tenant/customer context.
- Status and reason code.
- Risk tier.
- Data classification where relevant.
- Guardian decision ref.
- Evidence refs.
- Runbook link.

Cards must not display raw secrets, raw customer payloads, raw connector
payloads, raw prompts, or raw tool output.

## Tables

Tables are expected for:

- Workers.
- Tasks.
- Approvals.
- Guardian decisions.
- Evidence artifacts.
- Incidents.
- LIMA IT handoffs.
- Connector readiness.
- Governance identity/access review records.
- Export/delete requests.

Required table columns: state, severity, reason code, actor/ref, related worker
or task, updated time, evidence state, and runbook link.

## Filters And Search

Minimum filters:

- Tenant/customer context.
- Environment.
- Severity.
- Status.
- Worker role.
- Worker lifecycle state.
- Task status.
- Approval status.
- Guardian decision.
- Data classification.
- Evidence failure.
- Runbook required.
- Blocked-MVP.

Search uses IDs/refs and sanitized summaries only.

## Status Badges

Badge categories:

- Healthy.
- Pending review.
- Needs approval.
- Denied.
- Blocked MVP.
- Degraded.
- Quarantined.
- Revoked.
- Expired.
- Evidence missing.
- Tainted input.
- Rollback required.
- Connector revoked.

## Empty States

Empty states must say whether:

- No records exist.
- Records are unavailable.
- Policy is missing.
- Evidence is missing.
- The view is hidden by role.

Empty states must not imply the system is healthy when data is missing.

## Warning, Blocked, And Degraded States

Warning states show next review step. Blocked states show the missing contract,
policy, evidence, approval, token, or role requirement. Degraded states show the
reason code, affected component, latest evidence ref, and runbook.

## Audit Trail Placement

Every detail view places audit trail links near the top:

- Guardian decision.
- Approval request/result/token refs.
- Evidence artifact refs.
- Incident refs.
- Console action refs where available.

## Evidence Links

Evidence links must appear on every action-bearing row and every alert. If no
evidence exists for a required action, show `evidence_missing` and block the
action.

## Runbook Links

Each warning, blocked, degraded, or high-risk state must link to the specific
runbook that describes the next manual step.
