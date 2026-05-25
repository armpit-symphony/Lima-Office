# Reason Code Registry

Status: Phase 1A design-only taxonomy governance. Not runtime authorization.

## Purpose

Define one canonical, versioned reason-code registry so reconciliation,
evidence, export/delete, Guardian replay, approval binding, transaction, health,
and governance contracts use stable reason semantics.

## Scope

This registry governs reason-code meaning and compatibility for:

- schemas under `contracts/v1`
- examples under `contracts/examples`
- mock/in-memory runtime helpers in `lima_office/runtime`
- operator/audit metadata records

It does not authorize live runtime actions.

## Conformance Gate

Reason-code usage is enforced by
[scripts/check-reason-codes.py](../../scripts/check-reason-codes.py). The gate
scans schemas and examples, rejects unknown codes, enforces deprecated-code
compatibility coverage, blocks blocked-codes in success contexts, and validates
mandatory `taxonomy_version` for reason-bearing contracts/examples.

## Naming Rules

- Use lowercase snake_case.
- Use a category prefix where practical:
  - `recon_`, `linkage_`, `evidence_`, `export_delete_`, `guardian_`,
    `replay_`, `approval_`, `transaction_`, `health_`, `blocked_mvp_`,
    `tenant_`
- Do not reuse a code ID for a new meaning.
- Do not encode tenant/user secrets in codes.

## Taxonomy Version Rules

- Registry uses `taxonomy_version` (for example `taxonomy-reason-v1`).
- Supported values are governed in
  [lima_office/runtime/taxonomy.py](../../lima_office/runtime/taxonomy.py).
- Unknown or unsupported `taxonomy_version` values fail closed.
- Additive code addition: minor bump.
- Meaning change or category change: major bump.
- Removal is major-only and must be pre-announced as deprecated first.

## Reason Code Categories

Canonical category set:

- `reconciliation`
- `linkage`
- `evidence`
- `export_delete`
- `governance`
- `guardian`
- `replay`
- `approval_binding`
- `transaction`
- `health`
- `blocked_mvp`
- `tenant_isolation`

## Contract Families

Canonical contract-family set:

- `approval`
- `guardian`
- `replay`
- `reconciliation`
- `linkage`
- `evidence`
- `export_delete`
- `governance`
- `transaction`
- `health`
- `console`
- `supervisor`
- `worker`
- `blocked_mvp`
- `tenant_isolation`

Family/category enforcement is defined in
[lima_office/runtime/taxonomy.py](../../lima_office/runtime/taxonomy.py) and
enforced in [check-reason-codes.py](../../scripts/check-reason-codes.py).

### Family Category Rules

- `approval`: allow `approval_binding`, `guardian`, `replay`, `linkage`,
  `evidence`; disallow `export_delete`, `transaction`, `health`, `governance`
  unless explicit exception.
- `guardian`: allow `guardian`, `replay`, `linkage`, `approval_binding`,
  disallow `evidence`, `governance`, `health`, `transaction` unless explicit
  exception.
- `replay`: allow `replay`, `guardian`, `linkage`, `approval_binding`,
  `transaction`, `evidence`; disallow `health`, `governance` unless explicit
  exception.
- `reconciliation`: allow `reconciliation`, `linkage`, `evidence`, `guardian`,
  `replay`, `approval_binding`, `transaction`; disallow `health`,
  `export_delete` unless explicit exception.
- `linkage`: allow `linkage`, `reconciliation`, `approval_binding`, `guardian`,
  `replay`, `evidence`, `governance`, `health`; disallow `export_delete`
  unless explicit exception.
- `evidence`: allow `evidence`, `linkage`, `reconciliation`, `replay`,
  `transaction`, `export_delete`; disallow `health`, `governance` unless
  explicit exception.
- `export_delete`: allow `export_delete`, `evidence`; disallow `reconciliation`,
  `linkage`, `transaction`, `health`, `approval_binding` unless explicit
  exception.
- `governance`: allow `governance`, `export_delete`, `evidence`,
  `reconciliation`, `linkage`; disallow `health`, `approval_binding`,
  `transaction` unless explicit exception.
- `transaction`: allow `transaction`, `linkage`, `reconciliation`, `evidence`,
  `replay`, `approval_binding`; disallow `health`, `governance` unless explicit
  exception.
- `health`: allow `health`, `evidence`, `guardian`, `approval_binding`;
  disallow `transaction`, `export_delete`, `reconciliation` unless explicit
  exception.
- `console`: allow `health`, `evidence`, `governance`, `export_delete`,
  `reconciliation`, `linkage`; disallow `approval_binding`, `transaction`
  unless explicit exception.
- `supervisor`: allow `health`, `evidence`, `guardian`, `approval_binding`,
  `reconciliation`, `linkage`; disallow `transaction`, `export_delete` unless
  explicit exception.
- `worker`: allow `health`, `evidence`, `governance`, `guardian`, `linkage`;
  disallow `transaction`, `export_delete`, `approval_binding` unless explicit
  exception.
- `blocked_mvp`: allow only `blocked_mvp`.
- `tenant_isolation`: allow only `tenant_isolation`.

### Cross-Family Exceptions

- `blocked_mvp` and `tenant_isolation` categories are explicit cross-cutting
  exceptions and must still fail closed when mismatched to success contexts.
- Field-level constraints still apply:
  `reconciliation_reason_codes` must be one of reconciliation/linkage/
  tenant_isolation/blocked_mvp, `evidence_reason_codes` must be one of
  evidence/export_delete/tenant_isolation/blocked_mvp, and
  `export_delete_conflict_codes`/`conflict_codes` must be one of
  export_delete/tenant_isolation/blocked_mvp.

### Evidence And Fail-Closed Rules

- Family mismatch is always fail-closed.
- Any blocked/critical code in success-complete contexts is rejected.
- Deprecated alias handling is metadata-only and cannot bypass family checks.
- Cross-family exceptions do not bypass evidence requirements for blocked or
  critical reason outcomes.

## Registry Runtime Parity

- Canonical registry catalog:
  [contracts/taxonomy/reason-code-registry.catalog.json](../../contracts/taxonomy/reason-code-registry.catalog.json)
- Runtime registry source:
  [lima_office/runtime/taxonomy.py](../../lima_office/runtime/taxonomy.py)
- CI rejects:
  - registry-only codes missing in runtime
  - runtime-only codes missing in catalog
  - metadata drift (`category`, `status`, `severity`, `aliases`,
    `replaced_by`, `evidence_required`, `fail_closed_required`)

## Code Format Convention

- `reason_code` is a stable string identifier.
- Human wording may evolve in docs/UI.
- Contracts store code IDs, not free-form diagnostic prose, for policy
  decisions.

## Severity Mapping

- `info`: metadata-only, non-terminal
- `warning`: review-required
- `degraded`: degraded posture, no privilege escalation
- `blocked`: fail-closed denial/block
- `critical`: severe blocked/fail-closed state with incident posture

## Actor-Visible vs Internal-Only Classification

- `operator_visible`: safe for operator status surfaces
- `auditor_visible`: safe for evidence/audit trails
- `internal_only`: diagnostic or implementation-facing metadata

Visibility classification does not change authorization outcome.

## Evidence Requirement Mapping

Each registry record declares:

- `evidence_required`
- `fail_closed_required`

Rules:

- `blocked`/`critical` codes should require evidence refs.
- Codes used in denial/failure paths should set `fail_closed_required: true`.

## Deprecation Rules

- Deprecation sets status to `deprecated`.
- Deprecated codes keep original meaning frozen.
- Deprecated codes must carry `replaced_by` or explicit no-replacement note.
- Deprecation must include migration notes in compatibility records.

## Alias and Migration Rules

- Aliases are allowed only for compatibility migration.
- Alias records must map one legacy code to one canonical active code.
- Runtime helpers may normalize aliases for metadata display only.
- Authorization-sensitive paths must evaluate canonical active code semantics.

## Backwards Compatibility Rules

- Unknown codes are fail-closed by default for authorization/reconciliation/
  export/delete decision paths.
- Deprecated codes may be accepted with warning for metadata-only records where
  policy allows.
- Contracts/examples that carry reason-bearing fields must include
  `taxonomy_version`.
- New or changed code semantics must include a matching compatibility record.

## Blocked and Removal Rules

- `blocked` status means code cannot represent an authorized/completed
  privileged outcome.
- `reserved` status means code ID is held and must not be emitted.
- Removal is not silent:
  - mark `deprecated`
  - publish compatibility record
  - update examples/tests/docs
  - remove only in major taxonomy version after migration window

## MVP Non-Goals

- No dynamic online registry service
- No database-backed taxonomy engine
- No auto-migration runtime job
- No live operator UI implementation in this lane
