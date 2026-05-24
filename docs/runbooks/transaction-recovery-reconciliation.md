# Transaction Recovery And Reconciliation

## Purpose

Provide a fail-closed operator procedure for reconciling partial or ambiguous
transaction metadata in future durable replay/token/evidence flows.

This runbook is design guidance only. It does not implement a coordinator,
database, queue, or recovery service.

## When To Use

Use this runbook when any transaction-boundary/replay/token/evidence sequence
is incomplete, contradictory, or interrupted.

## Prerequisites

- Access to transaction metadata records for the affected tenant scope.
- Access to replay-store metadata records.
- Access to evidence-ledger and export-manifest metadata records.
- Operator approval role for containment actions.
- Incident tracking reference for the reconciliation activity.

## Failure Scenarios

- Replay nonce reserved but not consumed.
- Token consumed but evidence append failed.
- Evidence appended but transaction not committed.
- Export manifest prepared but delete conflict found.
- Coordinator crash mid-transaction.
- Duplicate idempotency key reported for same tenant scope.

## Steps

1. Confirm tenant, customer context, transaction ID, and correlation ID.
2. Set transaction posture to containment: no further side-effecting action
   attempts for that transaction scope.
3. Retrieve latest transaction-boundary record and ordered coordinator events.
4. Retrieve linked replay-store records, token-verification/binding records,
   and evidence-ledger refs.
5. Determine highest completed step in the expected sequence:
   `started -> preconditions -> replay reserve -> token verified ->
   pre-action evidence -> decision consumed -> post-action evidence -> terminal`.
6. If sequence is incomplete or contradictory, mark reconciliation started and
   capture reconciliation evidence refs.
7. Resolve outcome to one terminal state only:
   - `committed` when replay/token/evidence links are complete and coherent.
   - `rolled_back` when pre-action side effects must be discarded.
   - `failed_closed` when ambiguity remains or safety checks cannot be proven.
8. Record final reconciliation completed metadata with evidence refs and
   rationale.
9. Keep blocked posture for privileged actions until final state is recorded and
   reviewed.
10. Link all records to incident tracking and close only after reviewer signoff.

## Approval Requirements

- Containment and terminal-state selection require independent operator review.
- Self-approval is not allowed for privileged reconciliation decisions.
- Any proposed release from blocked/degraded posture requires explicit reviewer
  confirmation.

## Evidence To Capture

- Transaction-boundary record IDs and status timeline.
- Coordinator event IDs and transition checks.
- Replay-store record IDs and nonce status.
- Approval binding/token verification linkage refs.
- Evidence-ledger entry refs (pre-action, post-action, denial, rollback).
- Failure reason, operator decision, and reviewer confirmation refs.

## Rollback And Containment

- If preconditions or evidence are incomplete, prefer `failed_closed`.
- If pre-action metadata exists but commit cannot be proven, use `rolled_back`
  with rollback evidence.
- Never reopen a terminal transaction by mutating prior records; append new
  reconciliation metadata instead.

## Escalation

Escalate immediately when:

- tenant boundaries are unclear or conflicting;
- replay/token/evidence refs cannot be resolved;
- duplicate idempotency events indicate possible abuse;
- repeated reconciliation attempts fail to resolve ambiguity.

Escalation targets: security reviewer, compliance reviewer, and incident owner.

## Done Criteria

- A terminal transaction status is recorded (`committed`, `rolled_back`, or
  `failed_closed`).
- Reconciliation started/completed metadata exists with evidence refs.
- Containment posture and reviewer approvals are documented.
- No unresolved ambiguous state remains for the affected transaction scope.
