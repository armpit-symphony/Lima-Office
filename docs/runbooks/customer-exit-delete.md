# Customer Exit Delete Runbook

## Purpose

Define the manual, docs-only review path for customer exit, audit export, delete
requests, worker cache purge planning, and evidence preservation conflicts.

## When To Use

- Customer exit request.
- Delete or reset request.
- Audit export request tied to exit.
- Worker retirement or device reuse review.

## Prerequisites

- [Audit Export And Customer Exit Policy](../governance/AUDIT_EXPORT_AND_CUSTOMER_EXIT_POLICY.md)
- [Retention Redaction Policy](../governance/RETENTION_REDACTION_POLICY.md)
- `governance.audit_export` record.
- Worker deployment and lifecycle records when devices are in scope.
- Connector consent records when connectors are in scope.

## Steps

1. Confirm tenant and customer context.
2. Record requester identity ref and requested scope.
3. Classify request as export, delete, exit, or combined review.
4. Inventory task, Guardian, approval, evidence, worker, model, tool, memory,
   connector, LIMA IT, incident, and governance record classes.
5. Identify non-exportable classes and redaction profile.
6. Identify evidence preservation conflicts.
7. Review connector revocation needs.
8. Review worker cache purge, device retirement, or reset needs.
9. Record approval requirements and reviewer refs.
10. Capture evidence and unresolved blockers.

## Approval Requirements

- Export requires operator approval.
- Sensitive export requires security or compliance review.
- Delete requires compliance review.
- Device retirement or cache purge requires field IT review.
- Self-approval for conflict closure is blocked; unresolved reviewer separation
  keeps the request blocked.

## Evidence To Capture

- Export/delete request ID.
- Scope and date range.
- Included/excluded record classes.
- Redaction profile.
- Preservation conflict status.
- Connector revocation refs.
- Worker purge or retirement refs.
- Evidence refs.

## Rollback / Containment

- If scope is ambiguous, block export/delete.
- If preservation conflict exists, block automatic delete.
- If preservation conflict is unresolved, keep delete denied/blocked and record
  conflict evidence refs.
- If connector status is unknown, revoke or disable future live review posture.
- If worker cache purge proof is missing, keep device retired or quarantined.

## Escalation

Escalate to compliance reviewer for retention conflict and to security reviewer
for incidents, secret exposure, or cross-tenant risk.

## Done Criteria

- Export/delete posture is recorded.
- Redaction and evidence refs exist.
- Unresolved legal, retention, or evidence conflicts remain explicitly open.
- No runtime export or delete action is implied.
