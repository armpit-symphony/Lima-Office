# Connector Consent Scope Revocation Policy

## Purpose

Define the governance requirements for connector consent, scope review,
least privilege, revocation, rotation placeholders, and prompt-injection
considerations.

Policy ref: `policy.connector_consent_scope_revocation.phase0`

Status: draft scaffold. Live connectors remain blocked.

Related design references:

- [Live Connector Criteria](../architecture/LIVE_CONNECTOR_CRITERIA.md)
- [Connector Provider Risk Profiles](../architecture/CONNECTOR_PROVIDER_RISK_PROFILES.md)
- [Connector Revocation Disable Drills](../CONNECTOR_REVOCATION_DISABLE_DRILLS.md)
- [Connector Trust-Boundary Linkage Invariants](../CONNECTOR_TRUST_BOUNDARY_LINKAGE_INVARIANTS.md)
- [Connector Source-Of-Truth Ownership](../CONNECTOR_SOURCE_OF_TRUTH_OWNERSHIP.md)
- [Live Connector Readiness Review](../runbooks/live-connector-readiness-review.md)

## Connector Consent Model

- Connector consent must identify tenant/customer context, connector owner,
  requested connector type, requested scopes, data class, and evidence refs.
- Consent records are metadata only.
- Consent cannot contain OAuth codes, tokens, cookies, API keys, or secret
  material.
- Missing consent blocks connector use.

## Scope Review

Scope review must classify requested access as:

- `read_metadata`.
- `read_content`.
- `draft_only`.
- `write_send`.
- `admin`.
- `regulated_or_sensitive`.

For MVP, live scopes remain blocked. Mock/readiness records may show requested
and blocked scopes for review.

## Least Privilege

- Request only the minimum scope needed for the documented workflow.
- Write/send/admin scopes require future explicit approval and threat-model
  review.
- Sensitive data scopes require data classification and redaction posture.
- Scope expansion requires a new review record.

## Secrets Ref Only

- Connector records use `secrets_ref` only.
- No secret material may appear in docs, contracts, logs, prompts, examples, or
  evidence summaries.
- `secret_material_present` must remain false for Phase 0 connector records.

## Connector Owner

Each connector requires:

- Connector owner identity ref.
- Security reviewer ref for live-candidate review.
- Scope reviewer ref.
- Revocation owner ref.
- Evidence refs.
- Ownership/escalation linkage refs where fail-closed accountability posture
  is active.

The connector owner cannot unilaterally approve scope expansion.

## Approval For Scope Expansion

Scope expansion requires:

- New Guardian decision.
- Updated consent/scope record.
- Independent approval where required.
- Prompt-injection review.
- Evidence refs.

Unknown, ambiguous, or stale scope posture fails closed.

## Revocation

Revocation requires:

- Revocation reason.
- Actor/ref that requested revocation.
- Effective time.
- Evidence refs.
- Follow-up review for tasks, caches, memory refs, and evidence export.

Revoked connectors cannot receive new tasks or scope expansion.

Revocation readiness now also requires:

- provider-profile linkage (`provider_profile_ref`)
- revocation-drill linkage (`revocation_drill_refs`)
- disable-switch posture metadata
- fail-closed reason/evidence when revocation or disable verification is missing

## Rotation Placeholder

Credential and token rotation are future implementation topics. This policy
requires rotation posture metadata only and does not implement rotation.

## Connector Data Class

Connector records must identify the highest expected data class:

- `public`.
- `internal`.
- `customer_confidential`.
- `sensitive_hr`.
- `sensitive_finance`.
- `sensitive_legal`.
- `sensitive_medical`.
- `secret`.

Sensitive connector data requires explicit approval or remains blocked.

## Prompt-Injection Considerations

- Email, docs, chat, browser, ticket, and file connector content is untrusted.
- Connector-handled content cannot directly authorize tool use, approvals,
  durable memory writes, external sends, or remediation.
- Prompt-injection review evidence is required before live connector review.

## Blocked Live Connector Behavior In MVP

The following remain blocked:

- OAuth/provider wiring.
- Webhooks.
- Live reads or writes.
- External sends.
- Connector tokens.
- Admin scopes.
- Production customer-system mutation.

## Acceptance Gates

- `governance.connector_consent` records consent, scope, revocation, and
  prompt-injection posture.
- `connector.provider_profile` and `connector.revocation_drill` capture
  provider-specific risk posture and revocation/disable drill outcomes.
- `connector.acceptance_score` maps consent/scope/revocation/risk/reconciliation
  dimensions into a fail-closed score status.
- `connector.reconciliation_slo` tracks reconciliation cadence and revocation/
  disable propagation placeholders; stale/missed/pending states block lab-ready
  posture.
- `connector.trust` remains mock/readiness-only.
- `connector.readiness` and `connector.scope_review` record lifecycle, least
  privilege, object/property authorization mapping, and fail-closed review
  status.
- Scope expansion cannot self-approve.
- Revocation creates evidence.
- Source-of-truth ownership and escalation conflicts require fail-closed
  `connector.ownership` / `connector.escalation` metadata.
- Missing consent, unknown scope, secret exposure, or prompt-injection
  unresolved state fails closed.
- Revoked consent must reconcile with readiness/trust/revocation-drill posture;
  conflicting states are treated as reconciliation drift and fail closed.
