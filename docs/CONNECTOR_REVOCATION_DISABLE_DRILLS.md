# Connector Revocation Disable Drills

## Purpose

Define fail-closed metadata drill scenarios for connector revocation and
disable-switch verification before any future live connector implementation.

## Problem Statement

Individually valid connector records can drift apart. A connector may appear
usable in one record while consent, scope, or risk posture is revoked or
blocked elsewhere.

## Status

Design-only. Not implemented. No live connector behavior is enabled.

## Revocation Disable Graph

- `connector.readiness`
- `connector.scope_review`
- `connector.trust`
- `governance.connector_consent`
- `approval.binding`
- `guardian.decision`
- `tool.invocation`
- `evidence.artifact`
- `console.alert`
- `supervisor.health`

## Drill Scenarios

- connector revoked but tool invocation still requested
- consent revoked but readiness still approved
- scope overbroad after provider profile change
- disable switch missing
- revocation evidence missing
- token rotation placeholder missing
- provider risk elevated from medium to high/critical
- outbound action blocked
- cross-tenant connector ref
- prompt injection detected through connector payload

## Expected Fail-Closed Outcomes

- invocation state denied/blocked/failed_closed
- readiness or trust state downgraded to blocked/failed_closed
- connector lifecycle forced to disabled/revoked/blocked_mvp
- console alert emitted for operator visibility
- supervisor health reason includes degraded/blocked connector rationale
- no record may indicate live usability

## Evidence Requirements

Each drill result must carry:

- tenant-scoped correlation and connector IDs
- drill type and expected outcome
- actual outcome
- reason codes
- evidence refs
- completion timestamps (for completed drill outcomes)

## Operator Visibility

- connector-specific alerts for revocation, risk escalation, and disable-switch
  failures
- supervisor health surface for connector risk degradation
- traceability from drill result to readiness/scope/consent/trust records

Cross-contract reconciliation output is tracked by
`connector.reconciliation` records and linked operator drill posture in
[Connector Trust-Boundary Reconciliation Drill](runbooks/connector-trust-boundary-reconciliation-drill.md).

Acceptance posture and cadence impact are now tracked by
`connector.acceptance_score` and `connector.reconciliation_slo` records in
[Connector Provider Acceptance Scoring](CONNECTOR_PROVIDER_ACCEPTANCE_SCORING.md)
and
[Connector Reconciliation Propagation SLO](CONNECTOR_RECONCILIATION_PROPAGATION_SLO.md).
Source-of-truth ownership and escalation accountability are now tracked by
`connector.ownership` and `connector.escalation` records in
[Connector Source-Of-Truth Ownership](CONNECTOR_SOURCE_OF_TRUTH_OWNERSHIP.md).
Missing/stale/conflicted ownership posture is fail-closed.

## MVP Non-Goals

- no live connector implementation
- no OAuth/provider wiring
- no token storage or rotation runtime
- no external API calls
- no external sends/forms
- no browser automation
- no remediation execution
