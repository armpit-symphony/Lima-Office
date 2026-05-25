# Connector Provider Risk Profiles

## Purpose

Define metadata-only provider risk profiling posture and fail-closed gates that
must be satisfied before any connector can progress toward future live-lab
implementation planning.

## Status

Design-only. Not implemented. This document does not authorize live connector
execution, OAuth/provider wiring, token handling, or external API calls.

## Provider Risk Profile Model

Each provider profile is tenant-scoped metadata with:

- provider category and lifecycle status
- risk dimensions and normalized risk level
- revocation/disable-switch posture
- object/property authorization posture
- outbound and prompt-injection exposure posture
- export/delete impact posture
- evidence refs and reason-code traceability

Profiles are versioned policy records and must fail closed on missing or
ambiguous trust posture.

## Provider Categories

- `email`
- `calendar`
- `file_storage`
- `ticketing`
- `crm`
- `chat`
- `phone_text`
- `browser`
- `rmm_it`
- `cloud_provider`
- `payment`
- `legal_regulated`

## Risk Dimensions

- data sensitivity
- outbound capability
- object authorization
- property authorization
- token sensitivity
- revocation reliability
- rate-limit exposure
- prompt-injection exposure
- export/delete impact
- auditability
- tenant isolation

## Provider Risk Levels

- `low`
- `medium`
- `high`
- `critical`
- `blocked_mvp`

## Provider Lifecycle

- `profiled`
- `review_required`
- `approved_for_lab`
- `disabled`
- `revoked`
- `blocked_mvp`

## Fail-Closed Behavior

- Missing revocation method posture fails closed.
- Missing disable-switch posture fails closed.
- Missing object/property authorization mapping fails closed.
- Missing evidence for high/critical risk posture fails closed.
- Cross-tenant provider references fail closed.
- Prompt-injection or outbound-risk drift without review evidence fails closed.
- Blocked-MVP provider categories/actions remain non-usable metadata states.

## MVP Blocked Categories And Actions

Blocked categories for live use in MVP:

- `browser`
- `rmm_it`
- `cloud_provider`
- `payment`
- `legal_regulated`

Blocked actions in MVP regardless of category:

- external sends
- form submits
- customer-system mutation
- connector-admin mutation
- remediation execution

## Revocation And Disable Evidence Requirements

Provider risk posture transitions must include evidence refs for:

- revocation verification placeholder outcome
- disable-switch verification placeholder outcome
- scope-review impact after risk-level changes
- consent and Guardian/approval linkage for blocked outcomes
- console alert and supervisor health surfacing for degraded/blocked states

## Standards Alignment Notes

- OAuth 2.0 Security BCP RFC 9700: delegated-access least-privilege and
  revocation reliability posture (metadata-only in this phase).
- OWASP API Security Top 10: object/property authorization and unsafe API
  consumption risk modeling.
- NIST SP 800-207 Zero Trust: no implicit trust; policy and resource posture
  are required for each connector pathway.
- CISA Secure by Design: secure defaults and customer-visible fail-closed
  controls.
- NIST AI RMF: governed, mapped, measured, and managed AI-assisted connector
  behavior.

## Acceptance Gates Before Live Implementation

- Provider risk profile and revocation-drill contracts validate in CI.
- Risk-level and lifecycle transitions are evidence-linked and fail closed.
- Revocation/disable drills produce operator-visible alerts and health impact
  metadata.
- Consent/scope/readiness/trust/invocation/Guardian linkages are tested for
  drift detection.
- Live connector execution remains blocked until future approved runtime lanes.

Connector drift detection is further normalized by
[Connector Trust-Boundary Linkage Invariants](../CONNECTOR_TRUST_BOUNDARY_LINKAGE_INVARIANTS.md),
which adds reconciliation status + drift-class posture across provider and
connector governance records.

Risk posture is now also mapped into acceptance score and cadence posture via
[Connector Provider Acceptance Scoring](../CONNECTOR_PROVIDER_ACCEPTANCE_SCORING.md)
and
[Connector Reconciliation Propagation SLO](../CONNECTOR_RECONCILIATION_PROPAGATION_SLO.md).

Ownership/escalation accountability is now mapped via
[Connector Source-Of-Truth Ownership](../CONNECTOR_SOURCE_OF_TRUTH_OWNERSHIP.md),
which requires explicit owner/reviewer/escalation metadata for provider-profile
source-of-truth transitions.
