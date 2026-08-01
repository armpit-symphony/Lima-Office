# Audit Prep Checklist

Date: May 26, 2026

Use this checklist before independent baseline audit or merge-gate sign-off.

## Scope boundaries

- [ ] Confirm review is docs/contracts/tests/mock-hardening only.
- [ ] Confirm no runtime/live connector implementation is included.
- [ ] Confirm no production-readiness or compliance-certification claim language.

## Validation commands

- [ ] `python scripts/validate-contracts.py --require-jsonschema --check-formats --warnings-as-errors`
- [ ] `python scripts/check-reason-codes.py`
- [ ] `python scripts/check-doc-links.py`
- [ ] `python -B -m unittest discover -s tests -v`
- [ ] `python -m pytest -q`
- [ ] `python -B -m compileall lima_office scripts tests`
- [ ] `git diff --check`
- [ ] `git diff --cached --check`

## Safety scans

- [ ] Confirm no secret/token/provider credential content in docs/examples.
- [ ] Confirm no runtime authorization expansion in this lane.
- [ ] Confirm no live connector behavior claims.

## Docs/contracts consistency

- [ ] `STATUS.md`, `docs/BASELINE.md`, `docs/NEXT_PHASE_PLAN.md`, and `docs/VALIDATION_EVIDENCE.md` are branch/commit aligned.
- [ ] Schema/example counts in validation evidence match latest run.
- [ ] Reason-code/taxonomy references are consistent with registry.

## Runtime non-expansion verification

- [ ] No new live provider/API/client behavior.
- [ ] No OAuth/OIDC/SAML runtime wiring.
- [ ] No token runtime storage or rotation behavior.
- [ ] No remediation execution behavior.

## No-live-connector verification

- [ ] No connector API execution path added.
- [ ] No browser automation path added.
- [ ] No external send path added.

## No-production-claim verification

- [ ] No production readiness claim.
- [ ] No compliance certification claim.

## Branch/commit verification

- [ ] Capture current branch and HEAD commit.
- [ ] Capture latest checkpoint branch/commit.
- [ ] Confirm `main` unchanged unless explicitly approved.

## Safety patch disposition

- [ ] Document status of `model-routing-health-taxonomy.partial.patch`.
- [ ] Keep uncommitted unless explicit instruction says archive/promote/delete.
