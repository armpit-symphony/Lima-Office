# Validation Evidence

Date: May 26, 2026

This file records the latest validation run for the narrow Phase 1B
worker-lifecycle and task-lifecycle simulator lanes.

## Scope

- Branch: `task-lifecycle-simulator-only`
- Base branch: `safety-patch-disposition` / `e31e225`
- Scope basis: explicit approved tiny Phase 1B slices (worker lifecycle simulator only, task lifecycle simulator only)
- Main branch update: not performed in this lane

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
  - markdown files scanned: `151`
  - local links checked: `1076`
- `unittest`: `PASS`
  - `Ran 439 tests`
  - `OK`
- `pytest`: `PASS`
  - `439 passed, 1 warning, 244 subtests passed`
- `compileall`: `PASS`
- `git diff --check`: `PASS` (after whitespace cleanup)
- `git diff --cached --check`: `PASS`

## Independent audit note

- Audit document: [WORKER_LIFECYCLE_SIMULATOR_AUDIT.md](audits/WORKER_LIFECYCLE_SIMULATOR_AUDIT.md)
- Audit result: `PASS WITH WARNINGS`
- Task slice implementation document: [PHASE_1B_TASK_LIFECYCLE_SIMULATOR.md](PHASE_1B_TASK_LIFECYCLE_SIMULATOR.md)
- Task slice audit document: [TASK_LIFECYCLE_SIMULATOR_AUDIT.md](audits/TASK_LIFECYCLE_SIMULATOR_AUDIT.md)
- Task slice audit result: `PASS WITH WARNINGS`

## Safety patch disposition

Safety patch `model-routing-health-taxonomy.partial.patch` remains archived
outside repo and removed from repo root per:
[SAFETY_PATCH_DISPOSITION.md](audits/SAFETY_PATCH_DISPOSITION.md).

## Interpretation boundary

Passing these checks means docs/contracts/tests/runtime-mock code are internally
consistent for this narrow slice. It does not approve broader runtime expansion,
live connectors, provider wiring, token runtime, remediation execution,
production operation, or compliance certification.
