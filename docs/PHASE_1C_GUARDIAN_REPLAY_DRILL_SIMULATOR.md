# Phase 1C Guardian Replay Drill Simulator

## Purpose

Define and test a narrow, in-memory Guardian replay drill simulator that
validates decision/replay metadata and enforces fail-closed replay controls.

## Explicit Approval Scope

This branch implements only the approved Phase 1C slice:
Guardian replay drill simulator only.

## What Was Implemented

- `lima_office/guardian/replay_drill_simulator.py`
- In-memory replay drill state tracking per `guardian_decision_id`
- Contract validation for:
  - `guardian.decision`
  - `guardian.replay`
  - `replay.store.record`
- One-time nonce reservation and consumption modeling
- Fail-closed transition checks for:
  - replay after consume
  - expired decision metadata
  - stale decision metadata
  - future-effective decision metadata beyond skew allowance
  - binding/token/action-scope mismatches
  - tenant mismatches
  - blocked-MVP decisions
  - missing denial/fail-closed evidence on required paths
- Planned-only registration enforcement
- Same-state transition rejection
- Duplicate nonce reservation blocking before consumption
- Structured mismatch category enforcement for `mismatch_denied`
- In-memory-only transition history

## What Was Not Implemented

- No real Guardian service
- No durable replay store
- No external nonce storage
- No network/API calls
- No file/database persistence
- No dispatch/tool execution
- No runtime authorization expansion

## Replay Drill Transition Matrix

Allowed:

- `planned -> decision_registered`
- `decision_registered -> nonce_reserved`
- `nonce_reserved -> first_use_validated`
- `first_use_validated -> nonce_consumed`
- `nonce_consumed -> replay_denied`
- `nonce_reserved -> expired_denied`
- `nonce_reserved -> stale_denied`
- `nonce_reserved -> mismatch_denied`
- `nonce_reserved -> blocked_mvp_denied`
- `nonce_reserved -> failed_closed_recorded`

Blocked:

- `planned -> nonce_consumed`
- `decision_registered -> nonce_consumed` (without reserve/validate path)
- `nonce_consumed -> first_use_validated`
- denial states back to usable states
- duplicate nonce consumption
- cross-tenant replay paths
- blocked-MVP decision use paths

## Timestamp, Expiry, and Skew Fail-Closed Rules

- Expired decisions fail closed.
- Stale decisions fail closed using max-age and skew fields.
- Future `effective_at` beyond skew fails closed.
- Contradictory decision timing metadata fails closed.

## Approval/Token/Evidence Boundaries

- For `first_use_validated`, bound decisions require corresponding
  `approval.binding` and `token.verification` payloads.
- Binding/token mismatches against decision/requested action fail closed.
- Denial and failed-closed paths require evidence linkage metadata.
- Missing required evidence on denial/fail-closed paths fails closed.
- Denial and failed-closed evidence refs are format-checked (`ev-` prefix)
  and fail closed when malformed.

## Non-Goals

- Real authorization grants
- Runtime dispatch
- Connector/model/remediation execution
- Production replay service behavior

## Test Coverage

`tests/test_guardian_replay_drill_simulator.py` covers:

- safe path and denial paths
- nonce replay/duplicate consumption denial
- expiry/staleness/future-effective timing failures
- tenant/binding/token/scope/worker mismatch failures
- blocked-MVP denial posture
- denial/fail-closed evidence requirements
- planned-only registration and same-state transition rejection
- execute-tools and authorization hard-block behavior
- no file/network/persistence/authorization behavior

## Remaining Blockers

- Durable replay store and atomic nonce consumption remain blocked.
- Supervisor orchestration runtime implementation remains blocked.
- Live connector/model/auth/runtime expansion remains blocked.

## Hardening Follow-Up

Audit warnings from `docs/audits/GUARDIAN_REPLAY_DRILL_SIMULATOR_AUDIT.md`
were addressed in branch `guardian-replay-drill-simulator-audit-hardening`
without adding runtime scope beyond this simulator.
