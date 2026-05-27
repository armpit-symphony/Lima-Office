# Evidence Lifecycle Simulator Audit

Audit date: May 26, 2026

## Audited target

- Branch: `evidence-lifecycle-simulator-only`
- Commit: `ec28a7ef3577f6762e294e7085c6db1c1dd55c51`
- Audit branch: `audit-evidence-lifecycle-simulator-only`

## Audit result

**PASS WITH WARNINGS**

## Files reviewed

- `lima_office/evidence/lifecycle_simulator.py`
- `lima_office/evidence/__init__.py`
- `lima_office/runtime/errors.py`
- `tests/test_evidence_lifecycle_simulator.py`
- `contracts/v1/evidence.artifact.schema.json`
- `contracts/v1/evidence.failure.schema.json`
- `contracts/v1/evidence.ledger.entry.schema.json`
- `contracts/v1/evidence.export_manifest.schema.json`
- `docs/PHASE_1C_EVIDENCE_LIFECYCLE_SIMULATOR.md`
- `docs/PHASE_1C_SUPERVISED_LAB_ORCHESTRATION_PLAN.md`
- `docs/PHASE_1C_SUPERVISOR_LAB_ORCHESTRATOR_GATE.md`
- `docs/RUNTIME_BOUNDARIES.md`
- `docs/DURABLE_REPLAY_EVIDENCE_POSTURE.md`
- `docs/CROSS_CONTRACT_INVARIANTS.md`
- `docs/CROSS_CONTRACT_LINKAGE_HARDENING.md`
- `docs/APPROVAL_TOKEN_RUNTIME_BINDING.md`
- `docs/GUARDIAN_EXPIRY_REPLAY_POLICY.md`

## Implementation summary

- Evidence lifecycle simulator is implemented as in-memory metadata simulation only.
- Runtime export/delete/tool execution/authorization actions are explicitly blocked.
- Contract validation is enforced through the existing contract validator.
- Transition history is retained in memory only.
- Raw-content and secret-material indicators are fail-closed.
- Cross-tenant evidence linkage is fail-closed for known references and tenant mismatches.

## Scope-boundary findings

- No filesystem persistence behavior was added.
- No database, queue, scheduler, daemon, thread, subprocess, or web-server behavior was added.
- No network/API/socket behavior was added.
- No connector/model/auth/remediation/tool-execution/runtime-dispatch/UI behavior was added.
- No production-readiness or compliance-certification claims were added.

## Transition-matrix findings

Verified in implementation and tests:

- Allowed:
  - `planned -> pre_action_recorded -> post_action_recorded -> ledger_linked`
  - `planned -> denial_recorded -> ledger_linked`
  - `planned -> replay_denial_recorded -> ledger_linked`
  - `planned -> failed_closed_recorded -> ledger_linked`
  - `ledger_linked -> export_manifest_planned` (metadata planning only)
- Blocked:
  - `planned -> post_action_recorded` direct
  - any transition to non-modeled runtime states such as `exported` / `deleted`
  - evidence with `raw_content_included=true`
  - evidence with `secret_material_included=true`
  - tenant mismatch and cross-tenant chain mismatch
  - denial/replay-denial paths without required reason/linkage metadata
  - evidence-required completion metadata without evidence refs

## Evidence / Guardian / approval linkage findings

- Pre/post action evidence states require task and Guardian metadata.
- Approval-required task metadata requires approval binding and token verification metadata.
- Guardian replay-safety and token authorization invariants are reused and enforced.
- Export/delete runtime behavior remains blocked even when export-manifest metadata is present.

## Export/delete non-expansion findings

- Simulator methods `export_evidence` and `delete_evidence` always raise `UnsafeRuntimeActionError`.
- Payloads implying runtime-exported or runtime-delete execution are rejected fail-closed.
- No evidence writer/export runtime path was expanded in this slice.

## Validation results

Executed:

```powershell
python scripts/validate-contracts.py --require-jsonschema --check-formats --warnings-as-errors
python scripts/check-reason-codes.py
python scripts/check-doc-links.py
python -B -m unittest discover -s tests -v
python -m pytest -q
python -B -m compileall lima_office scripts tests
git diff --check
git status --short --branch
```

Results:

- `validate-contracts`: PASS (`65` schemas, `208` examples)
- `check-reason-codes`: PASS (`610` schema reason-code values, `323` example values)
- `check-doc-links`: PASS (`158` markdown files, `1087` local links)
- `unittest`: PASS (`Ran 463 tests`)
- `pytest`: PASS (`463 passed, 1 warning, 244 subtests passed`)
- `compileall`: PASS
- `git diff --check`: PASS

## Defects and warnings

Non-blocking warnings:

1. Simulator currently permits same-state transitions, which can update payload metadata without lifecycle advancement.
2. Evidence-reference checks validate format and known-tenant consistency, but do not universally require pre-existing reference resolution in all paths.
3. State-to-contract coupling is strict for `export_manifest_planned`, but other states can accept multiple evidence contract shapes when otherwise schema-valid.
4. As designed for this slice, history is in-memory only; durable audit trail is intentionally out of scope.
5. `pytest` emits a Windows cache warning (`.pytest_cache` write denied); test pass/fail is unaffected.

No critical defect requiring runtime-feature changes was found for this approved narrow slice.

## Merge safety assessment

Assessment: safe to keep/merge for approved scope.

- The branch stays within the explicitly approved evidence-lifecycle-only slice.
- Fail-closed behavior is present and covered by tests.
- No prohibited runtime expansion surfaces were introduced.

## Explicit blocked surfaces (still blocked)

- Guardian replay drill simulator implementation
- supervisor orchestration implementation
- runtime dispatch/tool execution behavior
- live connectors
- OAuth/OIDC/SAML/provider wiring
- token runtime/storage/rotation
- model provider calls and local inference runtime
- network sends/form submission/browser automation
- remediation execution
- durable storage/database/queue/web server/background runtime
- export/delete runtime implementation
- UI/frontend/runtime production expansion

## Recommendation

- **Merge/keep** this evidence lifecycle simulator slice.
- Next tiny slice may be considered only with explicit approval and fresh independent audit.
- Conservative next option: Guardian replay drill simulator planning first, then implementation only if separately approved.

## Follow-Up Hardening Note

A targeted follow-up hardening branch was opened after this audit:
`evidence-lifecycle-simulator-audit-hardening`.

The follow-up branch specifically addresses the non-blocking warnings about:

- same-state transition mutability
- reference pre-existence strictness for required lifecycle refs
- contract/state coupling clarity
- registration starting from non-`planned` states

This follow-up remains simulator-only and does not approve broader Phase 1C
runtime expansion.
