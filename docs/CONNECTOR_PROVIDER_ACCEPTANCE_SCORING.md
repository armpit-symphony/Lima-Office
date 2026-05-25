# Connector Provider Acceptance Scoring

## Purpose
Define a design-only, metadata-only acceptance scoring model for connector providers so Phase 0/1 reviews can fail closed before any live connector implementation.

## Design-Only Status
- This scoring model is not runtime enforcement.
- It does not authorize any connector action.
- It does not integrate OAuth/OIDC providers, tokens, APIs, or external sends.

## Scoring Model
- `overall_score` is an informational posture value only.
- `score_status` is the canonical decision output for posture:
  - `blocked_mvp`
  - `not_ready`
  - `review_required`
  - `approved_for_lab`
  - `degraded`
  - `revoked`
  - `failed_closed`
- `max_score` and `dimension_scores` provide transparent evidence for review and drift analysis.

## Acceptance Dimensions
- consent completeness
- scope least privilege
- object authorization
- property authorization
- revocation method
- disable switch
- token rotation placeholder
- prompt-injection exposure
- outbound action exposure
- rate-limit/resource controls
- export/delete impact mapping
- audit/evidence completeness
- tenant isolation
- provider risk level
- reconciliation drift status

## Score Bands
- `blocked_mvp`: connector type/action blocked by MVP policy.
- `not_ready`: baseline controls incomplete.
- `review_required`: actionable gaps remain; no lab-ready claim.
- `approved_for_lab`: metadata controls complete for lab planning posture only.
- `degraded`: previously acceptable posture regressed.
- `revoked`: provider/use path is revoked.

## Fail-Closed Scoring Rules
- Missing evidence in degraded/revoked/failed-closed status is invalid.
- Critical risk with missing review/evidence is `failed_closed`.
- Pending or missed revocation propagation blocks `approved_for_lab`.
- Unknown tenant/provider linkage must resolve to `failed_closed`.
- `overall_score` must never imply authorization.

## Score Mapping

### Score to Readiness
- `approved_for_lab` maps only to metadata readiness posture.
- `review_required`, `degraded`, `revoked`, `failed_closed`, `blocked_mvp` map to blocked/non-usable posture.

### Score to Console Alert
- `degraded` and `review_required`: warning/high severity.
- `revoked`, `failed_closed`, `blocked_mvp`: blocked severity.
- Alerts must reference evidence and linked contracts.

### Score to Supervisor Health
- `approved_for_lab`: does not imply healthy live connector execution.
- `degraded`: health degraded.
- `revoked` or `failed_closed`: health blocked.

## MVP Non-Goals
- no live connector calls
- no token issuance/storage/rotation runtime
- no OAuth/OIDC/SAML provider wiring
- no automatic external sends/form submissions
- no runtime authorization expansion

## Acceptance Gates Before Live Implementation
- finalized source-of-truth ownership
- finalized revocation/disable propagation SLOs
- finalized provider-by-provider safety criteria
- finalized legal/compliance review for connector data classes
- implemented and validated runtime controls (future phase)

## Ownership And Accountability Linkage
- scoring records should link `connector_ownership_ref` and
  `connector_escalation_refs` where available.
- stale/missing/conflicted ownership posture should force
  `score_status: failed_closed` or `review_required`.
- SoD violations must be reflected in score reason codes and evidence refs.
