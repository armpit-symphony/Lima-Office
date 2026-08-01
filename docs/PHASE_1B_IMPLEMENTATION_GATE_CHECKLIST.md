# Phase 1B Implementation Gate Checklist

Date: May 26, 2026

Use this checklist before approving any Phase 1B implementation branch.

## Gate Checklist

- [ ] Independent audit result is pass and reviewed.
- [ ] Safety patch disposition is complete and explicitly recorded.
- [ ] Integration baseline branch is refreshed and canonical.
- [ ] No open critical docs/contracts inconsistency exists.
- [ ] `python scripts/validate-contracts.py --require-jsonschema --check-formats --warnings-as-errors` passes.
- [ ] `python scripts/check-reason-codes.py` passes.
- [ ] `python scripts/check-doc-links.py` passes.
- [ ] `python -B -m unittest discover -s tests -v` passes.
- [ ] `python -m pytest -q` passes.
- [ ] `python -B -m compileall lima_office scripts tests` passes.
- [ ] `git diff --check` passes.
- [ ] `git diff --cached --check` passes.
- [ ] No new live connector behavior is introduced.
- [ ] No new external IO behavior is introduced.
- [ ] No durable storage/service behavior is introduced unless explicitly approved.
- [ ] No runtime authorization expansion exists beyond mock lab boundaries.
- [ ] No production-readiness or compliance-certification claim language exists.
- [ ] Fail-closed tests exist for replay, approval binding, taint, blocked-MVP,
      and missing evidence/linkage paths.

## Merge Strategy Recommendation

- Use a dedicated implementation branch with explicit scope boundaries.
- Require review from security, architecture, SRE, compliance, AI runtime, and
  product-scope owners.
- Require green validation and test gates before merge.
- Merge only after written gate sign-off; do not merge directly to `main`.
