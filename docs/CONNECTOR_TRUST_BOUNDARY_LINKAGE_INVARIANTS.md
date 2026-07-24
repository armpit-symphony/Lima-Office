# Connector Trust-Boundary Linkage Invariants

Status: design-only metadata hardening. Not implemented runtime connector use.

## Purpose

Define fail-closed connector linkage invariants so provider, consent, scope,
readiness, trust, revocation-drill, invocation, approval, Guardian, evidence,
alert, and health records cannot drift into an unsafe combined posture.

## Problem Statement

Individually schema-valid connector records can still conflict:

- consent revoked while readiness appears approved
- scope overbroad while invocation is still requested
- provider risk critical while connector still appears ready
- revocation drill failed while connector remains enabled

Without cross-contract linkage invariants, these conflicts may evade simple
single-record validation.

## Why Individually Valid Contracts Can Still Be Unsafe Together

- schema checks are local to each contract payload
- connector decisions are distributed across provider/governance/Guardian/tool
  records
- risk posture changes can lag across related records
- authorization-adjacent metadata can appear internally valid while globally
  inconsistent

## Required Connector Linkage Graph

- `connector.provider_profile`
- `connector.readiness`
- `connector.scope_review`
- `connector.trust`
- `governance.connector_consent`
- `connector.revocation_drill`
- `connector.ownership`
- `connector.escalation`
- `tool.invocation`
- `approval.binding`
- `guardian.decision`
- `evidence.artifact`
- `console.alert`
- `supervisor.health`

## Canonical IDs

- `tenant_id`
- `connector_id`
- `provider_profile_id`
- `connector_readiness_id`
- `scope_review_id`
- `connector_consent_id`
- `revocation_drill_id`
- `connector_ownership_id`
- `connector_escalation_id`
- `tool_invocation_id`
- `approval_binding_id`
- `guardian_decision_id`
- `evidence_refs`

## Drift Classes

- `consent_revoked_but_readiness_approved`
- `scope_overbroad_but_invocation_requested`
- `provider_critical_but_ready`
- `revocation_drill_failed_but_connector_enabled`
- `disable_switch_missing_but_ready`
- `outbound_action_missing_approval`
- `tainted_connector_payload_used_for_tool`
- `connector_cross_tenant_linkage`
- `connector_evidence_missing`
- `connector_trust_revoked_but_guardian_allow`
- `connector_owner_stale_or_missing`
- `connector_source_of_truth_conflicted`
- `connector_sod_violation`

## Fail-Closed Reconciliation Rules

- Any cross-tenant connector linkage is `failed_closed`.
- Revoked consent cannot coexist with `approved_for_lab` readiness.
- Overbroad scope cannot coexist with requested connector invocation.
- Critical provider risk cannot coexist with ready state without evidence.
- Failed revocation drill cannot coexist with enabled/approved connector state.
- Missing disable-switch posture in ready state is `failed_closed`.
- Outbound connector action metadata requires approval-binding, Guardian
  decision, and evidence linkage.
- Tainted connector payload in privileged context is blocked.
- Trust-revoked connector posture cannot coexist with Guardian allow posture.
- Missing evidence refs in reconciliation is blocked/fail-closed.
- Missing/stale/conflicted ownership or SoD violations are blocked/fail-closed.

## Evidence Requirements

- `reconciled` outcomes require evidence refs.
- `drift_detected`, `revocation_pending`, `action_blocked`, `failed_closed`
  outcomes require evidence refs and reason codes.
- Revocation and disable drill outcomes must be linked through evidence refs.

## Operator Visibility

- Drift outcomes must surface in `console.alert` and `supervisor.health`.
- Connector-risk and reconciliation reason codes must map to runbooks.
- Visibility records remain metadata-only and non-authorizing.
- Reconciliation drift now also maps to `connector.acceptance_score` and
  `connector.reconciliation_slo` posture so stale/missed/pending propagation
  states fail closed.

## MVP Non-Goals

- No live connector implementation.
- No OAuth/OIDC/SAML/provider wiring.
- No token storage or token rotation runtime.
- No API client execution or external sends.
- No browser automation.
- No remediation execution.

## Future Implementation Gates

- Durable connector linkage storage and replay-safe state transitions.
- Real delegated-access revocation verification with provider-specific checks.
- Runtime authorization enforcement coupled to reconciled linkage status.
- Provider-specific abuse/rate-limit telemetry integration.
