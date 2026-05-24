# Durable Transaction Coordinator (Conceptual)

Status: design only. Not implemented.

This document defines a future transaction coordinator model for LIMA Office
OS. It is docs/contracts/tests/mock-hardening only and does not implement a
database, queue, service, migration, or durable storage runtime.

## Purpose

Define how future runtime should atomically bind:

- Guardian decision replay nonce consumption
- approval-token one-time consumption
- transaction-boundary status transitions
- evidence ledger append posture
- export/delete conflict decisions

The design goal is deterministic fail-closed behavior when any state is missing
or ambiguous.

## Coordinator Responsibilities

- Enforce a strict transaction state-transition model.
- Enforce immutable append-only event history.
- Enforce tenant-scoped idempotency and duplicate detection.
- Enforce ordered atomic protocol steps for replay/token/evidence.
- Emit denial/failure/reconciliation metadata on abnormal paths.
- Block authorization when commit state is ambiguous.
- Trigger reconciliation posture after partial failure or crash recovery.

## Non-Goals

- No coordinator service process implementation.
- No durable storage engine selection or integration.
- No queue, lock-manager, or distributed consensus implementation.
- No evidence blob persistence implementation.
- No export package generation implementation.
- No live connector, external send, remediation, or production operation path.

## State-Transition Matrix

Transaction lifecycle (future target):

- `planned -> pending -> committed`
- `pending -> rolled_back`
- `pending -> failed_closed`
- `planned|pending -> blocked_mvp`

Coordinator event flow (future target):

1. `transaction_started`
2. `preconditions_checked`
3. `replay_nonce_reserved`
4. `token_binding_verified`
5. `pre_action_evidence_appended`
6. `decision_consumed`
7. `post_action_evidence_appended`
8. `transaction_committed` or `transaction_rolled_back` or
   `transaction_failed_closed`
9. optional `reconciliation_started -> reconciliation_completed`

Allowed transitions are strict; out-of-order events fail closed.

## Immutability Rules

- Coordinator event records are append-only metadata.
- Existing event payloads cannot be mutated in place.
- `coordinator_event_id` is immutable and unique.
- `transaction_id` ownership is immutable per tenant.
- Terminal transaction states (`committed`, `rolled_back`, `failed_closed`,
  `blocked_mvp`) cannot transition back to `planned` or `pending`.

## Idempotency Model

- Every transaction uses one deterministic `idempotency_key`.
- `idempotency_scope` defines the protected namespace for that key.
- Duplicate requests with same tenant/scope/key:
  - return existing outcome if payload is equivalent, or
  - emit `duplicate_request_detected` metadata and deny new side effects.
- Ambiguous duplicate resolution fails closed.

## Tenant-Scoped Idempotency Key Strategy

Idempotency uniqueness scope is conceptualized as:

`(tenant_id, idempotency_scope, idempotency_key)`

Suggested `idempotency_scope` classes:

- `guardian_replay_consume`
- `approval_token_consume`
- `evidence_append`
- `export_manifest_prepare`
- `delete_request_review`

Cross-tenant key reuse is isolated and does not collide.

## Atomic Commit Protocol (Conceptual Sequence)

1. Reserve replay nonce metadata.
2. Verify approval binding/token linkage and status.
3. Append pre-action evidence metadata.
4. Commit Guardian decision consumption metadata.
5. Append post-action evidence metadata for success, or denial evidence
   metadata for denied/failed paths.
6. Mark transaction `committed`, `rolled_back`, or `failed_closed`.

If any step is missing/ambiguous, final state must be `failed_closed`.

## Rollback And Reconciliation Model

- Rollback is explicit metadata, not silent deletion.
- `rolled_back` requires rollback evidence refs.
- Reconciliation compares transaction boundary, replay record, token state, and
  ledger refs for consistency.
- Reconciliation emits explicit `reconciliation_started` and
  `reconciliation_completed` events.
- Unresolvable reconciliation ambiguity ends in `failed_closed`.

## Failure-Drill Matrix (Conceptual)

- Replay-store unavailable -> fail closed, denial evidence, reconciliation.
- Token verification mismatch -> deny/failed_closed with evidence.
- Pre-action evidence append failure -> block action and fail closed.
- Decision consumed but post-action evidence missing -> degraded + reconciliation.
- Coordinator crash mid-transaction -> reconciliation required before any reuse.
- Duplicate tenant-scoped idempotency key -> duplicate-detected path.
- Export prepared then delete conflict found -> blocked/denied export posture.

## Recovery After Partial Failure

- Load latest transaction/event metadata.
- Detect incomplete sequences.
- Reconcile replay/token/evidence links.
- Emit reconciliation events and evidence.
- Resolve to terminal state only (`committed`, `rolled_back`, `failed_closed`,
  `blocked_mvp`).

No partial transaction may remain silently pending.

## Duplicate Request Behavior

- Same tenant/scope/key with different transaction intent is denied and
  represented as `duplicate_request_detected`.
- Same tenant/scope/key with equivalent request may return prior result.
- Duplicate handling never authorizes a new external side effect in MVP.

## Replay Denial Behavior

- Replay attempt after first consume produces denial metadata and evidence refs.
- Replay denial must not mutate prior committed records.
- Replay denial outcome cannot authorize task or tool execution.

## Evidence Writer Failure Behavior

- Pre-action evidence write failure blocks action and fails closed.
- Post-action evidence failure triggers degraded/reconciliation posture.
- Evidence failure paths must produce explicit failure evidence refs.

## Export/Delete Conflict Behavior

- Export manifest preparation remains refs-only metadata.
- If delete/export conflict is detected, coordinator resolves to denied/blocked
  posture and records conflict refs.
- No delete/export execution is implemented in this lane.

## Audit And Evidence Expectations

- Every coordinator stage change should have evidence refs.
- Denial, rollback, and failed-closed outcomes require explicit evidence.
- Event chain must remain tenant-consistent and append-only.
- Raw customer content and secrets are excluded from coordinator events.

## Cross-Contract Linkage Requirements

- Coordinator and transaction/replay/ledger/artifact/manifest records include
  explicit related-ID linkage fields.
- `linkage_status: linked` requires complete references and empty
  `linkage_failure_reasons`.
- `missing_ref`, `mismatched_*`, and `drift_detected` remain fail-closed and
  evidence-linked.
- See [Cross-Contract Linkage Hardening](../CROSS_CONTRACT_LINKAGE_HARDENING.md)
  for the canonical linkage graph.

## MVP Blocked Items

- Real transaction coordinator service
- Durable storage engine implementation
- Migrations
- Distributed lock/consensus implementation
- Evidence blob storage
- Live export/delete execution
- Live connector-side effects
- Real remediation execution

## Future Implementation Gates

- Approved durable storage engine decision.
- Approved real atomic commit mechanism.
- Approved migration and backup/restore posture.
- Approved retention periods and redaction taxonomy.
- Approved export package format and delete-proof posture.
- Approved RBAC/IdP/MFA/session/device trust matrix.
- Approved attestation trust root and signed update/rollback details.
- Approved live connector criteria.

## Acceptance Gates Before Implementation

Before coordinator runtime implementation starts:

1. Coordinator event contract and examples validate.
2. Transaction/event transition tests prove fail-closed behavior.
3. Duplicate idempotency behavior is tenant-scoped and deterministic.
4. Runbooks for reconciliation and failure drills are approved.
5. Cross-contract docs explicitly map replay/token/evidence coupling.
6. Validation suite passes without regressions.
