# Live Connector Criteria

## Purpose

Define the metadata-only policy and acceptance gates that must be satisfied
before any connector can move from mock/planned posture toward future lab-live
evaluation.

## Status

Design-only. Not implemented. This document does not authorize any live
connector behavior.

## Connector Lifecycle

- `mock_only`: connector is metadata-only and non-executing.
- `planned`: connector candidate exists but has no consent/scope approval path.
- `consent_pending`: consent record exists but is not review-complete.
- `scope_review`: scope/object/property authorization review is active.
- `risk_review`: threat and abuse review is active.
- `approval_required`: reviewer separation and approval policy checks required.
- `approved_for_lab`: metadata-only readiness gate passed for lab planning.
- `live_blocked_mvp`: explicitly blocked for MVP execution.
- `revoked`: connector access posture revoked and blocked.
- `retired`: connector removed from active planning posture.

## Connector Categories

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

## Readiness Gates

Required before `approved_for_lab`:

- Tenant isolation and tenant-scoped IDs.
- Named connector owner.
- Consent record reference.
- Scope review references.
- Least-privilege review status.
- `secrets_ref` only (no secret material in contracts/examples/evidence).
- Token storage policy placeholder reference.
- Revocation path references.
- Audit/evidence references.
- Prompt-injection handling policy references.
- Data class mapping.
- Outbound action policy reference.
- Rate-limit policy reference.
- Abuse detection placeholder reference.
- Rollback/disable switch reference.
- Approval workflow policy references.
- Export/delete impact references.

## Blocked Connectors And Actions In MVP

Default blocked connector types for live use in MVP:

- `browser`
- `rmm_it`
- `cloud_provider`
- `payment`
- `legal_regulated`

Default blocked action classes for all connectors in MVP:

- external send/message execution
- form submission
- direct customer-system mutation
- remediation execution

## Fail-Closed Rules

- Missing consent, scope review, object/property authorization mapping, owner,
  revocation path, approval policy, or evidence references: fail closed.
- Overbroad scope or unknown scope class: fail closed.
- Unknown connector type or lifecycle state: fail closed.
- Any blocked-MVP connector/action posture: non-usable metadata state only.
- Secret values/API keys/tokens in payloads: fail closed.

## Standards Alignment Notes

- OAuth 2.0 Security BCP RFC 9700 concepts: delegated-access minimization,
  explicit scope governance, revocation readiness, and anti-token leakage
  posture (metadata-only in this phase).
- OWASP API Security Top 10 2023 concepts: object/property authorization
  mapping, unsafe API consumption controls, and excessive exposure prevention.
- NIST SP 800-207 Zero Trust: no implicit connector trust; verify per request
  context and policy.
- CISA Secure by Design: secure defaults, explicit customer-visible blockers,
  and fail-closed controls.
- NIST AI RMF: governed risk posture for AI-assisted connector actions.

## Evidence And Audit Expectations

- Every readiness transition requires evidence refs.
- Revocation requires reason codes + revocation evidence refs.
- Scope denial/overbroad outcomes require evidence refs and reviewer refs.
- Outbound-action eligibility requires explicit approval/evidence policy refs.

## Export/Delete Interaction

- Connector readiness records must carry export/delete impact refs when connector
  data classes touch retention/redaction governance.
- Unknown export/delete impact posture blocks readiness progression.

## Acceptance Gates Before Any Live Implementation

- Connector readiness and scope-review contracts validated in CI.
- Reason-code conformance gate includes connector reason-code checks.
- Revocation and rollback/disable drills documented and tested as metadata-only.
- Guardian/approval/evidence linkage documented and tested for connector paths.
- MVP block posture remains enforced for live connector execution.

## Provider-Risk Extension

This criteria is extended by
[Connector Provider Risk Profiles](CONNECTOR_PROVIDER_RISK_PROFILES.md) and
[Connector Revocation Disable Drills](../CONNECTOR_REVOCATION_DISABLE_DRILLS.md).

Additional pre-live requirements now include:

- provider risk profile records (`connector.provider_profile`)
- revocation/disable drill records (`connector.revocation_drill`)
- explicit provider profile linkage in readiness/scope/consent/invocation paths
- explicit drill evidence for revocation/disable/cross-tenant/prompt-injection
  fail-closed outcomes
