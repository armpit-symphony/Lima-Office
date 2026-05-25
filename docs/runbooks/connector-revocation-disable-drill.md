# Connector Revocation Disable Drill

## Purpose

Provide an operator runbook for revocation and disable-switch drill validation
using metadata-only records.

## Status

Runbook posture only. No automated connector revocation/disable runtime is
implemented.

## When To Run

- new provider profile introduced
- provider risk level increases
- consent revoked or scope denied
- disable-switch or revocation verification drift suspected
- scheduled control validation cadence

## Prerequisites

- `connector.provider_profile` record exists
- `connector.revocation_drill` record scaffold exists
- related readiness/scope/trust/consent records exist
- reviewer roles assigned (security/compliance/operator)

## Drill Scenarios

- revocation verification
- disable-switch verification
- scope revocation
- token rotation placeholder verification
- outbound action blocking
- prompt-injection blocking
- cross-tenant reference blocking

## Operator Steps

1. Verify tenant, connector, provider profile, and readiness IDs.
2. Confirm current provider risk level and lifecycle status.
3. Confirm consent and scope-review linkage refs.
4. Execute metadata drill status transition (`planned` -> `running`).
5. Verify expected fail-closed outcome mapping.
6. Record actual outcome and reason codes.
7. Verify linked console alert and supervisor health posture.
8. Confirm drill completion evidence refs.

## Connector Records To Inspect

- connector.provider_profile
- connector.revocation_drill
- connector.readiness
- connector.scope_review
- connector.trust
- governance.connector_consent
- tool.invocation
- approval.binding
- guardian.decision
- evidence.artifact

## Revocation Verification Steps

- verify revocation method status is documented/verified placeholder
- verify revocation evidence refs are present
- verify readiness/trust records no longer indicate usable posture

## Disable Switch Verification Steps

- verify disable-switch status is documented/verified placeholder
- verify disable-switch failure paths mark failed_closed
- verify blocked actions remain blocked in invocation metadata

## Evidence To Capture

- drill record refs
- readiness/scope/trust/consent refs
- alert/health refs
- reason-code refs
- reviewer and completion timestamps

## Escalation

- security reviewer for authorization/scope drift
- compliance reviewer for evidence/export-delete impact ambiguity
- product scope guardian for MVP boundary violations

## Done Criteria

- drill record completed with evidence and reason codes
- fail-closed outcomes represented for blocked scenarios
- no record indicates live connector usability
