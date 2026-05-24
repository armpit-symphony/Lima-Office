# Cross-Contract Linkage Hardening

## Purpose
Define fail-closed linkage rules that keep durable transaction metadata coherent
across coordinator events, transaction boundaries, replay records, evidence
ledger entries, evidence artifacts, export manifests, approval bindings, and
Guardian decisions.

## Problem Statement
Individually schema-valid records can still be unsafe when references drift
across tenants, mismatched correlation contexts, stale idempotency keys,
incorrect nonces, or incomplete evidence chains.

## Why Individually Valid Contracts Can Still Be Unsafe Together
- A `transaction.coordinator.event` can be valid while pointing to replay or
  ledger refs that do not match a `transaction.boundary`.
- A `replay.store.record` can be valid while bound to the wrong transaction,
  wrong nonce, or mismatched action/tool scope.
- A ledger entry can be valid while referencing the wrong tenant artifact or an
  artifact outside the intended transaction/evidence chain.
- An export manifest can be valid while including refs that do not belong to the
  same tenant chain, or while delete/export conflicts are unresolved.

## Required Linkage Graph
- `transaction.coordinator.event`
- `transaction.boundary`
- `replay.store.record`
- `evidence.ledger.entry`
- `evidence.artifact`
- `evidence.export_manifest`
- `approval.chain`
- `approval.binding`
- `token.verification`
- `guardian.decision`
- `guardian.replay`

Every stage must be traceable with explicit relationship fields and fail-closed
linkage status.

## Canonical IDs
- `transaction_id`
- `coordinator_event_id`
- `replay_record_id`
- `ledger_entry_id`
- `artifact_id`
- `export_manifest_id`
- `binding_id`
- `approval_chain_id`
- `token_verification_id`
- `decision_id` / `guardian_decision_id`
- `replay_check_id` / `guardian_replay_id`

Canonical IDs are immutable once emitted. Rewrites are treated as drift.

## Tenant Consistency Rules
- `canonical_tenant_id` must match record `tenant_id`.
- Cross-tenant references are representable only as
  `linkage_status: mismatched_tenant` with failure reasons.
- Cross-tenant records can never be marked `linkage_status: linked`.

## Correlation Consistency Rules
- `canonical_correlation_id` must match the transaction-level correlation chain.
- Reconciliation may open a new correlation record only when explicitly linked
  to the original chain via related IDs and drift reasons.

## Idempotency Consistency Rules
- `canonical_idempotency_key` must remain stable for one transaction intent.
- Duplicate same-tenant/scope/idempotency combinations are tracked as drift or
  duplicate-detected paths; they cannot silently commit.

## Replay Nonce Consistency Rules
- `canonical_decision_nonce` must equal replay/decision nonce references.
- Consumed replay records require linked transaction and coordinator refs.
- Nonce mismatch is always fail-closed (`linkage_status: mismatched_nonce`).
- Approval chain, binding, token verification, Guardian decision, Guardian
  replay, and replay-store IDs must resolve to one canonical chain.

## Evidence Chain Consistency Rules
- Ledger entries and artifacts must share tenant and canonical linkage values.
- Parent-child links must remain append-only and monotonic.
- Non-denial ledger entries require artifact linkage; denial/replay-denial
  placeholders must still carry explicit drift/failure linkage metadata.

## Export Manifest Consistency Rules
- Included refs must be evidence refs only (`ev-*` style identifiers).
- Included refs must stay tenant-consistent with the manifest.
- Delete/export conflict states require explicit conflict refs and blocked or
  denied linkage status.
- Conflict and denial reasons should use canonical taxonomy codes so
  reconciliation and governance records do not drift by free-form text.

## Reconciliation Drift Detection
Drift is detected when terminal states disagree across linked contracts, such as:
- coordinator `transaction_failed_closed` while boundary is `committed`;
- replay record nonce marked `consumed` while coordinator reports failed-closed;
- export manifest prepared/exported while linked transaction failed or rolled
  back without reconciliation evidence.

## Negative-Path Examples
- Wrong `transaction_id` in coordinator event chain.
- Replay record linked to another tenant transaction.
- Nonce mismatch between replay record and Guardian decision.
- Ledger entry parent chain mismatch.
- Manifest including non-evidence refs or cross-tenant evidence refs.
- Delete/export conflict resolved as linked/committed without conflict evidence.

## Fail-Closed Rules
- `linkage_status` not equal to `linked` blocks authorization semantics.
- `mismatched_*`, `missing_ref`, and `drift_detected` require explicit
  `linkage_failure_reasons`.
- Committed paths require full linkage refs between coordinator, boundary,
  replay, and evidence chain components.
- Reconciliation drill states (`reconciliation_status`) must also fail closed
  unless `reconciled` with canonical IDs and evidence refs.

## MVP Non-Goals
- No durable storage engine implementation.
- No queue/service/migration/runtime transaction executor.
- No live connector/export delivery implementation.
- No customer payload or secret material in linkage metadata.

## Future Implementation Gates
- Durable atomic transaction coordinator and replay/token stores.
- Durable append-only evidence ledger and artifact/blob handling.
- Proven reconciliation tooling and operator runbooks.
- Final retention/redaction taxonomy and export package semantics.
- Signed update/rollback and trust-root posture.
