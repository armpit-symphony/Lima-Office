# Approval Token Runtime Binding

This document defines the Phase 1A approval-token runtime binding design for
LIMA Office OS. It is docs, contracts, tests, and mock/in-memory hardening
only. It does not add live connectors, OAuth/provider wiring, external model
calls, external sends, browser automation, real remediation, durable services,
UI, production operations, or compliance certification claims.

## Purpose

Approval records are not bearer capabilities. A valid-looking approval request,
approval result, token, token verification, Guardian decision, task, tool
invocation, or evidence artifact can be unsafe if it is copied across tenants,
replayed, widened, used after expiry, used by the wrong worker, or used for a
different action.

The binding model makes the approval chain explicit and fail-closed.

## Approval Chain

The approval chain is:

1. `approval.request`: records the requested tenant, task, requester, Guardian
   decision, requested action, requested scope, approver roles, expiry, and
   evidence.
2. `approval.result`: records the approve, deny, expired, cancelled,
   superseded, partial, or blocked-MVP outcome.
3. `approval.token`: records metadata for a scoped, one-time token. It never
   stores bearer token material or secrets.
4. `token.verification`: records the Guardian/supervisor verification result.
5. `approval.binding`: normalizes the exact runtime binding across request,
   result, token, verification, Guardian, task, tool, worker, tenant, scope,
   nonce, evidence, and policy snapshot.
6. `guardian.decision`: remains the syscall gate and must match the binding,
   expiry window, decision nonce, and replay policy.
7. `guardian.replay`: records the metadata-only replay check outcome for the
   Guardian decision. It does not authorize execution by itself.
8. `replay.store.record`: records future durable nonce/atomicity posture as
   metadata-only scaffolding for consume/replay decisions.
9. `transaction.boundary`: records future atomic consume/append/export boundary
   metadata for commit/rollback/fail-closed outcomes.
10. `evidence.ledger.entry`: records append-only metadata chain entries for
   consume, denial, rollback, and export events.
11. `evidence.export_manifest`: records refs-only export posture and delete
   conflict placeholders; it does not implement export/delete services.
12. `task.execution` and `tool.invocation`: may proceed only in mock/dry-run
   paths when the binding matches.
13. `evidence.artifact`: records approval, denial, verification, consumption,
   replay denial, mismatch, and blocked-MVP evidence by reference only.
    Reason codes should use canonical taxonomy registries to avoid drift across
    approval, Guardian replay, and governance conflict records.
14. Cross-contract linkage fields and `linkage_status` fail-closed semantics
   bind coordinator/boundary/replay/ledger/artifact/manifest metadata to the
   same canonical transaction context.
15. Reconciliation status fields and canonical approval/Guardian IDs provide a
    second fail-closed layer for approval/Guardian drift drills.

`approval.chain` examples summarize safe and unsafe combinations for validation
and review. They are example bundles, not runtime authorization records.

## Binding Model

`approval.binding` ties together:

- `tenant_id` and `customer_context_id`.
- `task_id`.
- `action_type`.
- `tool_scope` with resource refs, allowed operations, and prohibited
  operations.
- `worker_id` where the action is worker-bound.
- `requester_ref` and `approver_ref`.
- `approval_request_id`.
- `approval_result_id`.
- `approval_token_id`.
- `token_verification_id`.
- `guardian_decision_id`.
- `evidence_refs`.
- `correlation_id`.
- `approval_chain_id` and `binding_id`.
- `token_use_policy`.
- `nonce_ref`.
- `policy_version` and `policy_snapshot_hash`.
- `requested_scope_hash` and `approved_scope_hash`.

The mock verifier refuses to authorize when any requested tenant, customer
context, task, worker, action, tool scope, Guardian decision, token
verification, policy snapshot, approval chain, binding, or evidence ref does
not match.

The mock reconciliation helper classifies linkage as `reconciled`,
`missing_ref`, `mismatched_binding`, `stale_decision`, `replay_mismatch`,
`evidence_missing`, `coordinator_mismatch`, `cross_tenant_blocked`, or
`blocked_mvp`. All non-`reconciled` outcomes remain fail-closed.

Guardian decisions have their own expiry/replay gate in
[Guardian Expiry And Replay Policy](GUARDIAN_EXPIRY_REPLAY_POLICY.md). A valid
approval binding cannot override an expired, stale, replayed, revoked, tainted,
or mismatched Guardian decision.

## Token Lifecycle States

The binding states are:

- `pending`: request exists but binding is not usable.
- `bound`: one-time, non-replayed, unexpired mock/dry-run binding.
- `consumed`: one-time binding was used and evidenced.
- `denied`: approval was denied and no usable token exists.
- `expired`: token or binding expired.
- `revoked`: token or binding was revoked.
- `mismatched`: tenant, task, worker, tool, scope, Guardian, token, or evidence
  mismatch was detected.
- `blocked_mvp`: the action class is blocked for MVP and cannot issue a usable
  token.

## One-Time Use

Phase 1A accepts only `token_use_policy: one_time` for `bound` approvals.
`bounded_window` remains represented as future/denied metadata and cannot be a
valid MVP authorization path.

The mock `ApprovalBindingVerifier` tracks consumed nonce refs in memory for
tests. This is not durable replay protection. Future runtime work still needs a
durable atomic consume design before any real side-effecting action exists.

## Replay Prevention

A replay attempt fails when:

- the binding nonce was already consumed by the in-memory verifier;
- the binding status is `consumed`, `expired`, `revoked`, `mismatched`,
  `denied`, or `blocked_mvp`;
- the requested action uses a different tenant, task, worker, action, tool
  scope, token verification, Guardian decision, or evidence ref;
- the requested tool scope is wider than the approved scope.

Replay denial must produce evidence. Repeated or suspicious replay attempts
should become an incident in a future runtime lane.

## Expiry And Revocation

The binding must have `expires_at` for `bound` use. The mock verifier denies
bindings checked after expiry, and it denies revoked bindings. Guardian
expiry/replay policy now defines mock/in-memory timestamp, nonce, scope, and
clock-skew checks. Durable replay storage, distributed idempotency, and
non-test operations thresholds remain open.

## Blocked-MVP Handling

`external_message_send`, live connector access, software install/update,
remediation, LIMA IT remediation, production server touch, and regulated-system
use cannot become usable approval bindings in MVP. The schema forces these
action types to `blocked_mvp` with no usable token or token verification.

Dry-run or draft review can be represented as
`draft_external_message_review`, but that does not authorize a live external
send.

## Tainted Input

Untrusted, suspected, or confirmed taint cannot authorize a privileged binding.
Tainted chains must deny or block and must carry taint refs as evidence-linked
metadata. Tainted content may be reviewed as data; it cannot become fresh
operator intent, tool arguments, durable memory writes, external sends, or
remediation.

## LIMA IT Remediation

Read-only LIMA IT diagnostics may be represented as low-risk metadata.
Remediation remains blocked or approval-required metadata only in MVP. No
approval binding can authorize remediation execution or production-system touch.

## Evidence Requirements

The chain must capture evidence for:

- Guardian decision.
- Approval request.
- Approval result.
- Token issuance.
- Token verification.
- One-time consumption.
- Replay denial.
- Expiry.
- Revocation.
- Scope mismatch.
- Blocked-MVP denial.

Evidence records use refs and hashes. They must not include raw customer
content or secret material.

## Fail-Closed Behavior

The mock invariant checks raise explicit runtime errors when binding is missing,
expired, revoked, consumed, replayed, mismatched, tainted, wider than approved,
blocked for MVP, missing evidence, or not separated by requester and approver.

Task enqueueing for approval-required mock tasks now requires both a valid
`token.verification` and a valid `approval.binding`.

## MVP Acceptance Gates

- `approval.binding` and `approval.chain` schemas validate with sanitized
  examples.
- Approval-required mock task enqueueing fails without a binding.
- One-time binding passes once and replay fails.
- Expired, revoked, tenant-mismatched, task-mismatched, worker-mismatched,
  action-mismatched, scope-widened, tainted, missing-evidence, Guardian
  mismatch, blocked-MVP, LIMA IT remediation, live connector, external send,
  and remediation attempts fail closed in tests.
- No live connector, external send, real remediation, durable service, UI, or
  production operation is added.

## Non-Goals

- No live approval service.
- No durable token store.
- No durable nonce/replay table.
- No durable transaction coordinator.
- No OAuth or provider integration.
- No live connector access.
- No external sends.
- No remediation execution.
- No browser automation.
- No database, queue, web server, scheduler, or production service.
- No compliance certification claim.
