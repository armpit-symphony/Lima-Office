# Connector Trust-Boundary Reconciliation Drill

Status: runbook posture only. Not implemented automation.

## Purpose

Guide operators through connector linkage drift drills across provider, consent,
scope, readiness, trust, revocation, invocation, approval, Guardian, and
evidence metadata.

## When To Run

- after connector consent revoke/expiry changes
- after scope review downgrade (`overbroad`, `denied`, `failed_closed`)
- after provider risk elevation to `critical`
- after revocation/disable drill failure
- after connector-related blocked/failed_closed alert bursts

## Preconditions

- read access to connector/governance/Guardian/tool/evidence metadata records
- current reason-code taxonomy version is known
- no assumption of live connector behavior (this drill is metadata-only)

## Drill Scenarios

- consent revoked but readiness approved
- scope overbroad but invocation requested
- provider critical but ready
- revocation drill failed but connector still marked ready
- disable switch missing but connector ready
- outbound action requested without approval/Guardian/evidence linkage
- tainted connector payload requested for privileged tool path
- cross-tenant connector linkage mismatch
- trust revoked but Guardian allow
- missing evidence refs for drift/deny paths

## Operator Steps

1. Capture baseline snapshot refs for provider/readiness/scope/consent/trust/
   revocation/invocation/approval/Guardian/evidence.
2. Verify `tenant_id`, `connector_id`, and canonical refs match across records.
3. Check consent state against readiness and trust state.
4. Check scope review posture against invocation status.
5. Check provider risk posture against readiness/trust posture.
6. Check revocation drill status against enabled/readiness posture.
7. Check outbound invocation posture for approval-binding/Guardian/evidence
   linkage.
8. Check taint posture for privileged connector-requested actions.
9. Record reconciliation status and drift classes.
10. Confirm console alert and supervisor health records reflect blocked/drift
    posture.

## Records To Inspect

- `connector.provider_profile`
- `connector.readiness`
- `connector.scope_review`
- `connector.trust`
- `governance.connector_consent`
- `connector.revocation_drill`
- `tool.invocation`
- `approval.binding`
- `guardian.decision`
- `evidence.artifact`
- `console.alert`
- `supervisor.health`

## Evidence To Capture

- tenant-scoped correlation ID
- connector ID and reconciliation ID
- expected vs actual posture
- drift classes
- reason codes
- linked evidence refs
- completion timestamp and operator reviewer ref

## Expected Fail-Closed Outcomes

- invocation remains denied/blocked/failed_closed for drift states
- readiness/trust is downgraded to blocked/fail-closed posture
- no record indicates connector live usability
- console and supervisor surfaces show connector drift/block reasons

## Escalation

- security reviewer for consent/trust/revocation conflicts
- software architect for cross-contract linkage drift
- SRE/field IT reviewer for repeated drill failures or visibility gaps

## Done Criteria

- reconciliation outcome recorded with evidence refs
- all drift classes mapped to reason codes
- alert + health visibility confirmed
- unresolved connector drift states documented and escalated
