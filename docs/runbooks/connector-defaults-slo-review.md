# Connector Defaults SLO Review

## Purpose

Review connector default-value metadata, placeholder SLO targets, and threshold metadata for fail-closed governance posture.

## When To Use

- before lab-phase connector readiness review
- after connector default policy changes
- after tenant override requests
- when SLO target status is `stale`, `missed`, `failed_closed`, or `blocked_mvp`

## Prerequisites

- latest `connector.defaults` record
- latest `connector.slo_target` record
- latest `connector.score_threshold` record
- linked owner/reviewer assignments
- evidence refs and reason codes

## Default Value Review

1. Confirm ownership/reviewer requirements are present.
2. Confirm high/critical defaults require approver/reviewer/revocation/disable-switch.
3. Confirm blocked-MVP categories do not imply live-ready actions.
4. Confirm outbound policy defaults to blocked without approval/evidence.

## Threshold Review

1. Verify placeholder threshold fields are present and versioned.
2. Verify required dimensions are non-empty.
3. Verify threshold status and reason codes align (`stale`/`failed_closed` require evidence).

## SLO Review

1. Verify placeholder SLO target fields are present:
   - owner review cadence
   - revocation propagation
   - disable-switch verification
   - stale-owner escalation
   - reconciliation cadence
2. Verify `active_placeholder` includes owner/reviewer/evidence refs.
3. For `stale`/`missed`/`failed_closed`, verify evidence + reason-code linkage.

## Tenant Override Review

1. Check `tenant_override_status`.
2. For `approved_placeholder`, require evidence refs and reason codes.
3. Fail closed if override evidence is missing or ambiguous.

## Evidence To Capture

- defaults record ref
- SLO target ref
- score-threshold ref
- owner/reviewer/approver refs
- policy refs
- reason-code set
- review timestamp and reviewer identity

## Escalation

- Missing defaults or thresholds: fail closed and escalate to security reviewer.
- Missed revocation/disable target: mark `failed_closed`, raise console alert, and escalate to SparkPit operator.
- Unresolved stale-owner posture: escalate from owner to reviewer to security reviewer.

## Done Criteria

- defaults, SLO targets, and thresholds are present and valid
- evidence and reason-code requirements satisfied
- blocked-MVP boundaries intact
- unresolved stale/missed states explicitly escalated
- no live connector/runtime authorization behavior introduced
