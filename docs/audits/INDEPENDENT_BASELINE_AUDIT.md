# Independent Baseline Audit

Audit date: May 26, 2026

## Audited target

- Branch: `integration/phase-0-1a-baseline`
- Commit: `26d5789ff62318ede69abf3296139eea7eaac8f0`
- Main reference: `origin/main = e4bb6105a9d668ddffe21892da3aaff16a0d8ca0`

## Audit result

**PASS WITH WARNINGS**

## Branch lineage findings

- Integration target commit is present and checked out at audit start.
- `main` remains untouched and matches expected hash.
- Canonical hardening chain is reachable through integration tip.
- Warning: some docs still reference pre-refresh integration hash (`0d4188d`) and need commit-pointer freshness follow-up.

## Side-branch representation findings

Side branches reviewed:

- `taxonomy-family-constraint-hardening` / `674f41d`
- `model-routing-defaults-health-taxonomy-refinement` / `ba534b2`

Findings:

- Both branches exist locally and on origin.
- Neither is a direct ancestor of integration tip.
- `ba534b2` model-routing intent appears represented in integration through merged-equivalent route hardening (`71480d7`) plus later schema/runtime/doc updates.
- `674f41d` taxonomy hardening intent appears materially represented (registry growth, runtime taxonomy coverage, reason-code gate hardening), but branch-specific "family constraint" provenance is not direct and should stay explicitly documented as non-ancestor/superseded-tracked.
- No immediate missing critical runtime-safety artifact was found from these two branches.

## Validation results

Commands executed on audit branch:

```powershell
python scripts/validate-contracts.py --require-jsonschema --check-formats --warnings-as-errors
python scripts/check-reason-codes.py
python scripts/check-doc-links.py
python -B -m unittest discover -s tests -v
python -m pytest -q
python -B -m compileall lima_office scripts tests
git diff --check
git status --short --branch
```

Results:

- `validate-contracts`: PASS (`65` schemas, `208` examples)
- `check-reason-codes`: PASS (`610` schema reason-code values, `323` example values, `227` known canonical/alias)
- `check-doc-links`: PASS (`142` markdown files, `1058` local links)
- `unittest`: PASS (`394` tests)
- `pytest -q`: PASS (`394 passed, 1 warning, 244 subtests passed`)
- `compileall`: PASS
- `git diff --check`: PASS

## Unsafe-claim scan results

Scanned for enablement claims such as deployment-ready, compliance-certified, live-connector-enabled, OAuth-enabled, and remediation-enabled.

Result:

- Matches found were defensive or blocking language (for example "not deployment-ready", "no real verifier service", "do not begin production storage/runtime services").
- No positive enablement claim for blocked runtime surfaces was identified.

## Secret/material scan results

Scanned for likely secret, token, and key indicators.

Result:

- Hits were policy text, deny rules, validation regexes, schema enum guards, and tests.
- No exposed secret material was identified in audited files.

## Safety patch findings

Patch path:

- `C:\Users\limap\Lima-Office\model-routing-health-taxonomy.partial.patch`

Status:

- Exists, untracked, uncommitted, unchanged in this audit lane.
- Size observed: `42944` bytes.
- Hash was not recorded in this run (tooling constraints).
- Patch-content keywords are materially represented in committed contracts/runtime taxonomy/model-route surfaces.
- Patch secret scan: no likely secret markers detected.

Recommended disposition:

1. Keep uncommitted through audit closeout.
2. Then either archive outside repo with traceability, or delete only by explicit approval.

## Scope boundary findings

- No runtime feature implementation added by this audit lane.
- No live connector or OAuth/provider/token runtime enablement.
- No external-send, browser-automation, remediation, or runtime-authorization expansion.
- No production or compliance-certification claim introduced.

## Remaining blockers

- Runtime authorization implementation model.
- Durable replay, transaction, and storage implementation.
- Real connector implementation gates.
- IdP, MFA, session, and device runtime enforcement.
- Real attestation, verifier, signing, and update runtime.
- Export/delete runtime implementation and legal-retention finalization.
- Safety patch final disposition decision.

## Phase 1B readiness assessment

Assessment: **planning-only readiness**

- Planning-only: acceptable after this audit.
- Tiny implementation slice: not recommended yet; safety and governance gates remain unresolved.

## Recommendation

Proceed with:

1. Phase 1B planning-only lane.
2. Explicit safety patch disposition record.
3. Commit-pointer freshness cleanup in status, baseline, and evidence docs as needed.

Do not begin:

- live connectors,
- OAuth/provider/token runtime,
- real attestation/verifier runtime,
- durable production storage/services,
- export/delete runtime,
- browser automation,
- remediation execution,
- production operations.
