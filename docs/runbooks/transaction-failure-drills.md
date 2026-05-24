# Transaction Failure Drills (Tabletop)

## Purpose

Define tabletop drills that validate fail-closed readiness for future
transaction coordinator behavior across replay/token/evidence paths.

This document is mock/design-only and does not run production systems.

## Drill Format

For each drill:

- scenario
- expected fail-closed posture
- operator actions
- required evidence artifacts
- pass/fail criteria

## Drill 1: Replay-Store Outage

- Scenario: replay-store metadata cannot be read or written.
- Expected posture: transaction resolves to `failed_closed`; action blocked.
- Operator actions: contain scope, record outage evidence, run reconciliation.
- Evidence: failed-closed reason, incident ref, reconciliation events.
- Pass criteria: no action is authorized without replay certainty.

## Drill 2: Evidence-Ledger Outage

- Scenario: pre-action or post-action ledger append fails.
- Expected posture: pre-action failure blocks action; post-action failure enters
  degraded reconciliation path.
- Operator actions: classify stage, capture failure evidence, resolve terminal
  status.
- Evidence: evidence failure refs, terminal status ref, reviewer signoff.
- Pass criteria: no silent success without required evidence linkage.

## Drill 3: Duplicate Nonce Replay

- Scenario: second consume attempt for already consumed nonce.
- Expected posture: replay denied metadata, denial evidence, no new side effect.
- Operator actions: verify first-use record, confirm duplicate path, escalate if
  suspicious pattern repeats.
- Evidence: original consume ref, replay-denied ref, incident linkage if needed.
- Pass criteria: duplicate attempt never transitions to committed authorization.

## Drill 4: Token Verification Mismatch

- Scenario: approval token verification does not match action/binding scope.
- Expected posture: deny/fail-closed.
- Operator actions: compare binding/token/decision refs, capture mismatch cause,
  block action.
- Evidence: mismatch reason refs, failed-closed or denial event refs.
- Pass criteria: mismatch cannot authorize action or tool invocation.

## Drill 5: Cross-Tenant Idempotency Collision Attempt

- Scenario: same idempotency key attempted across tenant boundaries.
- Expected posture: tenant isolation; no cross-tenant collision effect.
- Operator actions: verify tenant-scoped idempotency namespace, capture audit
  refs.
- Evidence: transaction events from both tenant scopes, review decision.
- Pass criteria: one tenant cannot influence another tenant's transaction path.

## Drill 6: Export/Delete Conflict

- Scenario: export manifest prepared, then delete-preservation conflict appears.
- Expected posture: denied or blocked export posture with conflict refs.
- Operator actions: mark conflict, prevent export completion, route policy
  review.
- Evidence: delete conflict refs, blocked/denied manifest refs, review notes.
- Pass criteria: export does not proceed on unresolved conflict.

## Drill 7: Rollback Evidence Missing

- Scenario: rollback status set without required evidence refs.
- Expected posture: validation failure or failed-closed reconciliation.
- Operator actions: reject incomplete rollback record, capture correction path.
- Evidence: validation failure evidence, reconciliation events.
- Pass criteria: rollback cannot be accepted without evidence linkage.

## Drill 8: Partial Commit Ambiguity

- Scenario: some consume/evidence steps appear complete but commit status is
  absent or contradictory.
- Expected posture: reconcile then resolve to terminal state; ambiguous outcome
  fails closed.
- Operator actions: execute recovery sequence from transaction recovery runbook.
- Evidence: sequence comparison refs, final terminal-state evidence.
- Pass criteria: no ambiguous transaction remains open after drill completion.
