# LIMA IT Handoff Runbook

## Purpose

Guide operators through LIMA IT diagnostic, helpdesk triage, incident escalation, and remediation-request handoff.

## Policy Traceability

- Policy ref: `policy.lima_it_handoff.phase0`
- Version: `policy-phase0-v1`
- Triggering contracts: `lima_it.handoff`, `guardian.decision`, `approval.request`, `approval.token`, `incident.ops`, `evidence.artifact`.
- Required fields: tenant/customer context, handoff ID, handoff type, target system ref, diagnostic scope, remediation scope, operator owner, Guardian decision ID, approval posture, evidence artifact IDs, correlation ID.
- Fail-closed outcome: diagnostics remain read-only, remediation remains draft/request-only, production touch is blocked.

## When To Use

Use this runbook when:

- A health-check task needs read-only LIMA IT review.
- A helpdesk triage summary is needed.
- A security or operational incident needs field IT context.
- A remediation request is drafted for future approval review.

## Prerequisites

- `lima_it.handoff` record or draft.
- Guardian decision.
- Tenant ID and customer context.
- Target system ref.
- Diagnostic scope.
- Evidence artifact refs.
- Incident ID if incident-related.

## Must Not

- Do not execute remediation in Phase 0.
- Do not touch production servers.
- Do not install or update software.
- Do not change network/firewall/system settings.
- Do not use live connectors or OAuth.
- Do not hide background work from the operator.

## Procedure

1. Confirm handoff type: health check, diagnostic triage, helpdesk triage, remediation request, or incident escalation.
2. Verify Guardian decision and risk tier.
3. Confirm `read_only_diagnostic` is true for diagnostic handoff.
4. Review allowed read-only checks and prohibited actions.
5. Confirm remediation scope says `requested: false` unless this is a draft remediation request.
6. If remediation is requested, require approval request and keep status non-executing.
7. Link incident record if handoff is incident-related.
8. Capture evidence before sharing handoff context.
9. Share only redacted, metadata/ref-based diagnostic context.
10. Record closure or next-review evidence.

## Approval Requirements

Read-only diagnostic review may be allowed under low or medium risk policy.

Remediation requires approval and remains non-executing in Phase 0. Who can approve LIMA IT remediation is an open policy question before runtime.

## Evidence To Capture

- Guardian handoff decision.
- Handoff ID.
- Diagnostic scope.
- Operator owner.
- Field IT reviewer or approver role.
- Incident ID when linked.
- Approval request/token if remediation request is represented.
- Rollback plan placeholder for any future remediation.
- Handoff result or closure.

## Containment / Rollback

- If diagnostic scope is exceeded, block handoff and create incident.
- If production touch is requested, block and escalate.
- If evidence cannot be written, do not proceed.
- If remediation is requested without approval, deny and record evidence.

## Escalation

Escalate to:

- Field IT reviewer for diagnostics and health-check interpretation.
- Security reviewer for incident-related handoff or misuse.
- Supervisor admin for ambiguous target systems or approval role questions.

## Done Criteria

- Handoff remains read-only unless future approved policy says otherwise.
- Guardian, approval posture, evidence refs, tenant/customer context, actor identity, and correlation ID are recorded.
- Incident linkage exists when relevant.
- No production remediation occurred.
