# Durable Replay And Evidence Posture

This document defines the Phase 1A design posture for future durable replay and
evidence controls in LIMA Office OS. This lane is docs/contracts/tests/mock-only
hardening. It does not add databases, queues, web servers, durable production
storage, live connectors, OAuth/provider wiring, external model APIs, external
sends, browser automation, or real remediation execution.

## Purpose

Define how future durable nonce/replay controls and evidence export controls
must behave before any side-effecting runtime expansion is allowed.

## Problem Statement

In-memory replay/evidence state is enough for deterministic tests but not enough
for concurrent lab execution or future production posture. Without durable
state, one-time approvals and one-time Guardian decisions can be reused after
process restart and denial-path evidence can be incomplete.

## Why In-Memory Is Insufficient

- In-memory nonce sets are process-local and reset on restart.
- Cross-worker concurrency cannot be represented atomically.
- Replay denials can be lost if evidence metadata is not recorded durably.
- Export/delete governance posture needs explicit conflict tracking metadata.

## Durable Replay Store Requirements

- Represent each decision nonce as a scoped replay record.
- Record tenant, task/action scope, Guardian decision, approval binding/token
  verification linkage, and evidence refs.
- Track nonce states: `reserved`, `consumed`, `replay_denied`, `expired`,
  `revoked`, `failed`.
- Track atomicity state: `pending`, `committed`, `rolled_back`,
  `failed_closed`.
- Fail closed when replay-store state is missing, ambiguous, or inconsistent.
- Model cross-record atomicity through `transaction.boundary` metadata before
  any durable implementation is approved.

## Atomic Nonce Consumption Requirements

- Reserve and consume must be one guarded transition in future runtime.
- Duplicate consume attempts must return replay denied without side effects.
- Consume failure must produce `failed_closed` metadata and denial evidence.
- Current lane simulates this behavior in memory only.

## Durable Approval-Token Consumption Requirements

- Approval-token consume posture must match Guardian replay posture:
  one-time, scoped, tenant-bound, task/action/tool-bound, and fail closed.
- Approval binding/token verification and replay record linkage must be exact.
- Any mismatch must deny and create denial-path evidence metadata.
- Approval-token consume transitions should be represented by
  `transaction.boundary` status and linked ledger entries.

## Guardian Replay Artifact Requirements

- Every replay check outcome needs metadata:
  valid first use, replay denied, expired, stale, revoked, scope mismatch,
  tenant mismatch, blocked MVP.
- Replay artifacts are refs-only metadata, never raw payloads or secrets.
- Replay-denied/stale/expired paths require denial evidence refs.

## Denial-Path Replay Artifact Strategy

- Denial paths are first-class outcomes in contracts and tests.
- Replay-denied outcomes must include mismatch reasons and denial evidence refs.
- Future runtime must make denial artifact creation part of the same guarded
  transition as deny/block decisions.

## Evidence Artifact Integrity

- Evidence artifacts carry hash metadata and chain-position metadata.
- Parent-child refs are explicit (`parent_evidence_refs`,
  `previous_artifact_id`, `chain_position`).
- Chain tenant mismatch fails closed in invariants/tests.
- Future append-only chain posture is modeled by `evidence.ledger.entry`
  metadata and hash-link fields.

## Evidence Hash Strategy

- Phase 1A uses metadata-only hash placeholders (`hash_algorithm`,
  `content_hash`, `payload_hash`).
- Future runtime must define canonical payload canonicalization and hash
  materialization details.

## Evidence Chain Parent-Child Refs

- Pre-action and post-action evidence refs are modeled separately.
- Denial-path evidence refs are modeled explicitly.
- Chain position > 1 requires parent refs and previous artifact linkage.

## Pre-Action Evidence

- Required before replay-authorized side-effecting classes in future runtime.
- Missing pre-action evidence fails closed and blocks action.

## Post-Action Evidence

- Records completion/degraded outcomes.
- Missing post-action evidence drives degraded/incident posture and blocks
  follow-on privileged actions.

## Denial Evidence

- Replay denied, stale, expired, revoked, and blocked-MVP outcomes require
  denial evidence refs where applicable.

## Evidence Export Posture

- Export manifests contain evidence refs only; no raw customer content.
- Export manifest requires redaction profile and retention placeholders for
  prepared/exported states.
- Delete/export conflicts are represented explicitly and fail closed when
  unresolved.

## Customer Exit/Delete Conflict Placeholders

- Delete conflict refs are mandatory for denied/blocked export decisions.
- Ambiguous conflict remains blocked until policy/runbook resolution.
- This lane does not implement delete execution.

## Redaction Before Export

- Redaction profile ref is required for prepared/exported manifests.
- Export manifests track included/excluded evidence refs and conflict refs.

## Raw Content And Secret Exclusion Rules

- `raw_content_included` must be `false` in MVP replay/evidence contracts.
- `secret_material_included` must be `false` in MVP replay/evidence contracts.
- Refs-only metadata is allowed; raw payloads/secrets are blocked.

## Retention Placeholders

- Export manifests include `retention_policy_refs`.
- Final retention periods remain unresolved governance blockers.

## Failure Behavior

- Replay-store unavailable or ambiguous state becomes `failed_closed`.
- `failed_closed` records require `failure_reason` and evidence refs.
- Failed-closed replay states cannot authorize action.

## Degraded Mode

- Allows diagnostics, evidence triage, and operator-visible review only.
- Blocks privileged side effects and external/runtime expansion.

## Fail-Closed Rules

- Missing/ambiguous replay or evidence metadata denies action.
- Scope, tenant, task, worker, action, binding, or verification mismatch denies.
- Raw-content/secret-included markers deny in MVP.
- Blocked-MVP action types remain denied/blocked.

## MVP Non-Goals

- No durable storage implementation.
- No queue implementation.
- No distributed lock service.
- No live export/delete service.
- No external connector/runtime side effects.

## Future Implementation Gates

Runtime expansion remains blocked until all of the following are approved:

- Durable replay store implementation.
- Durable atomic nonce and token consumption mechanism.
- Durable transaction coordinator/commit mechanism aligned to
  [RFC_DURABLE_TRANSACTION_STORAGE](rfcs/RFC_DURABLE_TRANSACTION_STORAGE.md).
- Durable evidence storage and export path.
- Durable storage architecture decision from
  [DURABLE_STORAGE_ARCHITECTURE](architecture/DURABLE_STORAGE_ARCHITECTURE.md).
- Final retention periods and redaction taxonomy.
- Final export manifest format and customer delete proof posture.
- Final RBAC/IdP/MFA/session/device trust matrix.
- Model-routing defaults.
- Attestation trust root.
- Signed update/rollback details.
- Live connector criteria.
