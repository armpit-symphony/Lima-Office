# Approval Guardian Reconciliation Drill

## Purpose

Run deterministic tabletop checks that prove approval, Guardian, replay,
transaction, and evidence metadata fail closed when linkage drift is detected.

## When To Run

- Before merging approval/Guardian linkage contract changes.
- After reconciliation helper or invariant changes.
- During incident review for replay, approval, or evidence drift signals.

## Preconditions

- Latest schemas and examples validate.
- Reconciliation tests are runnable in local mock mode.
- Operator has access to drill evidence and validation outputs.

## Drill Scenarios

1. Missing Guardian decision.
2. Stale or expired Guardian decision.
3. Approval binding mismatch.
4. Token verification mismatch.
5. Replay record mismatch or missing replay record.
6. Coordinator event/transaction mismatch.
7. Evidence ledger mismatch.
8. Cross-tenant linkage attempt.
9. Blocked-MVP authorization attempt (`external_send`,
   `live_connector_access`, `lima_it_remediation`).
10. Denial path missing evidence references.

## Operator Steps

1. Build a known-good linkage bundle.
2. Mutate one field for a single drill scenario.
3. Run targeted reconciliation tests.
4. Confirm expected blocked status and reason code.
5. Capture contract-validation and test outputs.
6. Restore baseline bundle and repeat next scenario.

## Evidence To Capture

- Reconciliation status output.
- Reconciliation failure reasons.
- Reconciliation evidence refs.
- Contract validation pass/fail output.
- Test command output and failing assertion text when expected.

## Expected Fail-Closed Outcomes

- Non-reconciled status for every negative-path scenario.
- `can_authorize` remains `false`.
- No external side-effect path is enabled.
- Blocked-MVP classes remain blocked.

## Escalation

Escalate to security/compliance reviewers when:

- Cross-tenant linkage appears.
- Denial evidence is missing on denied/replay-denied outcomes.
- Reconciliation outcome is ambiguous across repeated runs.

## Done Criteria

- All drill scenarios executed.
- Expected fail-closed outcomes observed.
- Evidence captured for each scenario.
- No scenario produces an authorization-valid result.
