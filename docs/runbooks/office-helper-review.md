# Office Operations Helper Review

## Purpose

Run or inspect the attended deterministic review of one fixed synthetic
registration scenario in the LIMA Office lab.

## Operator Steps

1. Open the Supervisor console at `/office`.
2. Select one scenario from the fixed synthetic catalog.
3. Confirm that no customer or free-form data is involved.
4. Run the helper review once.
5. Inspect the disposition, findings, recommendations, Guardian decision ID,
   and post-action evidence reference.
6. Treat all proposed task steps as drafts requiring owner review. Do not
   submit a form or dispatch Arc from this result.

## Fail-Closed Checks

The review must be denied or withheld when:

- the scenario ID is not in the fixed catalog;
- explicit confirmation is missing;
- the helper scope/assignment/result contract fails;
- Guardian denies the action;
- pre-action, Guardian, or post-action evidence cannot be written;
- any model, tool, memory, approval-token, connector, Arc, submission, or
  external-effect flag is enabled.

## Evidence Expectations

Exactly one request, one Guardian authorization, and one completion event are
expected for a successful review. Evidence may include fixed scenario IDs,
counts, hashes, posture flags, and contract identifiers. It must not include a
synthetic profile, free-form customer content, credentials, or tool output.

## Done Criteria

- Result validates as `helper.result`.
- Human review remains required.
- `submission_allowed`, `arc_dispatched`, and `external_side_effects` are false.
- Guardian and evidence references are visible to the operator.
