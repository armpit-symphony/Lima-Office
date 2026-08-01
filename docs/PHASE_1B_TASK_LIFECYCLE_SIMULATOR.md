# Phase 1B Task Lifecycle Simulator

Date: May 26, 2026

## Purpose

Implement the explicitly approved narrow Phase 1B slice: a task lifecycle
simulator only.

## Explicit Approval Scope

- In-memory Python simulation only.
- Deterministic task status transitions for `task.execution` metadata.
- Contract validation using existing runtime schema validation.
- Fail-closed behavior for invalid/unsafe transitions.

## Implemented

- New module: `lima_office/supervisor/task_lifecycle_simulator.py`.
- Uses `ContractValidator` with `task.execution` validation.
- Optional validation hooks for:
  - `guardian.decision` replay/expiry/scope checks
  - `approval.binding` and `token.verification` checks for approval-required paths
  - `worker.deployment` checks for assignment-ready worker posture
- Maintains current task state and transition history in memory only.
- Never authorizes or executes real actions.

## Not Implemented

- No task execution engine.
- No tool invocation runtime.
- No connector/model/remediation/runtime auth behavior.
- No network calls, external APIs, sockets, or services.
- No persistence, databases, queues, schedulers, daemons, threads, subprocesses, web servers, or UI behavior.

## Transition Matrix

Schema status source of truth: `contracts/v1/task.execution.schema.json`.

Allowed transitions in simulator:

- `task_created -> classified | blocked | denied | cancelled`
- `classified -> needs_approval | assigned_to_worker | blocked | denied | cancelled`
- `needs_approval -> assigned_to_worker | denied | timed_out | cancelled`
- `assigned_to_worker -> accepted | rejected | blocked | denied | cancelled`
- `accepted -> in_progress | blocked | denied | cancelled`
- `rejected -> assigned_to_worker | denied | cancelled`
- `in_progress -> draft_ready | completed_mock | blocked | failed | blocked_evidence_unavailable`
- `draft_ready -> completed_mock | blocked | failed | denied`
- `completed_mock -> evidence_recorded`
- `blocked_evidence_unavailable -> blocked | denied | cancelled`
- `blocked -> needs_approval | denied | cancelled`
- `failed -> cancelled`
- `timed_out -> cancelled`

No transition path is provided for `rolled_back` because `task.execution` does
not define that status in v1.

## Fail-Closed Rules (Guardian / Approval / Evidence)

- Unknown task, tenant mismatch, or unknown state fails closed.
- Invalid transition pair fails closed.
- Executable states fail without assignment-ready worker metadata.
- Approval-required executable states fail without valid `approval.binding` and
  `token.verification`.
- Executable states fail without a valid, non-stale, non-expired, replay-safe
  `guardian.decision`.
- Completion states fail without evidence refs.
- Blocked-MVP posture cannot enter executable/completion states.
- `approval_required_write` execution mode cannot enter executable states in this simulator.
- External-send/live-connector/remediation execution intent is blocked for MVP.

## Worker Lifecycle Dependency Boundaries

- Assignment/executable task states require `worker.deployment` metadata with:
  - matching tenant and `assigned_worker_id`
  - lifecycle in assignable posture (`active` or `enrolled`)
- Quarantined/revoked/retired/degraded worker lifecycle posture blocks
  assignment and execution transitions.

## Test Coverage

`tests/test_task_lifecycle_simulator.py` covers:

- schema-valid task examples
- safe end-to-end status path (task_created to completed_mock)
- denied/blocked/failed path checks
- invalid transition blocking
- blocked-MVP blocking
- worker-ref and worker-state blocking
- tenant mismatch and unknown task blocking
- approval-required metadata gating
- Guardian denied/stale/expired metadata gating
- evidence-required completion gating
- prohibited external-send/live-connector/remediation gating
- in-memory-only history behavior
- no file-write / no network / no tool execution / no real-action authorization

## Non-Goals

- No broader Phase 1B runtime expansion.
- No task dispatch execution implementation.
- No production-readiness or compliance-certification claim.

## Remaining Blockers

- Live connectors and OAuth/provider wiring remain blocked.
- Token runtime services remain blocked.
- Durable storage/transaction runtime remains blocked.
- Real model provider/local inference runtime remains blocked.
- Real IdP/MFA/session/device runtime auth remains blocked.
- Real attestation/verifier/signing/update runtime remains blocked.
- Export/delete runtime implementation remains blocked.
