# Phase 1B Lab Runtime Plan

Date: May 26, 2026

## Purpose

Define a safe, narrow, future Phase 1B lab-runtime path without implementing it.

## Scope

This document is planning-only. It defines candidate scope, gates, acceptance
criteria, blockers, and stop criteria for a future tiny runtime slice.

## Status

Design-only / planning-only. Not implementation approval.

## Why Phase 1B Is Not Implementation Yet

- Independent audit result is `PASS WITH WARNINGS`, not implementation approval.
- Core blocked surfaces remain unresolved (live connectors, provider wiring,
  durable runtime storage/services, runtime authorization expansion).
- Safety patch disposition is still open and must be explicitly resolved.

## Current Baseline Summary

- Canonical integration baseline: `integration/phase-0-1a-baseline` at
  `26d5789ff62318ede69abf3296139eea7eaac8f0`.
- Audit branch checkpoint: `audit-independent-baseline-review` at
  `49c1030754387272b0b5cade1a144f436ab4cb84`.
- Baseline remains docs/contracts/tests/mock-hardening only.

## Audit Result Summary

- Result: `PASS WITH WARNINGS`.
- Warnings: side-branch provenance is not fully direct and some commit-pointer
  freshness follow-up remains.
- Main boundary outcome: planning-only is approved; implementation is not.

## Prerequisites

1. Integration baseline remains canonical and refreshed.
2. Safety patch disposition is documented and approved.
3. Validation suite is green on target branch.
4. No critical docs/contracts inconsistency remains open.
5. Phase 1B scope remains limited to mock-only, non-side-effecting behavior.

## Proposed Smallest Safe Future Runtime Slice

Future candidate (not approved by this branch):

- mock supervisor lab runner
- mock worker lifecycle simulator
- mock task lifecycle transitions
- mock Guardian decision replay validation
- mock approval binding verification
- mock evidence/replay/transaction metadata verification
- mock connector/model/attestation blocked-state verification

Hard limits for that candidate slice:

- no live IO
- no external calls
- no durable storage
- no background workers

## Explicit Non-Goals

- No live connector implementation.
- No OAuth/OIDC/SAML/provider wiring.
- No token runtime storage/rotation.
- No external API calls.
- No external sends, form submits, or browser automation.
- No remediation execution.
- No real model provider integration or local inference runtime.
- No real IdP/MFA/session/runtime authorization.
- No real TPM/verifier/signing/update runtime.
- No real export/delete runtime.
- No databases, queues, web servers, schedulers, or durable services.
- No UI/frontend runtime implementation.
- No production-readiness or compliance-certification claims.

## Blocked Surfaces

- live connectors
- provider wiring and token handling
- external message/send surfaces
- remediation and production-touch paths
- durable replay/transaction/storage runtime
- runtime authorization beyond mock lab invariants
- browser automation
- production operations claims

## Required Contracts

- `guardian.decision`
- `guardian.replay`
- `approval.request`
- `approval.result`
- `approval.token`
- `token.verification`
- `approval.binding`
- `task.execution`
- `worker.lifecycle`
- `worker.heartbeat`
- `model.route`
- `replay.store.record`
- `transaction.boundary`
- `transaction.coordinator.event`
- `evidence.artifact`
- `evidence.failure`
- `evidence.ledger.entry`
- `evidence.export_manifest`
- `supervisor.health`
- `console.alert`

## Required Tests

- fail-closed checks for replay, expiry, stale timestamp, nonce reuse
- fail-closed checks for approval binding mismatch and token mismatch
- fail-closed checks for tainted privileged paths
- fail-closed checks for blocked-MVP action classes
- fail-closed checks for missing evidence and linkage drift
- explicit assertions that helper/runtime paths do not authorize real actions
- explicit assertions that helper/runtime paths do not call live providers,
  live connectors, or external APIs

## Required Runbooks

- `runbooks/phase-1b-lab-runtime-drill.md`
- `runbooks/approval-guardian-reconciliation-drill.md`
- `runbooks/transaction-failure-drills.md`
- `runbooks/evidence-writer-failure.md`
- `runbooks/model-routing-review.md`
- `runbooks/health-taxonomy-review.md`

## Safety Gates

1. Independent audit pass on canonical integration branch.
2. Safety patch disposition complete and recorded.
3. Full validation suite pass with no new warnings in strict checks.
4. No live connector/provider/runtime IO behavior introduced.
5. No runtime authorization expansion beyond mock lab checks.
6. Fail-closed negative-path tests required for the proposed slice.
7. Explicit no-production/no-certification language remains present.

## Acceptance Criteria (Planning Lane)

- Phase 1B plan, gate checklist, and lab drill runbook are present.
- `NEXT_PHASE_PLAN` explicitly marks Phase 1B as planning-only.
- `OPEN_QUESTIONS` includes Phase 1B decision questions.
- `STATUS` reflects audit outcome and blocked implementation posture.
- Validation suite passes after doc updates.

## Stop / Rollback Criteria

Stop planning promotion to implementation if any of the following occurs:

- new runtime side-effecting behavior appears
- new live connector/provider/API capability appears
- validation gates regress
- safety patch disposition becomes ambiguous
- docs/contracts drift creates conflicting gate guidance

Rollback action for this lane:

- revert to planning-only docs posture
- re-run full validation
- reopen audit checklist and blockers

## Open Questions

- Should integration baseline be tagged/refrozen before any tiny implementation?
- Should first tiny slice be worker lifecycle simulator only, or task lifecycle
  transitions only?
- Must durable storage planning finish before any Phase 1B implementation?
- Is taxonomy-family hardening provenance sufficiently superseded, or should a
  dedicated reconciliation note be added first?

## Recommendation

Proceed with Phase 1B planning-only. Do not start implementation from this
branch. If a tiny slice is later proposed, require a separate gate approval
after safety patch disposition and fresh independent audit confirmation.
