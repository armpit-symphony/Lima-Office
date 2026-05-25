# Live Connector Readiness Review

## Purpose

Provide an operator review procedure for connector readiness metadata before any
future lab-live connector evaluation.

## Status

Runbook posture only. No live connector automation is implemented.

## When To Use

- New connector candidate introduced.
- Scope expansion requested.
- Consent/revocation posture changed.
- Prompt-injection or abuse risk reclassified.

## Prerequisites

- `connector.readiness` record exists.
- `connector.scope_review` record exists.
- Related `governance.connector_consent` record exists.
- Reviewer roles assigned (owner/security/compliance as required).

## Review Steps

1. Confirm tenant ID, connector ID/type, and lifecycle/readiness status.
2. Verify connector owner and reviewer refs are present.
3. Validate consent ref and consent status alignment.
4. Validate requested/approved/denied scope posture.
5. Confirm least-privilege status is `satisfied` before lab approval.
6. Confirm object/property authorization statuses are mapped and not missing.
7. Confirm `secrets_ref` only; reject any secret/token/key material fields.
8. Confirm prompt-injection policy refs and data-class mapping refs.
9. Confirm outbound action policy + approval policy refs for outbound-capable
   actions.
10. Confirm rate-limit policy and abuse-detection placeholder refs.
11. Confirm revocation refs and rollback/disable references exist.
12. Confirm export/delete impact refs and evidence refs.

## Revocation Drill

- Force lifecycle state to `revoked` metadata.
- Verify reason codes + revocation refs + evidence refs are present.
- Verify connector is non-usable and alert is emitted as blocked/degraded.

## Rollback/Disable Drill

- Force readiness status to `failed_closed` metadata.
- Verify reviewer notes and evidence refs capture the failure path.
- Verify no contract indicates live execution capability.

## Evidence To Capture

- Readiness record refs.
- Scope-review refs.
- Consent refs.
- Revocation and rollback drill refs.
- Reviewer and approval evidence refs.

## Escalation

- Security reviewer for scope/object/property authorization failures.
- Compliance reviewer for export/delete impact ambiguity.
- Product scope guardian for blocked-MVP boundary violations.

## Done Criteria

- Required refs and policy posture are complete.
- Fail-closed outcomes are represented for missing/overbroad states.
- No live connector behavior is implied or authorized.
