# Guardian Replay Drill Simulator Audit

Date: May 26, 2026

## Branch and Commit Audited

- Branch: `guardian-replay-drill-simulator-only`
- Commit: `5034ffab5eb0af41e4db39ff1d0244da96752dac`
- Audit branch: `audit-guardian-replay-drill-simulator-only`

## Audit Result

**PASS WITH WARNINGS**

## Files Reviewed

- `lima_office/guardian/replay_drill_simulator.py`
- `lima_office/guardian/__init__.py`
- `lima_office/runtime/errors.py`
- `tests/test_guardian_replay_drill_simulator.py`
- `docs/PHASE_1C_GUARDIAN_REPLAY_DRILL_SIMULATOR.md`
- `docs/RUNTIME_BOUNDARIES.md`
- `docs/GUARDIAN_EXPIRY_REPLAY_POLICY.md`
- `docs/APPROVAL_TOKEN_RUNTIME_BINDING.md`
- `docs/DURABLE_REPLAY_EVIDENCE_POSTURE.md`
- `docs/CROSS_CONTRACT_INVARIANTS.md`
- Contracts:
  - `contracts/v1/guardian.decision.schema.json`
  - `contracts/v1/guardian.replay.schema.json`
  - `contracts/v1/replay.store.record.schema.json`
  - `contracts/v1/approval.binding.schema.json`
  - `contracts/v1/token.verification.schema.json`

## Implementation Summary

The slice remains narrowly scoped to an in-memory Guardian replay drill simulator.
It validates contract-shaped metadata for decision/replay/replay-store records,
enforces replay-state transitions, and fails closed on stale/expired/replayed/
mismatched/blocked-mvp scenarios.

No live Guardian service, durable replay store, runtime authorization expansion,
or execution behavior was added.

## Scope-Boundary Findings

- No IO/storage/network/background behavior was introduced in implementation.
- No durable replay store behavior was introduced.
- No tool execution or real authorization behavior was introduced.
- Blocked surfaces remain blocked (connectors/models/auth/remediation/UI/production).

## Replay and Nonce Transition Findings

Verified expected behavior:

- `planned -> decision_registered -> nonce_reserved -> first_use_validated -> nonce_consumed` passes.
- `nonce_consumed -> replay_denied` passes.
- expired/stale/future-effective/contradictory timestamp paths fail closed.
- missing nonce fails.
- duplicate nonce consumption fails.
- cross-tenant replay fails.
- blocked-mvp decision cannot validate.
- denial and failed-closed paths require evidence and fail without required refs.

Warning:

- Duplicate nonce reservation is not independently blocked prior to nonce
  consumption; current protection is centered on consumed-nonce replay denial.

## Approval, Token, and Evidence Findings

- Approval binding mismatch fails.
- Token verification mismatch fails.
- Action and tool-scope mismatch fails.
- Worker mismatch (when bound) fails.
- Evidence requirements on denial/fail-closed paths are enforced.

Warning:

- First-use validation does not strictly require both approval-binding and token
  verification payload objects when decision metadata is bound; consistency
  checks are strong when supplied, but mandatory-presence enforcement is not
  fully strict.

## Known-Warning Assessment

1. Explicit tests for planned-only registration: **Warning (test coverage gap)**.
2. Explicit tests for same-state transition rejection: **Warning (coverage gap)**.
3. Explicit tests for `execute_tools` hard-block path: **Warning (coverage gap)**.
4. Stricter first-use mandatory binding/token objects when bound: **Warning**.
5. Duplicate nonce reservation blocking before consume: **Warning**.
6. Structured mismatch checks vs string-marker matching: **Warning**.
7. Stronger replay-store/evidence semantic enforcement: **Warning**.

None of the above are assessed as immediate blockers for keeping this narrow
in-memory slice, but they should be hardened before broader orchestration work.

## Validation Results

- `python scripts/validate-contracts.py --require-jsonschema --check-formats --warnings-as-errors`: PASS
  - schemas parsed: `65`
  - examples parsed: `208`
- `python scripts/check-reason-codes.py`: PASS
  - schemas scanned: `65`
  - examples scanned: `208`
- `python scripts/check-doc-links.py`: PASS
  - markdown files scanned: `161`
  - local links checked: `1093`
- `python -B -m unittest discover -s tests -v`: PASS (`Ran 490 tests`)
- `python -m pytest -q`: PASS (`490 passed, 1 warning, 244 subtests passed`)
- `python -B -m compileall lima_office scripts tests`: PASS
- `git diff --check`: PASS
- `git status --short --branch`: clean

## Defects or Warnings

- No blocking defects identified for this narrow slice.
- Warnings listed above remain open for follow-up hardening.

### Follow-Up Hardening Note

Warnings in this audit are addressed in follow-up branch
`guardian-replay-drill-simulator-audit-hardening`:

- explicit planned-only registration test
- explicit same-state transition test
- explicit execute-tools block test
- mandatory bound first-use approval/token payload requirement
- duplicate nonce reservation blocking pre-consumption
- structured mismatch category checks
- stronger denial/failed-closed evidence-ref semantics

## Safe to Keep or Merge

**Safe to keep/merge with warnings** for the approved narrow scope.

## Hardening Requirement Before Next Slice

Recommended: complete warning hardening first (especially duplicate reservation
handling, strict bound-binding presence checks, and structured mismatch checks)
before approving another implementation slice.

## Explicitly Blocked Surfaces Still Blocked

- live connectors
- OAuth/OIDC/SAML/provider wiring
- token runtime storage/rotation
- external APIs/network actions
- background workers/daemons/schedulers/queues
- durable replay/database/web service behavior
- tool execution/dispatch runtime
- remediation runtime
- UI/frontend runtime
- production-readiness/compliance claims
