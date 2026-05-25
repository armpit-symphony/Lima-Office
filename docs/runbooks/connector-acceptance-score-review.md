# Connector Acceptance Score Review

## Purpose
Run a metadata-only review of connector acceptance scoring and reconciliation SLO posture before any future live-connector phase.

## When To Use
- new connector provider profile
- risk-level increase
- revocation/disable drill updates
- stale or missed reconciliation cadence
- readiness drift reported by reconciliation

## Prerequisites
- latest `connector.provider_profile`
- latest `connector.readiness`
- latest `connector.reconciliation`
- latest `connector.revocation_drill`
- current `connector.acceptance_score`
- current `connector.reconciliation_slo`

## Score Review Steps
1. Validate tenant and connector ID parity across linked records.
2. Confirm scoring record includes evidence refs and reason codes where required.
3. Confirm failed dimensions match known control gaps.
4. Confirm score status maps to fail-closed posture when drift/revocation is pending or missed.
5. Verify no score output is treated as runtime authorization.

## Threshold Interpretation
- `approved_for_lab`: metadata-complete planning posture only.
- `review_required`/`degraded`: continue remediation planning; block connector use posture.
- `revoked`/`failed_closed`/`blocked_mvp`: enforce blocked posture with alert + health updates.

## Revocation/Disable Checks
1. Confirm revocation propagation status is not `pending` or `missed` for lab-ready claims.
2. Confirm disable-switch verification status is not `missing` or `missed`.
3. Confirm evidence for revocation/disable updates is present and linked.

## Reconciliation Cadence Checks
1. Compare `last_reconciled_at` and `next_due_at`.
2. If stale/missed, require `reason_codes` and `evidence_refs`.
3. Verify linked acceptance scoring reflects blocked or failed-closed posture.

## Evidence To Capture
- linked contract refs
- scoring inputs and failed dimensions
- SLO state change evidence refs
- operator and reviewer identity refs
- alert + supervisor health references

## Escalation
- escalate to security reviewer on `failed_closed`, `revoked`, or repeated missed SLO.
- escalate to architecture owner for source-of-truth ownership conflicts.

## Done Criteria
- all required evidence captured
- score/SLO state reconciled with linked contracts
- fail-closed posture recorded where required
- next review timestamp placeholder recorded
