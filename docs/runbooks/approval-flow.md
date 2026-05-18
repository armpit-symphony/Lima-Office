# Approval Flow Runbook

## Purpose

Handle a high-risk or privileged action request without bypassing Guardian.

## When To Use

Use for external sends, form submission, file delete/overwrite, customer record mutation, software install/update, remediation, sensitive data access, production server touch, or regulated system use.

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
6. Issue approval token with expiration, scope, and replay protection if approved.
7. Record denial reason if denied.
8. Attach approval result to evidence artifact.
9. Keep external writes blocked in Phase 0 unless future contracts explicitly approve them.

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

If approval scope is wrong, expire the token and deny execution. If suspicious activity appears, quarantine the worker or helper agent.

## Escalation

Escalate to security reviewer for high-risk ambiguity. Escalate to compliance reviewer for sensitive HR, finance, legal, medical, payment, or regulated actions.

## Done Criteria

- Approval or denial is recorded.
- Evidence exists.
- No blocked MVP action was approved.
- No action bypassed Guardian.
