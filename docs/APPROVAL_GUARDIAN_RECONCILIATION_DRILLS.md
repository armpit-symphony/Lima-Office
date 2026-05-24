# Approval Guardian Reconciliation Drills

This document defines Phase 1A mock-only reconciliation drills for approval and
Guardian linkage in LIMA Office OS. It is docs/contracts/tests hardening only.
It does not add databases, queues, web servers, durable storage, live
connectors, external sends, remediation execution, or production runtime
expansion.

## Purpose

Define repeatable fail-closed drill scenarios that prove approval and Guardian
records cannot drift across contracts while still appearing individually valid.

## Problem Statement

Approval and Guardian records can each validate independently yet still be
unsafe together when IDs, tenant context, transaction linkage, replay metadata,
or evidence references disagree.

## Approval Guardian Linkage Graph

Required cross-contract graph:

1. `approval.chain`
2. `approval.binding`
3. `token.verification`
4. `guardian.decision`
5. `guardian.replay`
6. `replay.store.record`
7. `transaction.coordinator.event`
8. `transaction.boundary`
9. `evidence.ledger.entry`

The graph is metadata-only in Phase 1A and must fail closed on drift.

## Required ID Parity

Parity checks must be enforced for:

- `tenant_id`
- `customer_context_id` when present
- `task_id`
- `worker_id`
- `action_type`
- `tool_scope`
- `approval_chain_id`
- `approval_binding_id`
- `token_verification_id`
- `guardian_decision_id`
- `guardian_replay_id`
- `replay_record_id`
- `transaction_id`
- `evidence_refs`

## Drift Classes

The reconciliation taxonomy uses these classes:

- `missing_guardian_decision`
- `stale_guardian_decision`
- `mismatched_approval_binding`
- `mismatched_token_verification`
- `replay_record_missing`
- `replay_record_mismatch`
- `evidence_ref_missing`
- `coordinator_event_mismatch`
- `cross_tenant_linkage`
- `blocked_mvp_authorization_attempt`

Canonical reason-code mappings are defined in
[Reconciliation Reason Taxonomy](taxonomy/RECONCILIATION_REASON_TAXONOMY.md).

## Reconciliation Rules

- Reconciliation status is deterministic and fail-closed.
- Cross-tenant linkage always maps to blocked status.
- Stale, expired, contradictory, or ambiguous Guardian time metadata is blocked.
- Approval-binding and token-verification mismatches are blocked.
- Replay mismatch or missing replay records are blocked.
- Missing denial evidence on denied/replay-denied outcomes is blocked.
- Coordinator and transaction mismatches are blocked.
- Evidence ledger mismatch is blocked.
- `can_authorize` remains `false` in reconciliation helper output.

## Failure-Drill Scenarios

Required drills include:

1. Missing Guardian decision.
2. Stale or expired Guardian decision.
3. Approval binding mismatch.
4. Token verification mismatch.
5. Replay record missing or nonce mismatch.
6. Coordinator event or transaction mismatch.
7. Evidence ledger mismatch.
8. Cross-tenant linkage attempt.
9. Blocked-MVP authorization attempt.
10. Denial path missing evidence.

## Fail-Closed Behavior

- Any non-reconciled status blocks privileged action semantics.
- `external_send`, `live_connector_access`, and `lima_it_remediation` remain
  blocked in MVP.
- Reconciliation metadata is evidence-linked and denial-friendly; it is not an
  authorization token.

## Operator and Runbook Visibility

- Every drift outcome must be traceable to denial evidence references.
- Operator runbook entry point:
  [approval-guardian-reconciliation-drill](runbooks/approval-guardian-reconciliation-drill.md).
- Reconciliation drills are tabletop and metadata-only in this phase.

## MVP Non-Goals

- No real durable replay store.
- No real atomic transaction engine.
- No migration or storage rollout.
- No live export or delete pipeline.
- No live connector or external-send enablement.
- No remediation execution path.
