# Validation Evidence

This file records the validation baseline for the Phase 0 / Phase 1A closeout.
Validation is not production certification and does not approve live connectors,
external sends, real remediation, production operations, or customer-system
mutation.

Latest captured run: 2026-05-22 on Windows with Python 3.12.10.

## Invariant Branch Reconciliation

Command:

```powershell
git fetch --all --prune
git cat-file -t e71431007ddbe96c3e141b77591efc2508c53e5d
git branch -a
git ls-remote --heads origin phase-1a-cross-contract-invariants
```

Result:

```text
git fetch --all --prune: PASS
git cat-file -t e71431007ddbe96c3e141b77591efc2508c53e5d: fatal: git cat-file: could not get object info
git branch -a: no local or remote phase-1a-cross-contract-invariants branch listed
git ls-remote --heads origin phase-1a-cross-contract-invariants: no matching head returned
```

Conclusion: `e71431007ddbe96c3e141b77591efc2508c53e5d` does not exist in this
local checkout after fetch, and `origin/phase-1a-cross-contract-invariants` is
not advertised. The branch could not be checked out or validated from this
workspace, and it could not be pushed because the local commit object is absent.

Environment note: the requested `python3` command form is not available in this
checkout. `python3 scripts/validate-contracts.py --require-jsonschema
--check-formats --warnings-as-errors` returned:

```text
Python was not found; run without arguments to install from the Microsoft Store, or disable this shortcut from Settings > Apps > Advanced app settings > App execution aliases.
```

The equivalent commands were run with `python`, which reports Python 3.12.10.

## Strict Schema Validation

Command:

```powershell
python3 scripts/validate-contracts.py --require-jsonschema --check-formats --warnings-as-errors
```

Result for requested `python3` command form: unavailable on this Windows
checkout because `python3` resolves to the Microsoft Store alias.

Equivalent result with available interpreter:

```text
LIMA Office contract validation
- schemas parsed: 19
- examples parsed: 28
- mapped examples: 28
- schemas with examples: 19
- validation mode: full JSON Schema draft 2020-12 with format checks
- jsonschema version: 4.26.0
- unsafe-content scan: 28 example files, 44 markdown files
- warnings: 0
- failures: 0
Result: PASS
```

Expected coverage:

- JSON Schema draft 2020-12 schema checks.
- Format checks.
- Example-to-schema mapping.
- Example coverage for every schema.
- Unsafe-content scan across examples and Markdown docs.

## Doc Link Check

Command:

```powershell
python3 scripts/check-doc-links.py
```

Result with available interpreter:

```text
LIMA Office markdown link check
- markdown files scanned: 52
- local links checked: 247
- external/anchor links ignored: 0
- failures: 0
Result: PASS
```

## Unit Tests

Command:

```powershell
python3 -B -m unittest discover -s tests -v
```

Result with available interpreter:

```text
Ran 50 tests in 0.685s

OK
```

## Pytest

Command:

```powershell
python3 -m pytest -q
```

Result with available interpreter:

```text
50 passed, 1 warning, 39 subtests passed in 0.77s
```

Warning: pytest could not create/write `.pytest_cache` because access was
denied in the local checkout. Test execution still passed.

## Compileall

Command:

```powershell
python3 -B -m compileall lima_office scripts tests
```

Result with available interpreter: PASS. Python compiled modules under
`lima_office`, `scripts`, and `tests`.

## Git Diff Checks

Commands:

```powershell
git diff --check
git diff --cached --check
```

Reconciliation patch result before staging: `git diff --check` returned exit 0
with LF-to-CRLF warnings for Markdown files in this Windows checkout; no
whitespace errors were reported.

## Git Status

Command:

```powershell
git status
```

Reconciliation patch result before staging: branch
`phase-0-1a-closeout-archive` with modified closeout docs only.

## CI Expectations

The CI baseline is `.github/workflows/phase0-validation.yml`.

Expected CI commands:

```bash
python scripts/validate-contracts.py --require-jsonschema --check-formats --warnings-as-errors
python scripts/check-doc-links.py
python -m unittest discover -s tests -v
python -m compileall lima_office scripts tests
git diff --check
```

CI runs without repository secrets. It validates contracts, local doc links,
Phase 1A mock runtime tests, Python compilation, and whitespace.

## Certification Boundary

Passing validation means the local docs, schemas, examples, and mock runtime
tests satisfy the repository checks. It does not prove:

- Production safety.
- Live connector readiness.
- Identity or MFA assurance.
- Worker attestation.
- Durable evidence integrity.
- Audit export readiness.
- Customer exit/delete readiness.
- LIMA IT separation of duties.
- Real remediation readiness.
