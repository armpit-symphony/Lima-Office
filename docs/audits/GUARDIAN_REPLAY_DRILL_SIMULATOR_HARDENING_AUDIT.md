# Guardian Replay Drill Simulator Hardening Audit

Date: May 26, 2026

## Branch and Commit Audited

- Branch: `guardian-replay-drill-simulator-audit-hardening`
- Commit: `a4f966176162d10dca192023c1928dd515e22346`
- Audit branch: `audit-guardian-replay-drill-simulator-hardening`

## Audit Result

**PASS WITH WARNINGS**

## Files Reviewed

- `lima_office/guardian/replay_drill_simulator.py`
- `tests/test_guardian_replay_drill_simulator.py`
- `lima_office/runtime/errors.py`
- `docs/PHASE_1C_GUARDIAN_REPLAY_DRILL_SIMULATOR.md`
- `docs/audits/GUARDIAN_REPLAY_DRILL_SIMULATOR_AUDIT.md`
- `docs/RUNTIME_BOUNDARIES.md`
- `docs/GUARDIAN_EXPIRY_REPLAY_POLICY.md`
- `docs/APPROVAL_TOKEN_RUNTIME_BINDING.md`
- `docs/DURABLE_REPLAY_EVIDENCE_POSTURE.md`
- Contracts:
  - `contracts/v1/guardian.decision.schema.json`
  - `contracts/v1/guardian.replay.schema.json`
  - `contracts/v1/replay.store.record.schema.json`
  - `contracts/v1/approval.binding.schema.json`
  - `contracts/v1/token.verification.schema.json`

## Warning-Closure Findings

Verified as closed:

1. Planned-only registration: enforced in simulator and tested.
2. Non-planned registration fails: explicit test present.
3. Same-state transitions: explicitly rejected and tested as non-mutating.
4. `execute_tools` and `authorize_real_action` remain hard-blocked.
5. Bound first-use now requires `approval.binding` payload when
   `approval_binding_id` is bound.
6. Bound first-use now requires `token.verification` payload when
   `token_verification_id` is bound.
7. Duplicate nonce reservation before consume is blocked.
8. Mismatch handling uses structured categories instead of brittle substring
   marker matching.
9. Replay denial / failed-closed evidence ref requirements are enforced.
10. Placeholder refs remain non-authorizing because simulator continues to block
    authorization, tool execution, persistence, and runtime dispatch.

## Scope-Boundary Findings

- No IO, storage, background worker, threading, daemon, queue, subprocess, or
  network behavior was added.
- No durable replay store behavior was added.
- No real authorization, task dispatch, or tool execution behavior was added.
- No broader Phase 1C runtime expansion was added.

## Replay / Nonce Findings

- Registration starts from `planned` only.
- Same-state transitions are denied.
- Duplicate nonce reservation is denied before consumption.
- Duplicate nonce consumption is denied.
- Nonce consumption requires prior reservation.
- Tenant-isolated nonce reservation behavior is preserved.

## Approval / Token / Evidence Findings

- First-use fail-closed checks now enforce bound payload presence for approval
  binding and token verification.
- Approval/token mismatch checks remain fail-closed.
- Structured mismatch categories are required and validated.
- Denial and failed-closed transitions require evidence refs and ref-format
  checks.

## Validation Results

- `python scripts/validate-contracts.py --require-jsonschema --check-formats --warnings-as-errors`: PASS
  - schemas parsed: `65`
  - examples parsed: `208`
- `python scripts/check-reason-codes.py`: PASS
  - schemas scanned: `65`
  - examples scanned: `208`
- `python scripts/check-doc-links.py`: PASS
  - markdown files scanned: `162`
  - local links checked: `1094`
- `python -B -m unittest discover -s tests -v`: PASS (`Ran 502 tests`)
- `python -m pytest -q`: PASS (`502 passed, 1 warning, 244 subtests passed`)
- `python -B -m compileall lima_office scripts tests`: PASS
- `git diff --check`: PASS
- `git status --short --branch`: clean

## Remaining Warnings

- Replay-store/evidence semantics are stronger than the prior audit baseline
  but still intentionally limited to metadata-only simulator scope. Durable
  cross-record replay-store semantics remain blocked future work.

## Safe to Keep / Merge

**Yes** for the approved narrow scope.

## Phase 1C Simulator Baseline Refreeze Assessment

Refreeze can be done next after this audit branch is reviewed and merged.

## Explicitly Blocked Surfaces Still Blocked

- live connectors
- OAuth/OIDC/SAML/provider wiring
- token runtime storage/rotation
- external API/network side effects
- durable replay store and durable storage
- background workers/schedulers/daemons/queues
- real authorization/dispatch/tool execution
- remediation runtime
- UI/frontend runtime
- production-readiness/compliance claims
