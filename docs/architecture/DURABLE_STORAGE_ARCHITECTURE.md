# Durable Storage Architecture (Conceptual)

Status: draft conceptual architecture. Not implemented.

This document defines a future storage architecture for durable replay/token
consumption and evidence export posture. It does not select a concrete storage
engine and does not implement databases, queues, services, or migrations.

## Purpose

Provide an architecture-level model for future durable transaction and evidence
storage behavior that remains consistent with Guardian-first, fail-closed, and
MVP-boundary constraints.

## Conceptual Components

- Replay Store
- Token Consumption Store
- Evidence Ledger
- Evidence Blob Store placeholder
- Export Manifest Builder
- Redaction Processor placeholder
- Audit Index

## Component Responsibilities

- Replay Store: durable nonce reserve/consume/deny/fail-closed metadata.
- Token Consumption Store: durable one-time approval-token consume metadata.
- Evidence Ledger: append-only, hash-linked metadata entries.
- Evidence Blob Store placeholder: protected payload-ref target (not defined in
  this pass).
- Export Manifest Builder: refs-only manifest generation.
- Redaction Processor placeholder: applies policy-driven exclusions/redactions.
- Audit Index: query support for operator/security/compliance review.

## Data Flow: Consume Path

```mermaid
flowchart TD
  A[Action Request] --> B[Guardian Decision Check]
  B --> C[Transaction Boundary Planned]
  C --> D[Replay Store Reserve/Consume]
  C --> E[Token Consumption Reserve/Consume]
  D --> F[Evidence Ledger Append Pre-Action]
  E --> F
  F --> G{All Preconditions Satisfied}
  G -- Yes --> H[Transaction Commit]
  G -- No/Ambiguous --> I[Transaction Failed Closed]
  H --> J[Post-Action Evidence Append]
  I --> K[Denial/Failure Evidence Append]
```

## Data Flow: Export/Delete Review Path

```mermaid
flowchart TD
  A[Export/Delete Request] --> B[Transaction Boundary Planned]
  B --> C[Audit Index Scope Query]
  C --> D[Redaction Processor Placeholder]
  D --> E[Export Manifest Builder]
  E --> F{Delete Conflict?}
  F -- No --> G[Prepared Manifest Metadata]
  F -- Yes --> H[Denied/Blocked Manifest Metadata]
  G --> I[Evidence Ledger Entry export_manifest]
  H --> J[Evidence Ledger Entry delete_review]
  I --> K[Transaction Commit]
  J --> L[Transaction Failed Closed or Denied]
```

## Trust Boundaries

- Supervisor transaction coordination boundary.
- Guardian and approval policy decision boundary.
- Ledger append boundary.
- Export/delete governance boundary.
- Tenant/customer-context isolation boundary.

Each boundary must preserve explicit evidence linkage and fail closed on
ambiguity.

## Storage Boundary Rules

- No cross-tenant data in transactional records.
- No raw customer content in transaction/ledger/export contracts.
- No secret material in contract metadata.
- Durable records are append-oriented; mutation is represented via new entries.

## No Implementation Selection Yet

This pass intentionally does not select:

- specific SQL/NoSQL engine
- object-storage provider
- queue technology
- lock manager
- migration framework

Selection requires a dedicated implementation RFC with threat model and failure
testing plan.

## Possible Future Storage Classes

- Local SQLite lab store (single-node lab durability).
- Server PostgreSQL store (multi-process concurrency control).
- Append-only object store (artifact/index separation).
- WORM-style evidence archive placeholder (immutability-focused retention
  posture).

## Tradeoffs

- SQLite: simple and local, weaker multi-writer coordination posture.
- PostgreSQL: stronger transactional semantics, higher operational complexity.
- Append-only object store: good archive durability, requires index consistency
  and chain-verification design.
- WORM-style archive: strong tamper-resistance goals, operational and cost
  complexity.

## Why No Storage Is Implemented In This Pass

- Phase objective is architecture/contracts/tests only.
- Final trust-root, RBAC/IdP/MFA, retention, and redaction rules are unresolved.
- Safe engine selection depends on final transaction and recovery requirements.
- Introducing real storage now would violate MVP scope and runtime boundaries.

## Deferred Implementation Gates

- Approved transaction coordinator design.
- Approved replay/token atomicity mechanism.
- Approved evidence blob strategy.
- Approved export package format.
- Approved delete-proof posture.
- Approved operational runbooks for backup/restore/recovery/rollback.
