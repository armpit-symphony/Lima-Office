# Phase 1C Evidence Lifecycle Simulator

Date: May 26, 2026

## Purpose

Implement the explicitly approved narrow Phase 1C slice: evidence lifecycle
simulator only.

## Explicit Approval Scope

- In-memory Python simulation only.
- Deterministic evidence lifecycle state transitions over validated
  metadata-only contracts.
- Fail-closed checks for task/Guardian/approval linkage and evidence integrity.

## What Was Implemented

- New module: `lima_office/evidence/lifecycle_simulator.py`.
- New simulator class: `EvidenceLifecycleSimulator`.
- Contract-backed validation using existing runtime `ContractValidator` for:
  - `evidence.artifact`
  - `evidence.failure`
  - `evidence.ledger.entry`
  - `evidence.export_manifest`
  - task/Guardian/approval/token metadata when provided for pre/post paths
- In-memory current-state and transition-history tracking only.
- Explicit blocked runtime methods for export, delete, tool execution, and real
  authorization.
- Registration hardening: new evidence records must start from `planned`.
- Transition hardening: same-state transitions are rejected fail-closed.
- State/contract intent hardening: lifecycle states enforce explicit evidence
  contract intent mapping.
- Reference semantics hardening: required lifecycle refs must be known
  in-simulator refs; unknown required refs fail closed.

## What Was Not Implemented

- No evidence storage runtime.
- No evidence file writes or persistence.
- No export runtime execution.
- No delete runtime execution.
- No background workers, schedulers, daemons, queues, or subprocesses.
- No network calls or external APIs.
- No connector/model/auth/remediation runtime expansion.
- No supervisor orchestrator implementation.

## Evidence Lifecycle Transition Matrix

Allowed:

- `planned -> pre_action_recorded`
- `pre_action_recorded -> post_action_recorded`
- `planned -> denial_recorded`
- `planned -> replay_denial_recorded`
- `planned -> failed_closed_recorded`
- `pre_action_recorded -> failed_closed_recorded`
- `post_action_recorded -> ledger_linked`
- `denial_recorded -> ledger_linked`
- `replay_denial_recorded -> ledger_linked`
- `failed_closed_recorded -> ledger_linked`
- `ledger_linked -> export_manifest_planned`

Blocked:

- `planned -> post_action_recorded` direct
- any runtime `exported` behavior
- any runtime delete/approved-delete behavior
- cross-tenant evidence-chain linkage
- raw-content or secret-bearing evidence metadata

## Fail-Closed Rules

- Reject unknown evidence IDs, unknown states, tenant mismatch, and invalid
  transitions.
- Reject non-`planned` initial registration states.
- Reject same-state transitions.
- Reject `raw_content_included: true` and `secret_material_included: true`.
- Reject malformed evidence refs and cross-tenant parent/child evidence chain
  linkage.
- Reject unknown required evidence linkage refs (denial/pre-action, chain,
  ledger-linked evidence refs).
- Enforce explicit state-to-contract pairing for lifecycle intent.
- Pre/post-action evidence states require valid task + Guardian metadata, and
  approval binding/token verification when task metadata is approval-required.
- Completion-class task metadata without evidence refs is blocked.
- Denial/replay-denial states require reason + denial evidence linkage.
- Export/delete executed-runtime postures are blocked in this simulator.

## Task / Guardian / Approval / Evidence Boundaries

- Pre/post transitions consume metadata-only contract records for consistency
  checks.
- Guardian replay/expiry/scope checks are reused from existing invariant
  functions.
- Approval-required metadata paths are fail-closed unless both
  `approval.binding` and `token.verification` pass validation and linkage.
- No task execution, tool execution, or dispatch is performed.

## Export/Delete Non-Goals

- `export_manifest_planned` is metadata planning posture only.
- Simulator never authorizes or performs export/delete runtime behavior.

## Test Coverage

`tests/test_evidence_lifecycle_simulator.py` covers:

- schema/example validation
- allowed transition paths
- blocked transitions
- tenant mismatch and cross-tenant chain blocking
- raw-content and secret-material blocking
- evidence-required completion linkage blocking
- denial/replay-denial linkage blocking
- no file-write / no network / no export-delete / no authorization behavior

## Remaining Blockers

- Supervisor orchestrator runtime remains blocked.
- Guardian replay drill simulator implementation remains blocked unless
  explicitly approved in a new slice.
- Evidence storage/export/delete runtime remains blocked.
- Durable transaction/replay/evidence storage remains blocked.
- Live connectors, OAuth/provider wiring, model calls, and remediation remain
  blocked.
