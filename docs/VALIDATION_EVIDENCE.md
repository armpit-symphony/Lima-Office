# Validation Evidence

Date: May 26, 2026

This file records the latest baseline validation run for the stabilization review lane.

## Scope

- Branch: `major-baseline-stabilization-next-phase-gate-review`
- Checkpoint basis: `connector-source-of-truth-values-slo-target-finalization` / `a92606a`
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
  - markdown files scanned: `142`
  - local links checked: `1058`
- `unittest`: `PASS`
  - `Ran 394 tests`
  - `OK`
- `pytest`: `PASS`
  - `394 passed, 1 warning, 244 subtests passed`
- `compileall`: `PASS`
- `git diff --check`: `PASS` (after whitespace cleanup)
- `git diff --cached --check`: `PASS`

## Safety patch caveat

The untracked safety patch `model-routing-health-taxonomy.partial.patch` remains intentionally uncommitted and unchanged in this lane.

## Interpretation boundary

Passing these checks means docs/contracts/tests/mock metadata are internally consistent for this checkpoint. It does not approve runtime implementation, live connectors, provider wiring, token runtime, remediation execution, production operation, or compliance certification.
