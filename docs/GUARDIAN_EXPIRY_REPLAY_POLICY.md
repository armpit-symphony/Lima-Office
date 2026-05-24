# Guardian Expiry And Replay Policy

This document defines the Phase 1A Guardian decision expiry and replay policy
for LIMA Office OS. It is docs, contracts, tests, and mock/in-memory hardening
only. It does not add live connectors, OAuth/provider wiring, external model
calls, external sends, browser automation, real remediation, durable services,
UI, production operations, or compliance certification claims.

## Purpose

Guardian decisions are not reusable authority. A decision can be unsafe when it
is copied across tenants, replayed after first use, used after expiry, used
before its effective time, widened to another tool scope, or paired with the
wrong approval binding.

Phase 1A makes Guardian decisions time-bounded, context-bound,
replay-resistant in memory for tests, and fail-closed when timestamps or scope
are missing or ambiguous.

## Threat Model

The policy addresses these misuse cases:

- stale decision replay after queue delay;
- one-time decision nonce reuse;
- worker or supervisor clock skew;
- future-issued or future-effective decision use;
- tenant, customer context, task, worker, action, or tool-scope substitution;
- approval binding or token verification mismatch;
- tainted input used as privileged intent;
- blocked-MVP action converted into an allow decision.

Detection is represented by `guardian.replay` records and evidence refs.
Durable replay storage, atomic distributed consumption, and incident thresholds
remain future work.

## Guardian Decision Lifecycle

1. Guardian evaluates policy and emits `guardian.decision`.
2. The decision records `issued_at`, `effective_at`, `expires_at`,
   `max_age_seconds`, `clock_skew_allowance_seconds`, `decision_nonce`,
   `decision_scope_hash`, binding refs, and evidence refs.
3. A requested mock action presents task, worker, action, tool scope, approval
   binding, token verification, evidence, and tenant metadata.
4. The mock replay verifier validates the decision and consumes the
   `decision_nonce` in memory for first use.
5. The verifier emits `guardian.replay` metadata for a valid first use.
6. Reuse, expiry, stale age, mismatch, taint, or blocked-MVP action raises a
   fail-closed runtime error in tests.

## Timestamp Rules

- `issued_at` is when Guardian created the decision.
- `effective_at` is the earliest time the decision may authorize a mock action.
- `expires_at` is the latest time the decision may authorize a mock action.
- `max_age_seconds` caps decision age even when `expires_at` is farther out.
- `clock_skew_allowance_seconds` is a bounded allowance for supervisor/worker
  clock differences.
- Missing, malformed, timezone-naive, contradictory, or ambiguous timestamps
  fail closed.
- `expires_at` must be after `effective_at`.
- `issued_at` or `effective_at` in the future beyond skew allowance fails
  closed.
- A decision older than `max_age_seconds + clock_skew_allowance_seconds` fails
  closed.

The Phase 1A mock default is 300 seconds max age with 30 seconds skew
allowance. These are test-policy defaults, not final operations thresholds.

## Replay Policy

Phase 1A authorizes only `replay_policy: one_time` in the mock runtime.
`bounded_window` is schema-visible for future policy review but is
non-authorizing in MVP. `deny_replay` and `blocked_mvp` never authorize action.

One-time decisions require:

- non-empty `decision_nonce`;
- `replay_status: unused`;
- `consumed_at: null`;
- `revoked_at: null`;
- a nonce not already consumed by the in-memory verifier.

The in-memory verifier is test scaffolding only. A future runtime lane must
define a durable replay store and atomic consume behavior before any
side-effecting runtime exists.

## Binding Model

A usable Guardian decision must match the requested action on:

- `tenant_id` and `customer_context_id`;
- `guardian_decision_id` / `decision_id`;
- `bound_task_id` when present;
- `bound_worker_id` when present;
- `bound_action_type`;
- `bound_tool_scope`;
- `decision_scope_hash`;
- `approval_binding_id` / `binding_id` when present;
- `token_verification_id` when present;
- evidence refs.

`guardian_decision_id` is required to equal `decision_id` in runtime
invariants. `approval_binding_id` mirrors the existing `binding_id` relation;
the invariant checks that both refer to the same approval binding when the
decision is approval-bound.

## Approval And Evidence Interactions

`approval.binding` remains the normalized approval-chain record. Guardian
expiry/replay checks add a second gate: the Guardian decision itself must still
be fresh, exact, one-time, and non-replayed when the approval-bound mock action
is presented.

`token.verification` can be valid only for the token check it records. It does
not override an expired, stale, replayed, or mismatched Guardian decision.

`evidence.artifact` refs are required for allow, denial, replay, expiry,
scope-mismatch, blocked-MVP, and taint outcomes. Guardian replay records are
metadata-only and must not contain raw customer content or secret material.

Phase 1A now also models a future durable replay-store posture through
`replay.store.record` and export posture through `evidence.export_manifest`.
These records remain metadata-only and mock-only. They do not implement durable
storage or export services.

Replay-denied, stale, expired, revoked, and blocked-MVP outcomes must carry
denial evidence refs where applicable. `failed_closed` replay-store atomicity
states cannot authorize action.

## Blocked-MVP And Tainted Input

The mock runtime blocks Guardian decisions for live connector access, external
sends, LIMA IT remediation, remediation-like actions, production touch,
unrestricted network/browser/file access, and other blocked-MVP action types.

Tainted or prompt-injection-suspected input cannot authorize privileged tool
use, durable memory write, external send, live connector path, or remediation.

## Fail-Closed Rules

Guardian decision validation fails closed when:

- decision is not `allow` or `allow_with_evidence`;
- decision ID fields disagree;
- nonce is missing, consumed, replayed, revoked, expired, or stale;
- timestamp is missing, ambiguous, future beyond skew, expired, or too old;
- tenant, task, worker, action, scope, approval binding, token verification, or
  evidence refs mismatch;
- requested tool scope exceeds the decision scope;
- action is blocked for MVP;
- input is tainted.

## MVP Acceptance Gates

- `guardian.decision` schema and examples include explicit expiry, nonce,
  replay, scope, binding, and evidence fields.
- `guardian.replay` schema and examples represent valid first-use, replay
  denial, expiry, scope mismatch, and blocked-MVP outcomes.
- `replay.store.record` schema and examples represent reserved/consumed,
  replay-denied, and failed-closed metadata states for future durable
  implementation gates.
- Mock helper consumes one-time decision nonces in memory only.
- Tests prove first-use success, replay denial, expiry denial, stale denial,
  missing expiry denial, future-effective denial, skew allowance, tenant/task/
  worker/action/tool-scope mismatch, scope hash mismatch, approval-binding
  mismatch, blocked-MVP denial, and evidence-required failure.

## Non-Goals

- No durable replay store.
- No distributed clock service.
- No durable atomic token or decision consumption.
- No live connector enforcement.
- No external send enforcement.
- No remediation execution.
- No database, queue, web server, UI, daemon, or scheduler.
- No production monitoring or compliance certification claim.
