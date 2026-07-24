# Connector Revocation Runbook

## Purpose

Record connector consent revocation and keep live connector behavior blocked in
MVP.

## When To Use

- Connector owner requests revocation.
- Scope review fails.
- Prompt-injection risk is unresolved.
- Customer exit or delete request includes connector posture.
- Secret exposure or suspected misuse is reported.

## Prerequisites

- [Connector Consent Scope Revocation Policy](../governance/CONNECTOR_CONSENT_SCOPE_REVOCATION_POLICY.md)
- `connector.trust` record.
- `governance.connector_consent` record.
- Evidence refs.

## Steps

1. Confirm connector ID and tenant/customer context.
2. Confirm connector is mock/readiness-only.
3. Record connector owner and revocation requester refs.
4. Mark consent status revoked or blocked.
5. Confirm `live_access_enabled` remains false.
6. Confirm no secret material is present in records.
7. Record blocked scopes and prompt-injection review posture.
8. Check tasks, memory, evidence, and export/delete records for connector refs.
9. Capture revocation evidence.

## Approval Requirements

- Connector scope expansion requires independent review.
- Revocation can be requested by connector owner, security reviewer, operator,
  or customer exit reviewer.
- Live connector approval remains blocked in MVP.

## Evidence To Capture

- Connector consent ID.
- Connector trust ID.
- Revocation reason.
- Revoked-by ref.
- Revoked-at time.
- Scope and consent status.
- Evidence refs.

## Rollback / Containment

- Keep connector disabled or revoked.
- Block new tasks using that connector.
- Open incident review if secret exposure, prompt injection, or unauthorized
  scope is suspected.

## Escalation

Escalate to security reviewer for scope mismatch, prompt-injection risk, or
secret exposure. Escalate to compliance reviewer for exit/delete implications.

## Done Criteria

- Consent is revoked or blocked.
- Live access remains false.
- Evidence refs exist.
- Follow-up export/delete or incident work is linked.
