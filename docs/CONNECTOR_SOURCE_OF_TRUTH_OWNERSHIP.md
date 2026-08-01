# Connector Source-of-Truth Ownership

## Purpose

Define metadata-only ownership, accountability, and escalation posture for
connector governance records before any live connector implementation.

## Design-Only Status

- This is docs/contracts/tests/mock metadata hardening only.
- No live connector, OAuth/provider wiring, token runtime, API client, or
  runtime authorization behavior is implemented.

## Source-of-Truth Model

Connector governance is treated as a source-of-truth chain where ownership and
review accountability must remain explicit and tenant-consistent across linked
records.

## Ownership Roles

- `connector_owner`
- `scope_reviewer`
- `consent_approver`
- `revocation_owner`
- `disable_switch_owner`
- `evidence_reviewer`
- `security_reviewer`
- `customer_admin`
- `sparkpit_operator`

## RACI-Style Matrix

- Provider profile: owner `connector_owner`, accountable `security_reviewer`,
  consulted `scope_reviewer`, informed `sparkpit_operator`.
- Readiness: owner `connector_owner`, accountable `consent_approver`,
  consulted `security_reviewer`, informed `customer_admin`.
- Scope review: owner `scope_reviewer`, accountable `security_reviewer`,
  consulted `connector_owner`, informed `customer_admin`.
- Consent: owner `consent_approver`, accountable `customer_admin`,
  consulted `security_reviewer`, informed `sparkpit_operator`.
- Revocation drill: owner `revocation_owner`, accountable `security_reviewer`,
  consulted `disable_switch_owner`, informed `connector_owner`.
- Acceptance score/SLO: owner `security_reviewer`, accountable
  `sparkpit_operator`, consulted `evidence_reviewer`, informed `customer_admin`.

## Ownership Lifecycle

- `proposed`
- `assigned`
- `active`
- `stale`
- `transferred`
- `revoked`
- `blocked_mvp`

## Source-of-Truth Records

- `connector.provider_profile`
- `connector.readiness`
- `connector.scope_review`
- `governance.connector_consent`
- `connector.trust`
- `connector.revocation_drill`
- `connector.acceptance_score`
- `connector.reconciliation_slo`

## Stale Owner Detection

- missing owner/reviewer assignment for required records
- ownership record not reviewed within placeholder cadence window
- ownership refs drift from linked connector/provider IDs
- unresolved escalations linked to owner for overdue revocation/disable posture

## Escalation Triggers

- missing owner
- stale owner
- source-of-truth conflict
- SoD violation
- revocation overdue
- disable-switch accountability gap
- risk threshold exceeded with unresolved ownership review

## Escalation Paths

- owner -> security reviewer
- security reviewer -> sparkpit operator
- unresolved failed-closed path -> blocked_mvp posture and operator-visible alert

## Separation-of-Duties (SoD) Requirements

- owner and reviewer must be separable for high-risk connector classes.
- consent approver must not be sole reviewer for revocation-overdue paths.
- revocation owner and disable-switch owner must not self-clear failed drills
  without reviewer evidence.

## Evidence Requirements

- every stale/conflict/escalation path requires reason codes + evidence refs.
- active ownership requires owner/reviewer refs + evidence refs.
- transferred/revoked ownership requires explicit reason + evidence linkage.

## Operator Visibility

- ownership status and source-of-truth status must surface in
  `console.alert`/`supervisor.health` metadata.
- escalation references must be linked from ownership/readiness/provider paths.

## Fail-Closed Behavior

- missing/stale/conflicted ownership is fail-closed.
- SoD violation is fail-closed.
- missing revocation/disable accountability in overdue paths is fail-closed.
- ownership metadata must never authorize connector runtime actions.

## MVP Non-Goals

- no live connector implementation
- no OAuth/OIDC/SAML/provider wiring
- no token runtime or external API calls
- no runtime authorization expansion
- no durable service automation for ownership/escalation

## Defaults Linkage

Ownership/accountability posture is now linked to default-value and target
metadata contracts:

- `connector.defaults`
- `connector.slo_target`
- `connector.score_threshold`

This linkage supports fail-closed source-of-truth review without authorizing
runtime connector execution.
