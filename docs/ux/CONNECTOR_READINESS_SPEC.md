# Connector Readiness Spec

## Purpose

Define operator-facing metadata views for connector readiness, scope, consent,
revocation, and fail-closed posture.

## Status

Design-only UX metadata spec. No UI implementation.

## Required Panels

- Connector inventory by lifecycle/readiness status.
- Consent and scope-review linkage.
- Object/property authorization status.
- Prompt-injection and outbound policy posture.
- Revocation and rollback/disable drill state.
- Provider risk profile and revocation-drill posture state.
- Evidence and approval policy references.

## Required Fields

- `connector_id`, `connector_type`, `lifecycle_state`, `readiness_status`
- `connector_owner_ref`
- `consent_ref`, `scope_refs`
- `least_privilege_status`
- `object_authorization_status`, `property_authorization_status`
- `allowed_actions`, `blocked_actions`
- `approval_policy_refs`, `evidence_refs`, `revocation_refs`
- `provider_profile_ref`, `revocation_drill_refs`
- `connector_reconciliation_id` (from `connector.reconciliation` when present)
- `token_rotation_placeholder_status`
- `reason_codes`

## Fail-Closed UX Rules

- Missing consent/scope/evidence/revocation refs must display blocked state.
- Overbroad or missing authorization mapping must display failed-closed state.
- Blocked-MVP connector types/actions must show non-usable posture.
- UI metadata must not imply live execution, OAuth wiring, or token handling.
- Reconciliation drift classes must be visible and mapped to runbook guidance.
