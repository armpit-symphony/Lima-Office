# Connector Reconciliation Propagation SLO

## Purpose
Define design-only reconciliation cadence and revocation/disable propagation SLO placeholders for connector governance metadata.

## Reconciliation Source-of-Truth Ownership
- Owner placeholder: `security_reviewer` for risk posture and revocation integrity.
- Operator placeholder: `owner_operator` for execution tracking and evidence completion.
- Escalation owner placeholder: `supervisor` governance authority.

## Cadence Placeholders
- `planned`: cadence defined but not yet operating.
- `current`: cadence met for the latest interval.
- `stale`: exceeded expected interval.
- `missed`: required reconciliation did not execute in interval.
- `failed_closed`: metadata integrity or evidence prerequisites missing.
- `blocked_mvp`: blocked by MVP boundary.

Cadence is represented as metadata (`cadence_seconds_placeholder`, `last_reconciled_at`, `next_due_at`) and does not run automation in Phase 0.

## Revocation Propagation SLO Placeholders
- `not_required`
- `pending`
- `propagated`
- `missed`
- `failed_closed`
- `blocked_mvp`

`pending`/`missed` propagation must block connector lab-ready posture in linked acceptance scoring.

## Disable-Switch Verification SLO Placeholders
- `not_required`
- `pending`
- `verified_placeholder`
- `missed`
- `failed_closed`
- `blocked_mvp`

Missing or missed disable verification must fail closed for connector usability posture.

## Stale Detection
- stale readiness metadata
- stale consent/scope metadata
- stale provider profile metadata
- stale reconciliation metadata

Any stale path with privileged/outbound implications requires blocked or failed-closed posture.

## Failed Reconciliation Behavior
- Set linked reconciliation and scoring posture to `failed_closed`.
- Require reason codes and evidence refs.
- Emit operator-visible alert and supervisor health degradation/block.

## Operator Visibility
- Console alerts map to missed/stale/pending states.
- Supervisor health includes connector SLO drift reason codes.
- All state changes must include linked evidence refs.

## Evidence Requirements
- linkage refs for provider/readiness/reconciliation
- evidence refs for cadence and propagation status updates
- reason codes for stale/missed/failed-closed paths
- ownership/escalation refs when source-of-truth accountability is stale,
  missing, conflicted, or overdue

## Blocked-MVP Behavior
- `blocked_mvp` is terminal for live readiness.
- `blocked_mvp` status cannot be interpreted as passed propagation.

## Future Implementation Gates
- choose authoritative scheduler/execution plane
- define hard SLO targets and breach workflows
- integrate durable evidence lineage
- implement verified propagation instrumentation
- finalize connector owner/escalation owner accountability values per tenant
