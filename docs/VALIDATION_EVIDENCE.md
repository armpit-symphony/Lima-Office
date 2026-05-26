# Validation Evidence

Date: May 26, 2026

This file records the latest validation run for the narrow Phase 1B
worker-lifecycle and task-lifecycle simulator lanes.

Phase 1C planning branch validation is also recorded below.
Phase 1C evidence lifecycle simulator slice validation is also recorded below.

## Scope

- Branch: `integration/phase-1b-simulator-baseline`
- Base branch: `safety-patch-disposition` / `e31e225`
- Scope basis: explicit approved tiny Phase 1B slices (worker lifecycle simulator only, task lifecycle simulator only)
- Main branch update: not performed in this lane
- Phase 1C planning branch: `phase-1c-supervised-lab-orchestration-planning`
- Phase 1C base branch: `audit-phase-1b-simulator-baseline-tag` / `be52227`
- Phase 1C evidence lifecycle branch: `evidence-lifecycle-simulator-only`
- Phase 1C evidence lifecycle base branch:
  `audit-phase-1c-supervised-lab-orchestration-planning` / `d7b5d49`

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
  - markdown files scanned: `152`
  - local links checked: `1078`
- `unittest`: `PASS`
  - `Ran 439 tests`
  - `OK`
- `pytest`: `PASS`
  - `439 passed, 1 warning, 244 subtests passed`
- `compileall`: `PASS`
- `git diff --check`: `PASS` (after whitespace cleanup)
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

## Safety patch disposition

Safety patch `model-routing-health-taxonomy.partial.patch` remains archived
outside repo and removed from repo root per:
[SAFETY_PATCH_DISPOSITION.md](audits/SAFETY_PATCH_DISPOSITION.md).

## Interpretation boundary

Passing these checks means docs/contracts/tests/runtime-mock code are internally
consistent for this narrow slice. It does not approve broader runtime expansion,
live connectors, provider wiring, token runtime, remediation execution,
production operation, or compliance certification.
