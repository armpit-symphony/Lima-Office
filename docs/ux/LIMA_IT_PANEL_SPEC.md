# LIMA IT Panel Spec

The LIMA IT panel shows read-only diagnostic handoffs and blocked remediation
metadata. It does not implement LIMA IT integration, remote access, endpoint
control, production touch, or remediation execution.

## Read-Only Diagnostic Handoff View

Show:

- Handoff ID.
- Task/incident refs.
- Requester and operator owner refs.
- Target system ref.
- Diagnostic scope.
- Read-only status.
- Guardian decision.
- Evidence refs.
- Runbook link.

Diagnostic handoff summaries must avoid raw customer payloads and secrets.

## Remediation Request View

Show remediation request metadata only:

- Requested remediation scope.
- Approval-required or blocked status.
- Blocked-MVP label where applicable.
- Approver separation state.
- Evidence refs.
- Incident refs.
- Denial/block reason.

No remediation execution control appears in MVP.

## Blocked MVP Remediation Labeling

The panel must label as blocked:

- Endpoint control.
- Network changes.
- Software install/update execution.
- Production server touch.
- Remote remediation.
- Regulated-system action.

## Approver Separation Warning

Warnings appear when:

- Requester and approver match.
- Field IT reviewer approves their own recommendation.
- Supervisor admin requests and approves the same high-risk handoff.
- Independent approver is missing.

## Incident Linkage

Security or operational handoffs must link to `incident.ops` when the handoff
relates to compromise, evidence failure, worker quarantine, connector risk, or
blocked remediation.

## Rollback And Evidence Requirements

For update/rollback-related LIMA IT context, the panel links to
`governance.update_record`, known-good refs, rollback reason, evidence refs, and
[Update Rollback Approval](../runbooks/update-rollback-approval.md).

## Runbook Links

- [LIMA IT handoff](../runbooks/lima-it-handoff.md)
- [Security incident](../runbooks/security-incident.md)
- [Update rollback approval](../runbooks/update-rollback-approval.md)

## Done Criteria

A handoff is done when it is diagnostic-ready, completed mock, denied, blocked,
cancelled, or failed with evidence refs. Remediation execution is never done by
this panel in MVP.
