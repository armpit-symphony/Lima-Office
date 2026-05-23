# Access Review Runbook

## Purpose

Review operator, approver, supervisor admin, field IT, security, compliance,
LIMA IT, worker, helper, and service identity roles before runtime expansion.

## When To Use

- Scheduled access review placeholder.
- Joiner, mover, or leaver event.
- Privileged role assignment.
- Security incident or identity ambiguity.

## Prerequisites

- [Identity And MFA Policy](../governance/IDENTITY_AND_MFA_POLICY.md)
- [Approver Separation Policy](../governance/APPROVER_SEPARATION_POLICY.md)
- `governance.identity` records.
- `governance.access_review` record.

## Steps

1. Confirm tenant and customer context.
2. List subject refs and assigned roles.
3. Confirm each human role maps to a named identity ref.
4. Check MFA status and session assurance posture.
5. Check least-privilege fit for each role.
6. Identify shared, stale, orphaned, or over-privileged roles.
7. Verify requester, reviewer, and approver separation.
8. Record findings in `governance.access_review`.
9. Create evidence refs for review completion or required changes.
10. Block or revoke ambiguous or conflicted privileged roles.

## Approval Requirements

- Privileged role continuation requires reviewer approval.
- Role escalation requires independent approval.
- Self-review is blocked.

## Evidence To Capture

- Access review ID.
- Subject refs reviewed.
- Role changes or confirmations.
- MFA/session posture.
- Separation check.
- Findings and required actions.
- Guardian decision and evidence refs.

## Rollback / Containment

- Revoke or suspend stale privileged roles.
- Mark identity as `review_required` or `blocked`.
- Block approval-required runtime actions when role posture is ambiguous.

## Escalation

Escalate to the security reviewer for identity ambiguity, self-approval,
conflicted review, or suspected account misuse.

## Done Criteria

- Review record is complete.
- Findings are resolved or explicitly blocked.
- Privileged roles have evidence-backed owner refs.
- Missing or ambiguous identity posture remains fail-closed.
