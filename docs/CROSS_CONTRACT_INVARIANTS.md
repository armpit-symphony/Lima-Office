# Cross-Contract Invariants

This document defines the Phase 1A invariant checkpoint that supersedes the
absent `phase-1a-cross-contract-invariants` /
`e71431007ddbe96c3e141b77591efc2508c53e5d` checkpoint. The original commit is
not reachable locally or on `origin`; this branch replaces it with a reachable
checkpoint built on [Baseline](BASELINE.md).

The checkpoint remains mock/in-memory hardening only. It does not add live
connectors, OAuth/provider wiring, external model calls, external sends,
browser automation, real remediation, durable services, UI, production
operations, or compliance certification claims.

## Purpose

Individually valid schemas can still form unsafe flows when their references do
not agree. Phase 1A v2 adds runtime invariant checks and tests that fail closed
when valid contract records are combined across the wrong tenant, task,
Guardian decision, token, evidence, taint, worker, tool, memory, helper, or LIMA
IT boundary. [Approval Token Runtime Binding](APPROVAL_TOKEN_RUNTIME_BINDING.md)
extends that checkpoint by normalizing the approval
request/result/token/verification/Guardian/task/tool chain into
`approval.binding`.
[Guardian Expiry And Replay Policy](GUARDIAN_EXPIRY_REPLAY_POLICY.md) further
hardens the checkpoint by making `guardian.decision` authorization one-time,
time-bounded, scope-bound, and replay-checked in memory for tests.

## Enforced Invariants

- `task.execution` cannot be assigned or completed without a matching
  `guardian.decision` for the same tenant, customer context, task, and decision
  ID.
- A Guardian deny, block-MVP, or quarantine decision cannot produce task
  completion.
- Expired, stale, future-effective, missing-expiry, ambiguous-timestamp,
  replayed, consumed, revoked, tainted, or blocked-MVP Guardian decisions
  cannot authorize mock task assignment, tool invocation, or completion.
- One-time Guardian decision nonce consumption is tracked in memory by the mock
  verifier for tests only; durable replay storage remains future work.
- Guardian decisions must match bound tenant, customer context, task, worker
  where present, action type, tool scope, decision scope hash, approval binding,
  token verification, and evidence refs.
- Approval-required tasks require a valid `token.verification` bound to the same
  tenant, customer context, task, approval request, approval token, and Guardian
  decision.
- Approval-required mock task assignment also requires a valid
  `approval.binding` bound to the same tenant, customer context, task, approval
  chain, binding, approval result, token, token verification, Guardian decision,
  policy snapshot, worker when applicable, and evidence refs.
- Approval bindings cannot authorize replayed, expired, revoked, consumed,
  mismatched, tainted, blocked-MVP, or wider-than-approved action metadata.
- One-time binding consumption is tracked in memory by the mock verifier for
  tests only; durable nonce/replay storage remains future work.
- Expired, revoked, missing, mismatched, ambiguous, wrong-scope, or fail-closed
  token verifications block assignment and completion.
- Evidence-required completion cannot proceed without evidence refs; when a
  mock evidence writer is attached, evidence refs must exist in that writer.
- Pre-action evidence failure blocks action; post-action evidence failure
  produces degraded state instead of silent success.
- Quarantined, revoked, offline, unknown, or wrong-tenant workers cannot receive
  tasks.
- Required task tool packs must be a subset of the assigned worker's registered
  capabilities.
- Tool invocation tenant, customer context, task, and worker identity must match
  the task and worker records when those records are present.
- Blocked-MVP approval results cannot authorize a tool invocation.
- Tainted input cannot authorize privileged tool invocation, external send,
  live connector-like behavior, remediation-like behavior, or durable memory
  write.
- Memory access must remain tenant-matched, non-cross-tenant, metadata-only, and
  fail closed on unresolved taint for summary writes.
- LIMA IT diagnostics may be represented as read-only metadata. LIMA IT
  remediation remains non-executing and approval-required/blocked for MVP.
- Helper scopes must remain supervisor-side, active, leased by metadata, and
  unable to exceed declared task classes, tool packs, data classifications, or
  blocked capabilities.

## Supervisor Health Contract

The checkpoint adds `supervisor.health` as metadata-only health reporting for
one Supervisor Server and 1-8 Arc workers. The report summarizes:

- worker state counts;
- task state counts;
- Guardian decision counts;
- evidence writer/artifact/failure counts;
- stale, quarantined, and revoked worker counts;
- blocked task and denied action counts;
- degraded component count;
- health status `healthy`, `degraded`, or `blocked`;
- reason codes from [Health Reason Taxonomy](ux/HEALTH_REASON_TAXONOMY.md);
- evidence, policy, and related contract refs.

The health report is mock/lab reporting only. It is not production monitoring,
an alerting service, durable telemetry, or an operations SLA.

## Unsafe Combinations Blocked

The new tests show that these combinations fail closed:

- a terminal task without evidence refs;
- a denied Guardian decision used for task completion;
- expired and revoked token verifications on approval-required tasks;
- wrong-scope token verification on approval-required tasks;
- one-time approval binding replay;
- approval binding tenant, task, worker, action, tool scope, or Guardian
  decision mismatch;
- blocked-MVP approval binding used for live connector, external send,
  remediation, production touch, or regulated-system action;
- expired or stale Guardian decisions;
- replayed Guardian decision nonce;
- future-effective Guardian decision beyond clock-skew allowance;
- Guardian decision tenant, task, worker, action, tool scope, approval binding,
  token verification, or decision-scope-hash mismatch;
- tainted privileged tool invocation;
- tainted durable memory summary write;
- LIMA IT remediation authorization in MVP;
- quarantined or revoked worker assignment;
- wrong-tenant worker heartbeat;
- worker capability mismatch during routing;
- helper scope overreach;
- blocked-MVP approval result used to run a tool;
- health payloads that would include raw customer content or secret-like
  material.

## Remaining Work

This checkpoint narrows unsafe combinations, but it does not finish all future
runtime policy. The remaining blockers stay open:

- durable approval-token consumption storage, replay evidence, and export
  posture beyond the in-memory mock verifier;
- durable Guardian replay store, atomic decision consumption, idempotency,
  concurrency handling, and exportable replay evidence beyond the mock
  verifier;
- durable evidence storage, integrity chain, audit export, retention,
  redaction, and customer exit/delete posture;
- final RBAC, IdP, MFA, session, and device trust decisions;
- model-routing defaults by data classification and provider class;
- worker attestation trust root and channel/device identity proof;
- signed update/rollback source format and trigger matrix;
- live connector consent, scope, revocation, and prompt-injection criteria.

## Validation

The checkpoint validation set remains:

```powershell
python scripts/validate-contracts.py --require-jsonschema --check-formats --warnings-as-errors
python scripts/check-doc-links.py
python -B -m unittest discover -s tests -v
python -m pytest -q
python -B -m compileall lima_office scripts tests
git diff --check
git diff --cached --check
git status
```
