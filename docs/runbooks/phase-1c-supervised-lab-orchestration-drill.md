# Phase 1C Supervised Lab Orchestration Drill

## Purpose

Exercise a planning-approved, metadata-only supervised lab orchestration drill
without introducing runtime dispatch or side effects.

## When To Use

- Before requesting approval for a Phase 1C tiny implementation slice.
- After any Phase 1C planning update that changes gates or assumptions.
- Before independent audit sign-off for a future Phase 1C implementation branch.
- After evidence lifecycle simulator updates, before considering any next
  simulator slice.

## Prerequisites

- Current audited baseline is confirmed.
- Phase 1C plan and gate checklist are reviewed.
- Worker/task simulator audit findings are reviewed.
- Required contracts remain validated.
- Validation suite is green on branch under review.

## Mock Drill Steps

1. Prepare one-tenant mock worker and task metadata bundles.
2. Read worker simulator snapshot metadata only.
3. Read task simulator snapshot metadata only.
4. Compose a metadata-only supervisor decision envelope candidate.
5. Validate compatibility checks:
   tenant, lifecycle posture, task status, Guardian/approval linkage, and
   evidence refs.
6. Confirm fail-closed outcomes for incompatible, stale, or missing metadata.
7. Confirm no dispatch/tool/network/storage/background behavior is attempted.
8. Capture decision-envelope metadata outcome and reason codes.

## Expected Fail-Closed Outcomes

- Unknown or mismatched tenant metadata blocks orchestration outcome.
- Quarantined/revoked/retired worker posture blocks assignment-compatible states.
- Missing/invalid Guardian or approval linkage blocks executable intent.
- Missing evidence refs on evidence-required transitions blocks completion intent.
- Any blocked-MVP task class/action remains blocked.
- Evidence export/delete runtime behavior remains blocked.

## Evidence To Capture

- audited branch/commit and baseline tag reference
- simulator payload refs and correlation IDs
- compatibility-check results and reason codes
- fail-closed scenario matrix and outcomes
- validation run output summary

## Validation Commands

```powershell
python scripts/validate-contracts.py --require-jsonschema --check-formats --warnings-as-errors
python scripts/check-reason-codes.py
python scripts/check-doc-links.py
python -B -m unittest discover -s tests -v
python -m pytest -q
python -B -m compileall lima_office scripts tests
git diff --check
git diff --cached --check
git status --short --branch
```

## Stop Conditions

- Any implementation introduces IO/network/storage/background behavior.
- Any implementation introduces tool execution or dispatch behavior.
- Any implementation introduces connector/model/auth/remediation integration.
- Validation gates fail.
- Audit cannot confirm fail-closed behavior.

## Done Criteria

- Drill completed as metadata-only checks.
- Fail-closed expectations observed and recorded.
- Validation commands pass.
- Recommendation explicitly states whether implementation remains blocked.
