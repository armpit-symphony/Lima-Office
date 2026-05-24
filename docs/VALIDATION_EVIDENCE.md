# Validation Evidence

This file records the validation baseline for the Phase 0 / Phase 1A closeout,
canonical integration branch, and Phase 1A invariant checkpoint v2. Validation
is not production certification and does not approve live connectors, external
sends, real remediation, production operations, or customer-system mutation.

Latest captured run: `reason-code-conformance-ci-gate` on Windows with
Python 3.12.10.

## Canonical Integration Branch

- Base branch: `integration/phase-0-1a-baseline`
- Base commit: `f64d3a0447a76b24a5213487ce8836cb21511882`
- Invariant checkpoint branch: `phase-1a-invariant-checkpoint-v2`
- Approval binding branch: `approval-token-runtime-binding-design`
- Guardian expiry/replay branch: `guardian-expiry-replay-policy-design`
- Durable replay/evidence posture branch: `durable-replay-evidence-posture`
- Durable transaction/storage RFC branch: `durable-transaction-storage-rfc`
- Durable transaction coordinator branch: `durable-transaction-coordinator-design`
- Cross-contract linkage hardening branch: `cross-contract-linkage-hardening`
- Approval Guardian reconciliation drills branch:
  `approval-guardian-linkage-reconciliation-drills`
- Governance export/delete taxonomy finalization branch:
  `governance-export-delete-taxonomy-finalization`
- Reason-code registry compatibility policy branch:
  `reason-code-registry-compatibility-policy`
- Reason-code conformance CI gate branch:
  `reason-code-conformance-ci-gate`
- Included branches and excluded checkpoints are listed in
  [Baseline](BASELINE.md).
- `main` was not updated by this validation evidence.

## Invariant Branch Reconciliation

Commands:

```powershell
git fetch --all --prune
git cat-file -t e71431007ddbe96c3e141b77591efc2508c53e5d
git ls-remote --heads origin phase-1a-cross-contract-invariants
```

Result:

```text
git fetch --all --prune: PASS
git cat-file -t e71431007ddbe96c3e141b77591efc2508c53e5d: fatal: git cat-file: could not get object info
git ls-remote --heads origin phase-1a-cross-contract-invariants: no matching head returned
```

Conclusion: `e71431007ddbe96c3e141b77591efc2508c53e5d` does not exist in this
local checkout after fetch, and `origin/phase-1a-cross-contract-invariants` is
not advertised. [Cross-Contract Invariants](CROSS_CONTRACT_INVARIANTS.md)
documents the reachable v2 checkpoint that supersedes the absent commit.

## Branch Inclusion Checks

The v2 checkpoint was created from `integration/phase-0-1a-baseline`, which had
already verified the reachable stabilization targets as ancestors:

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

## Approval Binding Checkpoint

This branch adds `approval.binding` and `approval.chain` contracts and
mock/in-memory approval binding tests. Validation remains repository health
evidence only; it does not approve live connectors, external sends, real
remediation, durable services, production operations, or customer-system
mutation.

## Guardian Expiry Replay Checkpoint

This branch adds `guardian.decision` expiry/replay fields, a `guardian.replay`
metadata contract, sanitized examples, a mock/in-memory Guardian decision
replay verifier, and fail-closed tests. Validation remains repository health
evidence only; it does not approve live connectors, external sends, real
remediation, durable services, production operations, or customer-system
mutation.

## Durable Replay Evidence Posture Checkpoint

This branch adds durable replay/evidence posture design docs, new
`replay.store.record` and `evidence.export_manifest` contracts with examples,
mock/in-memory replay-store/export-manifest helpers, cross-contract invariant
hardening, and fail-closed tests. Validation remains repository health evidence
only; it does not approve databases, queues, durable storage services, live
connectors, external sends, real remediation, production operations, or
customer-system mutation.

## Durable Transaction Storage RFC Checkpoint

This branch adds durable transaction/storage architecture docs, new
`transaction.boundary` and `evidence.ledger.entry` contracts with sanitized
examples, and mock-only validation tests for transaction and ledger metadata.
Validation remains repository health evidence only; it does not approve
databases, queues, durable storage services, live connectors, external sends,
real remediation, production operations, or customer-system mutation.

## Durable Transaction Coordinator Design Checkpoint

This branch adds coordinator architecture and recovery/failure-drill runbooks,
new `transaction.coordinator.event` contracts with sanitized examples, and a
mock-only in-memory transition/idempotency validator with fail-closed tests.
Validation remains repository health evidence only; it does not approve
databases, queues, durable storage services, live connectors, external sends,
real remediation, production operations, or customer-system mutation.

## Cross-Contract Linkage Hardening Checkpoint

This branch adds cross-contract linkage posture docs, linkage-status and
canonical-linkage fields across transaction/replay/evidence contracts, a
mock-only in-memory linkage validator, and negative-path linkage drift tests.
Validation remains repository health evidence only; it does not approve
databases, queues, durable storage services, live connectors, external sends,
real remediation, production operations, or customer-system mutation.

## Approval Guardian Reconciliation Drills Checkpoint

This branch adds approval/Guardian reconciliation drill docs and runbook,
reconciliation conditionals across approval/Guardian/replay/transaction/ledger
contracts, a mock-only in-memory reconciler, and fail-closed
approval/Guardian drift tests. Validation remains repository health evidence
only; it does not approve databases, queues, durable storage services, live
connectors, external sends, real remediation, production operations, or
customer-system mutation.

## Governance Export Delete Taxonomy Finalization Checkpoint

This branch adds reconciliation and evidence reason taxonomy docs,
export/delete conflict governance policy and runbook docs, taxonomy-aware
governance review contracts and examples, mock-only taxonomy conflict
classification helper logic, and fail-closed tests for blocked/conflict/
redaction/hold conditions. Validation remains repository health evidence only;
it does not approve export or delete implementation, databases, queues, durable
storage services, live connectors, external sends, real remediation, production
operations, or customer-system mutation.

## Reason-Code Registry Compatibility Policy Checkpoint

This branch adds a canonical reason-code registry and compatibility policy docs,
new reason-code registry/compatibility contracts and examples, schema-level
reason-code policy fields and fail-closed conditionals across decision-relevant
contracts, and mock-only runtime taxonomy compatibility tests. Validation
remains repository health evidence only; it does not approve runtime
authorization expansion, export/delete execution, databases, queues, durable
storage services, live connectors, external sends, real remediation, production
operations, or customer-system mutation.

## Reason-Code Conformance CI Gate Checkpoint

This branch adds a fail-closed reason-code conformance gate in
`scripts/check-reason-codes.py`, a CI workflow step, expanded taxonomy runtime
catalog entries for existing contract/example reason codes, and dedicated tests
in `tests/test_reason_code_conformance_ci.py`.
Validation remains repository health evidence only; it does not approve runtime
authorization expansion, export/delete execution, durable storage services, live
connectors, external sends, real remediation, production operations, or
customer-system mutation.

## Strict Schema Validation

Command:

```powershell
python scripts/validate-contracts.py --require-jsonschema --check-formats --warnings-as-errors
```

Result:

```text
LIMA Office contract validation
- schemas parsed: 41
- examples parsed: 107
- mapped examples: 107
- schemas with examples: 41
- validation mode: full JSON Schema draft 2020-12 with format checks
- jsonschema version: 4.26.0
- unsafe-content scan: 107 example files, 99 markdown files
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

## Reason-Code Conformance Check

Command:

```powershell
python scripts/check-reason-codes.py
```

Result:

```text
LIMA Office reason-code conformance
- schemas scanned: 41
- examples scanned: 107
- known canonical/alias codes: 63
- reason-code values scanned in schemas: 63
- reason-code values scanned in examples: 64
- blocked-in-success violations: 0
- warnings: 17
- failures: 0
Result: PASS
```

Notes:

- The gate fails closed on unknown codes, deprecated-code compatibility gaps,
  blocked-codes in success contexts, breaking-change coverage gaps, and missing
  schema-required taxonomy versions.
- Current warnings reflect legacy schemas that use reason-bearing fields but do
  not yet require `taxonomy_version`. This remains an open governance question.

## Doc Link Check

Command:

```powershell
python scripts/check-doc-links.py
```

Result:

```text
LIMA Office markdown link check
- markdown files scanned: 107
- local links checked: 806
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
Ran 218 tests

OK
```

Coverage added by this checkpoint:

- Cross-contract invariant checks.
- Guardian decision expiry/staleness checks.
- Approval-token verification binding checks.
- Evidence-required completion checks.
- Worker state and capability routing checks.
- Taint propagation checks for tool and memory paths.
- LIMA IT remediation blocking checks.
- Helper scope overreach checks.
- Supervisor health reporting checks.
- Approval binding checks for one-time use, replay, expiry, revocation,
  tenant/task/worker/action/tool scope/Guardian mismatch, blocked-MVP action,
  LIMA IT remediation, tainted input, missing evidence, and approval-required
  task enqueue binding.
- Guardian expiry/replay checks for first-use success, replay denial, expiry,
  stale decision age, missing expiry, future-effective timestamp beyond skew,
  clock-skew allowance, tenant/task/worker/action/tool-scope mismatch, decision
  scope hash mismatch, approval-binding mismatch, blocked-MVP action, LIMA IT
  remediation block, external-send/live-connector block, ambiguous timestamp,
  missing evidence, missing required requested-action fields, contradictory
  timestamp ordering, and nonce non-consumption on failed validation.
- Durable replay/evidence posture checks for consumed and replay-denied replay
  store records, failed-closed atomicity blocks, nonce double-consume denial,
  tenant/action/scope mismatch, denial-path evidence artifact validation,
  tenant-consistent evidence chains, refs-only export manifests, raw/secret
  export deny, delete/export conflict deny posture, and replay-store
  unavailable fail-closed behavior.
- Durable transaction/storage RFC checks for transaction-boundary schema
  examples, evidence-ledger schema examples, failed-closed failure/evidence
  requirements, committed/rolled-back timestamp requirements, raw/secret
  metadata exclusion, metadata-only hash fields, refs-only export-manifest
  transaction posture, and explicit no-real-storage authorization.
- Durable transaction coordinator design checks for coordinator event schema
  examples, transition-order enforcement, tenant-scoped idempotency collision
  handling, failed-closed/rolled-back evidence requirements, replay/token/
  evidence reference requirements, reconciliation evidence requirements, and
  explicit no-real-action authorization.
- Approval/Guardian reconciliation drill checks for valid chain reconciliation,
  stale/missing/mismatched linkage failures, replay/coordinator/transaction/
  ledger mismatch handling, cross-tenant isolation, blocked-MVP action classes,
  denial-path evidence enforcement, and explicit no-real-action authorization.
- Governance export/delete taxonomy checks for recognized reason-code
  enforcement, unknown-code fail-closed behavior, review-schema conflict
  evidence requirements, blocked-MVP completion denial, preservation-hold
  delete blocking, exported-manifest redaction requirements, failed-closed
  evidence requirements, and explicit no-real-action authorization.
- Reason-code registry compatibility checks for active/deprecated/blocked
  registry entry validation, unknown-code fail-closed handling, alias-to-
  replacement normalization, breaking-change compatibility requirements, and
  explicit no-real-action authorization.

## Pytest

Command:

```powershell
python -m pytest -q
```

Result:

```text
218 passed, 1 warning, 143 subtests passed
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
LF-to-CRLF warnings for files in this Windows checkout; no whitespace errors
were reported.

Cached result after staging: PASS, no whitespace errors reported.

## Git Status

Command:

```powershell
git status
```

Checkpoint patch result before staging: modified runtime mock hardening, tests,
schemas/examples, and documentation only, including governance export/delete
taxonomy hardening plus canonical reason-code registry compatibility policy
hardening for lifecycle/deprecation/alias metadata, schema conditionals, and
mock fail-closed helper coverage.

## CI Expectations

The CI baseline is [.github/workflows/phase0-validation.yml](../.github/workflows/phase0-validation.yml).

Expected CI commands:

```bash
python scripts/validate-contracts.py --require-jsonschema --check-formats --warnings-as-errors
python scripts/check-reason-codes.py
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
