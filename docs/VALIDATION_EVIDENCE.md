# Validation Evidence

Date: May 26, 2026

This file records the latest validation run for the narrow Phase 1B
worker-lifecycle and task-lifecycle simulator lanes.

Phase 1C planning branch validation is also recorded below.
Phase 1C evidence lifecycle simulator slice validation is also recorded below.
Phase 1C evidence lifecycle warning hardening validation is also recorded below.
Phase 1C Guardian replay drill simulator slice validation is also recorded below.
Phase 1C Guardian replay drill simulator independent audit validation is also
recorded below.
Phase 1C Guardian replay drill simulator warning hardening validation is also
recorded below.
Phase 1C Guardian replay drill simulator hardening audit validation is also
recorded below.
Phase 1C simulator baseline tag provenance fix validation is also recorded
below.

## Scope

- Branch: `phase-1c-closeout-status-archive`
- Base branch: `phase-1c-annotated-tag-provenance-fix` / `2a36006`
- Scope basis: explicit approved tiny Phase 1B slices (worker lifecycle simulator only, task lifecycle simulator only)
- Main branch update: not performed in this lane
- Phase 1C planning branch: `phase-1c-supervised-lab-orchestration-planning`
- Phase 1C base branch: `audit-phase-1b-simulator-baseline-tag` / `be52227`
- Phase 1C evidence lifecycle branch: `evidence-lifecycle-simulator-only`
- Phase 1C evidence lifecycle base branch:
  `audit-phase-1c-supervised-lab-orchestration-planning` / `d7b5d49`
- Phase 1C evidence lifecycle warning hardening branch:
  `evidence-lifecycle-simulator-audit-hardening`
- Phase 1C evidence lifecycle warning hardening base branch:
  `audit-evidence-lifecycle-simulator-only` / `ede4580`
- Phase 1C Guardian replay drill simulator branch:
  `guardian-replay-drill-simulator-only`
- Phase 1C Guardian replay drill simulator base branch:
  `audit-evidence-lifecycle-simulator-hardening` / `72da9cb`
- Phase 1C Guardian replay drill simulator audit branch:
  `audit-guardian-replay-drill-simulator-only`
- Phase 1C Guardian replay drill simulator warning hardening branch:
  `guardian-replay-drill-simulator-audit-hardening`
- Phase 1C Guardian replay drill simulator warning hardening base branch:
  `audit-guardian-replay-drill-simulator-only` / `eac554f`
- Phase 1C Guardian replay drill simulator hardening audit branch:
  `audit-guardian-replay-drill-simulator-hardening`
- Phase 1C Guardian replay drill simulator hardening audit base branch:
  `guardian-replay-drill-simulator-audit-hardening` / `a4f9661`
- Phase 1C simulator provenance branch: `phase-1c-annotated-tag-provenance-fix`
- Phase 1C annotated provenance tag:
  `lima-office-phase-1c-simulator-baseline-annotated`
- Original lightweight tag retained for history:
  `lima-office-phase-1c-simulator-baseline`

## Phase 1C Simulator Baseline Tag Provenance Fix Update

Audit lane: docs-only provenance correction for baseline tag object type.
No implementation changes were made.

Latest command results on `phase-1c-annotated-tag-provenance-fix`:

- `check-doc-links`: `PASS`
- `git diff --check`: `PASS`
- `git status --short --branch`: clean with expected branch tracking

## Phase 1C Closeout Archive Update

Closeout branch: `phase-1c-closeout-status-archive`

Canonical baseline/provenance status:

- Integration baseline branch:
  `integration/phase-1c-simulator-baseline` ->
  `8232970eb5e18e1c5db29e78f673b42f15b07ccc`
- Canonical annotated tag:
  `lima-office-phase-1c-simulator-baseline-annotated` (tag object type)
- Annotated tag target:
  `8232970eb5e18e1c5db29e78f673b42f15b07ccc`
- Original lightweight tag retained for continuity:
  `lima-office-phase-1c-simulator-baseline` (commit object type)
- `origin/main` unchanged anchor:
  `e4bb6105a9d668ddffe21892da3aaff16a0d8ca0`

Closeout guidance:

- Baseline remains simulator-only and fail-closed.
- Broader implementation remains blocked by default.
- Any next tiny implementation slice still requires explicit approval and fresh
  independent audit.

## Commands

```powershell
python scripts/validate-contracts.py --require-jsonschema --check-formats --warnings-as-errors
python scripts/check-reason-codes.py
python scripts/check-doc-links.py
python -B -m unittest discover -s tests -v
python -m pytest -q
python -B -m compileall lima_office scripts tests
git diff --check
git diff --cached --check
git status
```

## Results (latest run on this branch)

- `validate-contracts`: `PASS`
  - schemas parsed: `65`
  - examples parsed: `208`
  - mapped examples: `208`
  - schemas with examples: `65`
- `check-reason-codes`: `PASS`
  - schemas scanned: `65`
  - examples scanned: `208`
  - known canonical/alias codes: `227`
  - reason-code values scanned in schemas: `610`
  - reason-code values scanned in examples: `323`
- `check-doc-links`: `PASS`
  - markdown files scanned: `165`
  - local links checked: `1099`
- `unittest`: `PASS`
  - `Ran 502 tests`
  - `OK`
- `pytest`: `PASS`
  - `502 passed, 1 warning, 244 subtests passed`
- `compileall`: `PASS`
- `git diff --check`: `PASS` (after whitespace cleanup)
- `git diff --cached --check`: `PASS`

## Phase 1C Guardian Replay Drill Simulator Audit Update

Audit lane: docs-only independent review for Guardian replay drill simulator
slice. No runtime expansion was added in this audit branch.

Latest command results on `audit-guardian-replay-drill-simulator-only`:

- `validate-contracts`: `PASS`
  - schemas parsed: `65`
  - examples parsed: `208`
  - mapped examples: `208`
  - schemas with examples: `65`
- `check-reason-codes`: `PASS`
  - schemas scanned: `65`
  - examples scanned: `208`
  - known canonical/alias codes: `227`
  - reason-code values scanned in schemas: `610`
  - reason-code values scanned in examples: `323`
- `check-doc-links`: `PASS`
  - markdown files scanned: `161`
  - local links checked: `1093`
- `unittest`: `PASS`
  - `Ran 490 tests`
  - `OK`
- `pytest`: `PASS`
  - `490 passed, 1 warning, 244 subtests passed`
- `compileall`: `PASS`
- `git diff --check`: `PASS`
- `git diff --cached --check`: `PASS`

## Phase 1C Planning Branch Update

Planning lane: docs/runbook/gate updates only. No runtime implementation added.

Latest command results on `phase-1c-supervised-lab-orchestration-planning`:

- `validate-contracts`: `PASS`
  - schemas parsed: `65`
  - examples parsed: `208`
  - mapped examples: `208`
  - schemas with examples: `65`
- `check-reason-codes`: `PASS`
  - schemas scanned: `65`
  - examples scanned: `208`
  - known canonical/alias codes: `227`
  - reason-code values scanned in schemas: `610`
  - reason-code values scanned in examples: `323`
- `check-doc-links`: `PASS`
  - markdown files scanned: `156`
  - local links checked: `1083`
- `unittest`: `PASS`
  - `Ran 439 tests`
  - `OK`
- `pytest`: `PASS`
  - `439 passed, 1 warning, 244 subtests passed`
- `compileall`: `PASS`
- `git diff --check`: `PASS`
- `git diff --cached --check`: `PASS`

## Phase 1C Evidence Lifecycle Slice Update

Implementation lane: in-memory evidence lifecycle simulator only.
No runtime IO/storage/background/network expansion added.

Latest command results on `evidence-lifecycle-simulator-only`:

- `validate-contracts`: `PASS`
  - schemas parsed: `65`
  - examples parsed: `208`
  - mapped examples: `208`
  - schemas with examples: `65`
- `check-reason-codes`: `PASS`
  - schemas scanned: `65`
  - examples scanned: `208`
  - known canonical/alias codes: `227`
  - reason-code values scanned in schemas: `610`
  - reason-code values scanned in examples: `323`
- `check-doc-links`: `PASS`
  - markdown files scanned: `158`
  - local links checked: `1087`
- `unittest`: `PASS`
  - `Ran 463 tests`
  - `OK`
- `pytest`: `PASS`
  - `463 passed, 1 warning, 244 subtests passed`
- `compileall`: `PASS`
- `git diff --check`: `PASS`
- `git diff --cached --check`: `PASS`

## Phase 1C Evidence Lifecycle Warning-Hardening Update

Hardening lane: warning-closure for evidence lifecycle simulator only.
No runtime IO/storage/background/network/export-delete expansion added.

Latest command results on `evidence-lifecycle-simulator-audit-hardening`:

- `validate-contracts`: `PASS`
  - schemas parsed: `65`
  - examples parsed: `208`
  - mapped examples: `208`
  - schemas with examples: `65`
- `check-reason-codes`: `PASS`
  - schemas scanned: `65`
  - examples scanned: `208`
  - known canonical/alias codes: `227`
  - reason-code values scanned in schemas: `610`
  - reason-code values scanned in examples: `323`
- `check-doc-links`: `PASS`
  - markdown files scanned: `161`
  - local links checked: `1093`
- `unittest`: `PASS`
  - `Ran 490 tests`
  - `OK`
- `pytest`: `PASS`
  - `490 passed, 1 warning, 244 subtests passed`
- `compileall`: `PASS`
- `git diff --check`: `PASS`
- `git diff --cached --check`: `PASS`

## Phase 1C Guardian Replay Drill Simulator Slice Update

Implementation lane: in-memory Guardian replay drill simulator only.
No runtime IO/storage/background/network/durable replay-store expansion added.

Latest command results on `guardian-replay-drill-simulator-only`:

- `validate-contracts`: `PASS`
  - schemas parsed: `65`
  - examples parsed: `208`
  - mapped examples: `208`
  - schemas with examples: `65`
- `check-reason-codes`: `PASS`
  - schemas scanned: `65`
  - examples scanned: `208`
  - known canonical/alias codes: `227`
  - reason-code values scanned in schemas: `610`
  - reason-code values scanned in examples: `323`
- `check-doc-links`: `PASS`
  - markdown files scanned: `161`
  - local links checked: `1093`
- `unittest`: `PASS`
  - `Ran 490 tests`
  - `OK`
- `pytest`: `PASS`
  - `490 passed, 1 warning, 244 subtests passed`
- `compileall`: `PASS`
- `git diff --check`: `PASS`
- `git diff --cached --check`: `PASS`

## Phase 1C Guardian Replay Drill Simulator Warning-Hardening Update

Hardening lane: warning-closure for Guardian replay drill simulator only.
No runtime IO/storage/background/network/durable replay-store expansion added.

Latest command results on `guardian-replay-drill-simulator-audit-hardening`:

- `validate-contracts`: `PASS`
  - schemas parsed: `65`
  - examples parsed: `208`
  - mapped examples: `208`
  - schemas with examples: `65`
- `check-reason-codes`: `PASS`
  - schemas scanned: `65`
  - examples scanned: `208`
  - known canonical/alias codes: `227`
  - reason-code values scanned in schemas: `610`
  - reason-code values scanned in examples: `323`
- `check-doc-links`: `PASS`
  - markdown files scanned: `162`
  - local links checked: `1094`
- `unittest`: `PASS`
  - `Ran 502 tests`
  - `OK`
- `pytest`: `PASS`
  - `502 passed, 1 warning, 244 subtests passed`
- `compileall`: `PASS`
- `git diff --check`: `PASS`
- `git diff --cached --check`: `PASS`

## Phase 1C Guardian Replay Drill Simulator Hardening Audit Update

Audit lane: docs-only independent review for Guardian replay drill simulator
warning-hardening branch. No runtime expansion was added in this audit branch.

Latest command results on `audit-guardian-replay-drill-simulator-hardening`:

- `validate-contracts`: `PASS`
  - schemas parsed: `65`
  - examples parsed: `208`
  - mapped examples: `208`
  - schemas with examples: `65`
- `check-reason-codes`: `PASS`
  - schemas scanned: `65`
  - examples scanned: `208`
  - known canonical/alias codes: `227`
  - reason-code values scanned in schemas: `610`
  - reason-code values scanned in examples: `323`
- `check-doc-links`: `PASS`
  - markdown files scanned: `162`
  - local links checked: `1094`
- `unittest`: `PASS`
  - `Ran 502 tests`
  - `OK`
- `pytest`: `PASS`
  - `502 passed, 1 warning, 244 subtests passed`
- `compileall`: `PASS`
- `git diff --check`: `PASS`

## Independent audit note

- Audit document: [WORKER_LIFECYCLE_SIMULATOR_AUDIT.md](audits/WORKER_LIFECYCLE_SIMULATOR_AUDIT.md)
- Audit result: `PASS WITH WARNINGS`
- Task slice implementation document: [PHASE_1B_TASK_LIFECYCLE_SIMULATOR.md](PHASE_1B_TASK_LIFECYCLE_SIMULATOR.md)
- Task slice audit document: [TASK_LIFECYCLE_SIMULATOR_AUDIT.md](audits/TASK_LIFECYCLE_SIMULATOR_AUDIT.md)
- Task slice audit result: `PASS WITH WARNINGS`
- Frozen simulator baseline branch: `integration/phase-1b-simulator-baseline`
- Baseline tag audit document: [PHASE_1B_SIMULATOR_BASELINE_TAG_AUDIT.md](audits/PHASE_1B_SIMULATOR_BASELINE_TAG_AUDIT.md)
- Baseline tag audit result: `PASS WITH WARNINGS`
- Phase 1C planning audit document:
  [PHASE_1C_SUPERVISED_LAB_ORCHESTRATION_PLANNING_AUDIT.md](audits/PHASE_1C_SUPERVISED_LAB_ORCHESTRATION_PLANNING_AUDIT.md)
- Phase 1C planning audit result: `PASS WITH WARNINGS`
- Phase 1C evidence lifecycle simulator audit document:
  [EVIDENCE_LIFECYCLE_SIMULATOR_AUDIT.md](audits/EVIDENCE_LIFECYCLE_SIMULATOR_AUDIT.md)
- Phase 1C evidence lifecycle simulator audit result: `PASS WITH WARNINGS`
- Evidence lifecycle warning-hardening branch:
  `evidence-lifecycle-simulator-audit-hardening`
- Evidence lifecycle hardening audit document:
  [EVIDENCE_LIFECYCLE_SIMULATOR_HARDENING_AUDIT.md](audits/EVIDENCE_LIFECYCLE_SIMULATOR_HARDENING_AUDIT.md)
- Evidence lifecycle hardening audit result: `PASS`

## Safety patch disposition

Safety patch `model-routing-health-taxonomy.partial.patch` remains archived
outside repo and removed from repo root per:
[SAFETY_PATCH_DISPOSITION.md](audits/SAFETY_PATCH_DISPOSITION.md).

## Interpretation boundary

Passing these checks means docs/contracts/tests/runtime-mock code are internally
consistent for this narrow slice. It does not approve broader runtime expansion,
live connectors, provider wiring, token runtime, remediation execution,
production operation, or compliance certification.
