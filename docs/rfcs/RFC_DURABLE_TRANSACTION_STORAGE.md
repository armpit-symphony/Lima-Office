# RFC: Durable Transaction And Storage Architecture

- RFC ID: `RFC_DURABLE_TRANSACTION_STORAGE`
- Status: `draft`
- Implementation status: `not_implemented`
- Scope: docs/contracts/tests/mock-hardening only

## Purpose

Define the future atomic transaction and durable storage posture for:

- Guardian replay nonce consumption
- approval-token consumption
- evidence-ledger append
- export-manifest preparation
- delete/export conflict tracking

This RFC does not implement storage engines, services, queues, or migrations.

## Problem Statement

Phase 1A currently proves fail-closed behavior with in-memory metadata only.
That is sufficient for deterministic tests, but insufficient for concurrent
multi-process execution and restart resilience.

Without durable transactional boundaries, the system cannot reliably guarantee:

- exactly-once consume semantics for one-time nonces/tokens
- durable denial-path evidence for replay/expiry failures
- append-only evidence chain continuity across restarts
- deterministic export/delete conflict decisions after partial failure

## Why In-Memory Replay/Evidence Is Insufficient

- Process-local state is lost on restart.
- Concurrent consumers cannot coordinate atomic reserve/consume.
- Partial failures can commit one record and lose another.
- Denial-path audit records can be skipped on exception-only flows.
- Recovery and replay reconciliation cannot be proven across nodes.

## Target Future Capabilities

- Atomic Guardian replay nonce consumption.
- Atomic approval-token consumption.
- Append-only evidence ledger posture.
- Export-manifest generation from evidence references.
- Delete/export conflict tracking with fail-closed decisions.
- Recovery from partial failures using durable transaction records.

## Non-Goals

- No storage engine selection in this RFC.
- No database, queue, or service implementation.
- No migration files.
- No live connector behavior.
- No external sends.
- No remediation execution.
- No production-readiness or compliance-certification claim.

## Trust Boundaries

- Supervisor transaction coordinator boundary.
- Guardian decision producer boundary.
- Approval workflow boundary.
- Evidence ledger writer boundary.
- Export/delete governance boundary.
- Tenant isolation boundary (one tenant at a time still requires explicit
  tenant/customer-context checks).

No component may bypass Guardian, approval, or evidence requirements.

## Storage Boundaries

Conceptual logical stores:

- Replay Store (nonce status and consume outcome).
- Token Consumption Store (approval-token one-time consume outcome).
- Evidence Ledger (append-only metadata chain).
- Evidence Blob Store placeholder (out of scope implementation).
- Export Manifest Store (refs-only metadata).
- Audit Index (query/index metadata only).

All stores are metadata-only at this phase and must exclude raw content and
secret material from contract records.

## Transaction Model

Future runtime transactions are represented by `transaction.boundary` records:

- `planned` -> `pending` -> `committed`
- `pending` -> `rolled_back`
- `pending` -> `failed_closed`
- `blocked_mvp` for actions outside MVP authority

Each transaction declares:

- participants
- required operations
- preconditions
- postconditions
- idempotency key
- evidence refs

Fail-closed requirement: if any required operation result is ambiguous, the
transaction must resolve to `failed_closed` with `failure_reason` and evidence.

## Idempotency Model

- Every transaction has a deterministic `idempotency_key`.
- Re-submission with the same key must return the same final transaction state
  or fail closed when state is ambiguous.
- Idempotency scope includes tenant, transaction type, and protected resource
  identifiers (nonce/token/evidence IDs).

## Replay Prevention Model

- Replay decision and approval token consumption are modeled as one-time state
  transitions with durable records.
- First valid consume transitions from reserved/pending to consumed/committed.
- Reuse attempts transition to replay-denied or failed-closed, never to
  consumed.
- Denial-path evidence must be generated and linked.

## Evidence Ledger Model

- Ledger entries are append-only metadata (`evidence.ledger.entry`).
- Each entry references chain parents and previous hash material.
- Chain position is strictly monotonic per tenant-scoped chain.
- Raw content and secret-material inclusion is always `false` in MVP contracts.

## Export Pipeline Model

1. Gather candidate evidence refs by tenant and authorized scope.
2. Apply redaction-profile placeholder rules.
3. Build refs-only export-manifest metadata.
4. Record transaction and ledger entries for prepare/export decisions.
5. Block when delete/export conflicts are unresolved.

No raw payload export implementation is included in this RFC.

## Redaction Pipeline Placeholder

The redaction processor is a conceptual component only:

- input: evidence refs and policy refs
- output: redaction decisions and excluded refs
- no raw secret/customer payload persistence in transaction contracts

Final taxonomy and implementation remain open governance items.

## Customer Exit/Delete Conflict Model

- Delete requests and export requests are distinct transaction types.
- Conflict detection output is represented by refs and conflict reason codes.
- Unresolved conflict requires `failed_closed` or denied/blocked manifest
  posture.
- No automatic delete execution is authorized in this phase.

## Failure Modes

- storage unavailable
- duplicate consume race
- stale/ambiguous precondition reads
- hash-chain linkage mismatch
- export-manifest build failure
- redaction placeholder unavailable
- delete conflict unresolved

## Recovery Behavior

- Recovery must reconcile transaction boundary state with replay/token/evidence
  records.
- Orphan pending transactions must resolve to committed, rolled_back, or
  failed_closed; never silently disappear.
- Recovery operations must emit evidence entries.
- Ambiguous recovery outcome must fail closed.

## Audit And Evidence Requirements

- Each transaction state transition produces evidence refs.
- Denial/replay-denied/failed-closed paths must produce explicit denial/failure
  evidence.
- Ledger entries must be tenant-consistent and hash-linked metadata.
- Export-manifest operations must remain refs-only.

## MVP Blocked Items

- durable storage implementation
- real transaction coordinator
- migration tooling
- blob/object store implementation
- queue/scheduler/service processes
- live connector/export/delete execution
- remediation execution

## Future Implementation Gates

- Approved durable storage design and threat model.
- Approved atomic transaction mechanism.
- Approved replay/token consume concurrency rules.
- Approved evidence blob and ledger integrity mechanism.
- Final retention periods and redaction taxonomy.
- Final export package format and delete proof posture.
- Final RBAC/IdP/MFA/session/device trust posture.
- Attestation trust-root and signed update/rollback posture.
- Live connector criteria and safety gates.

## Acceptance Gates Before Implementation

Before any storage/runtime implementation lane begins:

1. `transaction.boundary` and `evidence.ledger.entry` contracts validate with
   sanitized examples.
2. Cross-contract invariants explicitly fail closed on ambiguous transaction,
   replay, token, ledger, or export states.
3. Tests cover committed/rolled_back/failed_closed requirements and metadata-only
   constraints.
4. Docs and runbooks define recovery responsibilities and blocked-MVP posture.
5. Validation suite passes with no schema/link/test regressions.
