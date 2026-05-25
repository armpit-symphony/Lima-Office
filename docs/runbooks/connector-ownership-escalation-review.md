# Connector Ownership Escalation Review

## Purpose

Review connector source-of-truth ownership and escalation accountability in a
metadata-only fail-closed posture.

## When To Use

- ownership assignment changes
- stale owner detection
- revocation/disable accountability drift
- SoD concerns
- failed-closed connector accountability events

## Prerequisites

- latest `connector.ownership` record
- latest `connector.escalation` record(s)
- linked provider/readiness/scope/consent/revocation/score/SLO records

## Owner Review Steps

1. Verify connector/provider/readiness IDs match linked ownership record.
2. Verify owner/reviewer/approver refs are present for active posture.
3. Verify evidence refs exist for current ownership state.

## Stale Owner Review

1. Check `ownership_status` and `source_of_truth_status`.
2. If stale/missing/conflicted, mark fail-closed and open escalation metadata.
3. Confirm alert + supervisor health linkage for visibility.

## Escalation Review

1. Validate escalation type/status pair is coherent.
2. Validate due-at placeholder, escalation owner ref, reason codes, evidence.
3. For resolved status, require `resolved_at` + evidence refs.

## SoD Review

1. Confirm separable owner/reviewer paths for high-risk connectors.
2. Confirm revocation/disable reviewer independence for failed/overdue paths.
3. If violated, set SoD violation and fail-closed state.

## Revocation/Disable Accountability Review

1. Confirm revocation owner exists for overdue revocation escalations.
2. Confirm disable-switch owner exists for disable-failed escalations.
3. If missing, enforce fail-closed and escalated posture.

## Evidence To Capture

- ownership + escalation refs
- reason codes and status transitions
- reviewer and approver refs
- linked console alert and supervisor health refs
- timestamps (`created_at`, `reviewed_at`, `acknowledged_at`, `resolved_at`)

## Escalation

- escalate missing/stale/conflicted ownership to `security_reviewer`
- escalate unresolved failed-closed paths to `sparkpit_operator`

## Done Criteria

- ownership state reconciled with linked records
- SoD posture captured and non-ambiguous
- escalation record status/evidence complete
- fail-closed state preserved where unresolved
