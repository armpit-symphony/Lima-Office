# Approval Flow Runbook

## Purpose

Handle a high-risk or privileged action request without bypassing Guardian.

## When To Use

Use for approval-required requests such as external-message drafts, form submission planning, file delete/overwrite requests, customer record mutation requests, software install/update requests, remediation requests, sensitive data access, or regulated system use.

Production server touch and remediation execution are blocked in MVP unless a future policy and contract explicitly authorize them.

## Prerequisites

- Task has Guardian classification.
- Risk tier is known.
- Approver role is assigned.
- Evidence capture is available.

## Steps

1. Review task, tenant, worker/helper identity, action class, and risk tier.
2. Confirm Guardian decision is `requires_approval`.
3. Confirm the action is not blocked for MVP.
4. Present scope, expected effect, rollback/containment, and evidence summary to approver.
5. Record approver identity.
6. Issue approval-token metadata with expiration, scope, and replay protection if approved and if the action is not blocked for MVP.
7. Record denial reason if denied.
8. Attach approval result to evidence artifact.
9. Keep external writes, live connector writes, remediation execution, and production server touch blocked in Phase 0 unless future policies and contracts explicitly approve them.

## Approval Requirements

Approver must have the right role for the action class. Breakglass is not defined in Phase 0 and remains an open question.

## Evidence To Capture

- Task ID.
- Tenant ID.
- Action class.
- Risk tier.
- Guardian decision ID.
- Approver identity.
- Approval token ID.
- Expiration.
- Approval or denial reason.
- Evidence artifact ID.

## Rollback/Containment

If approval scope is wrong, expire the token metadata and deny execution. If suspicious activity appears, quarantine the worker or helper agent.

## Escalation

Escalate to security reviewer for high-risk ambiguity. Escalate to compliance reviewer for sensitive HR, finance, legal, medical, payment, or regulated actions.

## Done Criteria

- Approval or denial is recorded.
- Evidence exists.
- No blocked MVP action was approved.
- No action bypassed Guardian.
- No production remediation, production server touch, live connector write, or external send was executed.
