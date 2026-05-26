# Connector Defaults and SLO Targets

## Purpose

Define Phase 1A metadata-only defaults for connector ownership, escalation, revocation/disable propagation targets, and acceptance thresholds before any live connector runtime exists.

## Status

Design-only contract and documentation hardening. Not implemented runtime behavior. This lane does not enable live connectors, OAuth/OIDC/SAML wiring, token handling, API clients, external sends, browser automation, remediation execution, or runtime authorization expansion.

## Default Ownership Value Model

- Owner assignment is required (`default_owner_required: true`) for all connector defaults.
- Reviewer assignment is required (`default_reviewer_required: true`) for all connector defaults.
- Approver assignment is required for high/critical defaults (`default_approver_required: true`).
- `source_of_truth_status` defaults to `missing` unless explicitly declared and verified by evidence-linked metadata records.

## Default Escalation Target Model

- Escalation targets are represented as placeholder SLO metadata only.
- Stale owner posture and unresolved escalation posture map to `stale`, `missed`, or `failed_closed`.
- Any missing owner/reviewer linkage for active-placeholder targets is fail-closed.

## Default Revocation/Disable Propagation Target Model

- Revocation propagation defaults to pending/not verified until evidence exists.
- Disable-switch verification defaults to pending/not verified until evidence exists.
- Missed propagation/verification posture must fail closed and produce reason codes plus evidence refs.

## Default Acceptance Score Threshold Model

Placeholder threshold fields:

- `approved_for_lab_min_score_placeholder`
- `review_required_min_score_placeholder`
- `degraded_max_failed_dimensions_placeholder`

Default acceptance posture remains `not_ready` unless threshold and evidence requirements are satisfied.

## Default Provider Category Risk Model

Provider categories are risk-tiered metadata (`low`, `medium`, `high`, `critical`, `blocked_mvp`) and must fail closed on ambiguity:

- high/critical categories require reviewer, approver, revocation, and disable-switch requirements.
- browser/rmm_it/payment/legal_regulated categories are blocked-MVP or approval-required placeholders only.

## Default Blocked-MVP Connector Category Model

Defaults for blocked categories:

- connector acceptance default is `not_ready`
- live connector default is `blocked_mvp`
- outbound action default is blocked without explicit approval and evidence
- blocked-MVP defaults cannot imply live provider execution

## Tenant Override Model

- `tenant_override_status` is explicit:
  - `not_allowed`
  - `review_required`
  - `approved_placeholder`
  - `denied`
  - `blocked_mvp`
- `approved_placeholder` overrides require evidence refs and reason codes.
- Missing evidence on override fails closed.

## SLO Placeholder Fields

- `owner_review_cadence_seconds_placeholder`
- `revocation_propagation_seconds_placeholder`
- `disable_switch_verification_seconds_placeholder`
- `stale_owner_escalation_seconds_placeholder`
- `reconciliation_cadence_seconds_placeholder`

These fields are placeholders for lab governance metadata only; no live enforcement is implemented.

## Evidence Requirements

- Required for high/critical defaults, override approvals, stale/missed/failed-closed SLO targets, and blocked outbound paths.
- Evidence links must include operator-visible refs and policy refs for review.

## Operator Visibility

Operator views should expose:

- provider category
- risk level
- default readiness/acceptance/lifecycle states
- override status
- SLO target status
- reason codes
- evidence refs

## Fail-Closed Behavior

Fail closed when:

- defaults are missing or ambiguous
- SLO targets are missing
- score thresholds are missing
- blocked-MVP category attempts live-ready posture
- override approval lacks evidence/reason codes
- high/critical defaults lack reviewer/approver/revocation/disable-switch requirements

## MVP Non-Goals

- live connector implementation
- OAuth/OIDC/SAML/provider wiring
- token storage/rotation runtime
- live API calls
- external send/form execution
- browser automation
- remediation execution
- durable storage/migrations/queues/web servers

## Future Implementation Gates

Before any runtime implementation:

1. Finalize tenant-specific numeric target values.
2. Finalize provider-category policy tables and blocked/approval-required boundaries.
3. Finalize override governance and SoD checks.
4. Finalize incident/escalation ownership and review cadence policy.
5. Pass contract, taxonomy, reason-code, and runbook evidence gates.

## Standards Alignment Notes

- NIST CSF 2.0 Govern: explicit ownership, accountability, escalation, and
  policy/evidence posture metadata.
- NIST SP 800-207 Zero Trust: no implicit connector trust; missing defaults or
  target metadata fails closed.
- OWASP API Security Top 10 (2023): explicit owner/scope/review posture and
  blocked unsafe outbound defaults.
- OAuth 2.0 Security BCP RFC 9700: revocation/disable posture and propagation
  targets are explicit, auditable metadata placeholders.
- CISA Secure by Design: safe-by-default blocked posture and operator-visible
  accountability metadata.
