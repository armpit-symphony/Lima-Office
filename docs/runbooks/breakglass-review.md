# Breakglass Review Runbook

## Purpose

Handle breakglass requests as blocked metadata in MVP and define the future
review trail required before any breakglass implementation can be considered.

## When To Use

- Operator asks for emergency access.
- Identity workflow is unavailable.
- Worker quarantine/revoke needs emergency review.
- Evidence preservation requires manual security review.

## Prerequisites

- [Breakglass Policy](../governance/BREAKGLASS_POLICY.md)
- [Approver Separation Policy](../governance/APPROVER_SEPARATION_POLICY.md)
- `governance.breakglass` record.
- Incident ref when the request is security-related.

## Steps

1. Confirm the request is not a runtime authorization.
2. Record requester identity ref and reason code.
3. Identify requested scope and blocked action classes.
4. Confirm MVP-blocked actions remain blocked.
5. Link incident ref when applicable.
6. Record Guardian denial or blocked-MVP decision.
7. Capture evidence refs.
8. Assign post-use or post-request review owner if future policy work is needed.

## Approval Requirements

- MVP breakglass receives denial or blocked metadata only.
- Future breakglass requires independent emergency approver, MFA posture,
  expiry, revocation, evidence, and post-use review.

## Evidence To Capture

- Breakglass record ID.
- Requester and emergency approver refs, if any.
- Reason code.
- Requested scope.
- Denial reason.
- Incident ref.
- Evidence refs.

## Rollback / Containment

- No access is granted in MVP.
- If a request indicates active risk, open or update an incident record.
- Quarantine or revoke affected workers through existing manual runbooks.

## Escalation

Escalate to the security reviewer for security incidents, identity compromise,
or attempted use of breakglass to bypass policy.

## Done Criteria

- Breakglass request is denied or blocked for MVP.
- Evidence exists.
- MVP-blocked actions remain blocked.
- Follow-up policy gaps are recorded in [Open Questions](../OPEN_QUESTIONS.md).
