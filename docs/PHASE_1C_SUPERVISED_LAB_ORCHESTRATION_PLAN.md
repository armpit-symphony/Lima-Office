# Phase 1C Supervised Lab Orchestration Plan

Date: May 26, 2026

## Purpose

Define the next planning lane after the frozen Phase 1B worker/task simulator
baseline, without implementing a supervisor orchestrator or widening runtime
behavior.

Snapshot note:
This planning document reflects pre-closeout planning posture at branch date.
Canonical Phase 1C baseline closeout and provenance posture is recorded in
`docs/PHASE_1C_CLOSEOUT.md`.

## Status

Planning-only. This document is not implementation approval.

## Current Baseline Summary

- Frozen simulator baseline branch:
  `integration/phase-1b-simulator-baseline` / `5925d2718f663e2ebd99504d00ef353b782e2dbe`
- Frozen simulator baseline tag:
  `lima-office-phase-1b-simulator-baseline`
- Independent baseline tag audit:
  `docs/audits/PHASE_1B_SIMULATOR_BASELINE_TAG_AUDIT.md` (`PASS WITH WARNINGS`)
- `main` remains untouched:
  `origin/main = e4bb6105a9d668ddffe21892da3aaff16a0d8ca0`

## What Exists Today

- Worker lifecycle simulator (`worker_lifecycle_simulator.py`) in-memory only.
- Task lifecycle simulator (`task_lifecycle_simulator.py`) in-memory only.
- Independent worker/task slice audits (`PASS WITH WARNINGS`).
- Frozen simulator baseline tag and independent gate audit.

## What Does Not Exist

- No supervisor lab orchestrator implementation.
- No runtime dispatch engine.
- No real task workers.
- No tool execution runtime.
- No live IO, live connectors, or external calls.
- No durable storage, queues, or databases.
- No background services, daemons, or schedulers.

## Proposed Future Supervised Lab Orchestration Concept

Future concept is a metadata-only supervisor lab orchestrator simulator that
evaluates compatibility between already-existing simulator states.

### Allowed Future Simulator-Only Interactions

- Read worker simulator metadata snapshots.
- Read task simulator metadata snapshots.
- Simulate a Supervisor decision envelope (metadata-only record).
- Validate state compatibility and fail closed on mismatch.
- Return metadata-only orchestration result (allow/deny/degraded/blocked).

### Blocked Future Interactions

- Real assignment to executable workers.
- Tool execution or dispatch of tool actions.
- Connector calls, model calls, or OAuth/provider flows.
- Filesystem persistence or durable state writes.
- Network calls or external APIs.
- Background loops, schedulers, daemons, or queue workers.

## Candidate Next Tiny Implementation Slices

### Option A: Supervisor Lab Orchestrator Simulator Only

- Purpose:
  simulate supervisor decision envelopes that read existing worker/task
  simulator metadata and return fail-closed orchestration metadata.
- Primary risk:
  accidental creep into dispatch, assignment, or execution semantics.
- Risk level:
  medium-high.
- Guard priority:
  highest; explicit fail-closed API boundaries required.

### Option B: Evidence Lifecycle Simulator Only

- Purpose:
  simulate metadata-only evidence lifecycle linkage checks
  (pre-action/post-action/denial-path integrity) without orchestrator coupling.
- Primary risk:
  adding pseudo-persistence semantics beyond in-memory metadata checks.
- Risk level:
  medium.
- Guard priority:
  high; no storage/no export execution.

### Option C: Guardian Replay Drill Simulator Only

- Purpose:
  simulate replay/expiry mismatch drill metadata sequencing only.
- Primary risk:
  accidental policy-authoritative behavior beyond drill semantics.
- Risk level:
  medium-low.
- Guard priority:
  high; no runtime authorization expansion.

### Option D: Pause And Audit/Merge Only

- Purpose:
  stop implementation and stabilize on audited simulator baseline.
- Primary risk:
  slower implementation cadence.
- Risk level:
  low.
- Guard priority:
  preserves baseline safety and clarity.

## Risk Analysis Summary

- Connecting worker/task simulators is the highest-risk boundary because it can
  drift into implicit dispatch semantics.
- Any "orchestration" naming can unintentionally imply scheduling or background
  behavior; contracts/runbooks must keep it request/response metadata-only.
- Denylist-only protections should be supplemented by strict allowlist state
  compatibility checks for future simulator interactions.
- Monotonic timestamp/idempotency hardening is still open and should be treated
  as a prerequisite for deeper orchestration simulation.

## Recommended Next Slice

Primary recommendation:

- **Option D (pause + audit/merge only)** as default until explicit approval for
  another tiny implementation slice.

If explicit approval is granted for one tiny slice, recommended order:

1. **Option B (evidence lifecycle simulator only)** first, to harden
   cross-contract evidence integrity before orchestration coupling.
2. Option A (supervisor lab orchestrator simulator only) only after Option B
   audit and explicit gate approval.

## Required Tests For Any Future Phase 1C Implementation Slice

- Explicit no-IO/no-network/no-storage/no-background assertions.
- Explicit no-tool-execution/no-real-dispatch assertions.
- Fail-closed tests for tenant mismatch, stale metadata, and incompatible worker
  or task states.
- Guardian/approval/evidence linkage mismatch denial tests.
- Timestamp/idempotency ambiguity fail-closed tests.
- Regression tests confirming worker/task simulators remain metadata-only.

## Required Audit After Any Phase 1C Implementation

- Fresh independent audit branch and audit document.
- Full validation suite pass with evidence recorded.
- Prohibited-behavior scan on changed implementation files.
- Explicit check that `main` remains untouched.

## Stop / Rollback Criteria

Stop and roll back to planning-only if any occur:

- runtime dispatch or tool execution behavior appears;
- any external IO/network/storage/background behavior appears;
- any connector/model/auth/remediation integration appears;
- fail-closed tests regress or become ambiguous;
- validation or audit gates fail.

## Explicit Non-Goals

- No supervisor orchestrator runtime implementation.
- No simulator wiring into executable runtime paths.
- No live connector, model-provider, or OAuth/provider integration.
- No token runtime, storage services, queues, web servers, or daemons.
- No remediation execution.
- No UI/frontend runtime behavior.
- No production-readiness or compliance-certification claim.
