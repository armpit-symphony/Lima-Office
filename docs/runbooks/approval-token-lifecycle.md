# Approval Token Lifecycle Runbook

## Purpose

Guide an operator through review, approval, denial, expiry, revocation, and evidence checks for privileged LIMA Office actions.

## Policy Traceability

- Policy ref: `policy.approval_token_lifecycle.phase0`
- Version: `policy-phase0-v1`
- Triggering contracts: `guardian.decision`, `approval.request`, `approval.token`, action-specific contract, `evidence.artifact`.
- Required fields: tenant/customer context, actor, task/action/resource refs, Guardian decision ID, approval request ID, approval token ID when issued, evidence artifact IDs, correlation ID.
- Fail-closed outcome: block action and revoke token when missing, expired, revoked, mismatched, reused, ambiguous, tainted, or unsupported by evidence.

## When To Use

Use this runbook when the operator dashboard shows:

- Approval request pending.
- Approval token issued, expired, revoked, mismatched, or reused.
- Privileged task blocked for missing approval.
- Worker quarantine requiring approval-token revocation.
- LIMA IT remediation request awaiting review.

## Prerequisites

- Confirm the request has tenant ID, customer context, task ID, action class, resource refs, risk tier, data classification, correlation ID, and Guardian decision ID.
- Confirm evidence for Guardian `requires_approval` exists.
- Confirm the action is not `blocked_mvp`.
- Confirm the requested scope is understandable and no broader than needed.

## Must Not

- Do not approve live connector writes, OAuth flows, external sends, customer-system writes, production remediation, or production server changes in Phase 0.
- Do not approve requests with missing evidence.
- Do not approve requests based on tainted content alone.
- Do not treat an approval token as a secret, bearer credential, or standing permission.
- Do not broaden scope during approval.

## Procedure

1. Open the approval request record.
2. Verify `guardian.decision` says `requires_approval`.
3. Compare request scope to task, action, tenant, resource refs, risk tier, and data classification.
4. Check for prompt-injection or tainted-source flags.
5. Check evidence artifact refs for request creation.
6. Decide one of:
   - Approve exact scope.
   - Deny.
   - Request a narrower superseding request.
   - Expire or cancel stale request.
7. If approved, ensure the token metadata is single-use, expiring, tenant/task/action/resource-bound, and linked to evidence.
8. If denied or expired, confirm no token was issued or that any existing token is revoked.
9. Record the approval result evidence.

## Approval Requirements

Approval requires an operator or approver role defined by policy. LIMA IT remediation also requires field IT reviewer or supervisor admin review until a future policy assigns the exact role.

Partial approval requires a new narrowed request or a token bound only to the approved subset. Ambiguous partial approvals fail closed.

## Evidence To Capture

- Guardian decision ID.
- Approval request ID.
- Approval result.
- Approval token ID if issued.
- Scope hash.
- Presented scope hash and approved scope hash when different.
- Approver identity ref and role.
- Approver role snapshot and approval channel placeholder.
- Expiry time.
- Denial or revocation reason.
- Whether tainted content was involved.
- Incident ID if replay, mismatch, or misuse is suspected.

## Containment / Rollback

If a token is missing, expired, revoked, reused, mismatched, ambiguous, or unsupported by evidence:

- Block the action.
- Revoke the token if present.
- Record evidence.
- Create or update an incident for replay, misuse, or suspicious repeated attempts.
- Quarantine the worker if the attempt came from a worker outside scope.

## Escalation

Escalate to security reviewer when:

- Replay or reuse is attempted.
- Scope mismatch occurs.
- Approval was requested from tainted content.
- Worker is quarantined.
- Evidence writer is unavailable.

Escalate to field IT reviewer when the request involves LIMA IT handoff or remediation.

## Done Criteria

- Guardian decision, approval request, approval result, and evidence refs are present.
- Approved token, if any, is scoped, single-use, expiring, and metadata-only.
- Denied/expired/revoked requests cannot execute.
- Correlation ID and tenant/customer context are recorded.
- No Phase 0 blocked action was approved.
