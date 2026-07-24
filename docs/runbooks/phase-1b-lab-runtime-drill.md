# Phase 1B Lab Runtime Drill

## Purpose

Exercise a planning-approved mock lab drill to confirm fail-closed runtime
boundaries before any implementation approval.

## When To Use

- Before proposing any tiny Phase 1B implementation slice.
- After baseline refresh or audit follow-up updates.
- When planning assumptions for replay/approval/evidence linkage change.

## Prerequisites

- Canonical baseline branch and commit are recorded.
- Independent audit findings are reviewed.
- Safety patch disposition is explicitly documented.
- Required contracts and runbooks are present.
- Validation suite is green.

## Mock Lab Drill Steps

1. Prepare mock supervisor/worker/task payload set for one tenant.
2. Run worker lifecycle simulator transitions (provisioned/enrolled/active/degraded/quarantined/reenrollment/revoked/retired) and record fail-closed outcomes.
3. Validate `guardian.decision` and `guardian.replay` metadata paths.
4. Validate approval request/result/token/verification/binding chain metadata.
5. Run task lifecycle simulator transitions in mock-only mode and record fail-closed outcomes.
6. Validate replay-store/transaction/evidence linkage metadata.
7. Validate blocked-state metadata for connector/model/attestation paths.
8. Confirm no execution path performs live IO or side effects.

## Expected Fail-Closed Outcomes

- Missing or stale replay metadata blocks privileged path.
- Approval binding or token mismatch blocks privileged path.
- Tainted privileged path is denied/blocked.
- Missing evidence refs blocks evidence-required privileged transitions.
- Blocked-MVP route/connector/remediation classes remain blocked.

## Evidence To Capture

- branch and commit reviewed
- correlation IDs used in drill payloads
- related contract refs
- reason-code and taxonomy-version refs
- explicit pass/fail notes for each fail-closed scenario

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

## Escalation / Stop Conditions

- Any live connector/provider/API/external-send/remediation behavior appears.
- Any validation gate fails.
- Any critical contract/linkage mismatch is unresolved.
- Safety patch disposition is missing or contradictory.

If any stop condition occurs, halt implementation discussion and return to
planning-only plus audit remediation.

## Done Criteria

- All drill steps completed as metadata-only checks.
- All expected fail-closed outcomes observed where applicable.
- Required evidence captured and linked.
- Validation commands pass.
- Recommendation remains explicit: planning-only until separate gate approval.
