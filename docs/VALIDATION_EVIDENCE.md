# Validation Evidence

This file records the validation baseline for the Phase 0 / Phase 1A closeout
and the canonical integration branch. Validation is not production
certification and does not approve live connectors, external sends, real
remediation, production operations, or customer-system mutation.

Latest captured run: `integration/phase-0-1a-baseline` on Windows with Python
3.12.10.

## Canonical Integration Branch

- Branch: `integration/phase-0-1a-baseline`
- Source base: `operator-console-ux-spec` /
  `bac6f80cc63dd15ec7cd3d669193160c3766a8e1`
- Included branches and excluded checkpoints are listed in
  [Baseline](BASELINE.md).
- `main` was not updated by this validation evidence.

## Invariant Branch Reconciliation

Commands:

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
not advertised. The branch is not integrated or validated in the canonical
baseline.

## Branch Inclusion Checks

Command:

```powershell
git merge-base --is-ancestor <branch> HEAD
```

Result: PASS for each reachable stabilization target:

- `phase-0-architecture-contracts-roadmap`
- `phase-0-contract-schemas`
- `phase-0-policy-runbook-hardening`
- `phase-0-schema-conditionals-followups`
- `phase-0-ci-schema-validation`
- `phase-1a-runtime-scaffolding`
- `phase-0-1a-closeout-archive`
- `worker-deployment-blueprint`
- `governance-policy-details`
- `operator-console-ux-spec`

No merge was required because all target branches were already ancestors of the
integration branch.

## Strict Schema Validation

Command:

```powershell
python scripts/validate-contracts.py --require-jsonschema --check-formats --warnings-as-errors
```

Result:

```text
LIMA Office contract validation
- schemas parsed: 29
- examples parsed: 42
- mapped examples: 42
- schemas with examples: 29
- validation mode: full JSON Schema draft 2020-12 with format checks
- jsonschema version: 4.26.0
- unsafe-content scan: 42 example files, 81 markdown files
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
python scripts/check-doc-links.py
```

Result:

```text
LIMA Office markdown link check
- markdown files scanned: 89
- local links checked: 552
- external/anchor links ignored: 0
- failures: 0
Result: PASS
```

## Unit Tests

Command:

```powershell
python -B -m unittest discover -s tests -v
```

Result:

```text
Ran 50 tests

OK
```

## Pytest

Command:

```powershell
python -m pytest -q
```

Result:

```text
50 passed, 1 warning, 53 subtests passed
```

Warning: pytest could not create/write `.pytest_cache` because access was
denied in the local checkout. Test execution still passed.

## Compileall

Command:

```powershell
python -B -m compileall lima_office scripts tests
```

Result: PASS. Python listed and compiled modules under `lima_office`, `scripts`,
and `tests`.

## Git Diff Checks

Commands:

```powershell
git diff --check
git diff --cached --check
```

Working-tree result before staging: `git diff --check` returned exit 0 with
LF-to-CRLF warnings for Markdown files in this Windows checkout; no whitespace
errors were reported.

Cached result after staging: PASS, no whitespace errors reported.

## Git Status

Command:

```powershell
git status
```

Integration patch result before staging: modified docs only plus new
`docs/BASELINE.md`.

## CI Expectations

The CI baseline is [.github/workflows/phase0-validation.yml](../.github/workflows/phase0-validation.yml).

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
