# Phase 0 Validation

LIMA Office validation is a Phase 0 contract-safety check. It makes schemas,
examples, and documentation easier to enforce before Phase 1A runtime
scaffolding, but it does not authorize runtime behavior.

## Local Commands

Run contract validation:

```powershell
python scripts/validate-contracts.py
```

Run local Markdown link validation:

```powershell
python scripts/check-doc-links.py
```

Optional full JSON Schema validation dependency:

```powershell
python -m pip install -r requirements-dev.txt
```

Strict mode, matching CI:

```powershell
python scripts/validate-contracts.py --require-jsonschema --check-formats --warnings-as-errors
```

Run reason-code conformance gate:

```powershell
python scripts/check-reason-codes.py
```

## Contract Validator

[validate-contracts.py](../scripts/validate-contracts.py) checks:

- JSON syntax for every schema in [contracts/v1](../contracts/v1).
- JSON syntax for every example in [contracts/examples](../contracts/examples).
- Schema structure, including draft 2020-12 declaration, `$id`, top-level object
  type, `additionalProperties: false`, required envelope fields, and
  `contract_name`.
- No remote `$ref` dependencies.
- Example-to-schema mapping.
- Every mapped example against its intended schema when `jsonschema` is
  installed.
- Date-time and other JSON Schema formats when `--check-formats` is used.
- One or more mapped examples for every schema.
- Unsafe-content scan coverage across examples and docs.

The validator returns non-zero on parse errors, missing schema directories,
missing examples, unmapped examples, schema structure failures, failed full
schema validation, broken example coverage, or unsafe positive content.

## Reason-Code Conformance Gate

[check-reason-codes.py](../scripts/check-reason-codes.py) checks:

- Reason-code usage across all `contracts/v1/*.schema.json` and
  `contracts/examples/*.json`.
- Reason fields:
  `reason_code`, `reason_codes`, `result_reason_code`,
  `blocked_reason_code`, `quarantine_reason_code`, `denial_code`,
  `previous_reason_code`, `reasons`, `visible_reason_codes`,
  `reconciliation_reason_codes`, `evidence_reason_codes`,
  `export_delete_conflict_codes`, `conflict_codes`,
  `linkage_failure_reasons`, `reconciliation_failure_reasons`,
  `mismatch_reasons`, and enum-like `failure_reason`.
- Reason-code policy metadata fields:
  `reason_code_registry_refs`, `unknown_reason_code_policy`,
  `deprecated_reason_code_policy`, and `reason_code_status`.
- Canonical reason-code catalog from
  [lima_office/runtime/taxonomy.py](../lima_office/runtime/taxonomy.py) plus
  `reason.code.registry` examples.
- Unknown reason-code detection (fail closed).
- Deprecated-code usage enforcement requiring `reason.code.compatibility`
  coverage.
- Breaking-change compatibility record requirements (`affected_contracts` and
  `evidence_refs`).
- Blocked reason codes in success contexts (`approved`, `committed`,
  `completed`, `prepared`, `exported`, and related success statuses).
- `taxonomy_version` is mandatory for all reason-bearing schemas/examples.
- Unsupported `taxonomy_version` values fail closed.
- Versionless reason-code payloads fail closed.

The gate exits non-zero on violations.

## Example Mapping

Examples map to schemas in this order:

1. Explicit override table in [validate-contracts.py](../scripts/validate-contracts.py).
2. Declared `$schema_ref`, `schema_ref`, `contract_name`, `contract_type`, or
   `type` field when it safely resolves to a known schema.
3. Filename longest-prefix convention.

Current examples use `contract_name`, such as `approval.result`, and schema
files use the matching filename form, such as
`contracts/v1/approval.result.schema.json`. Variant examples such as
`approval.result.denied-blocked-mvp.example.json` therefore map to
`approval.result.schema.json`.

If a declared schema and filename mapping disagree, validation fails closed.

## Dependency Behavior

When Python `jsonschema` is installed, validation uses
`Draft202012Validator.check_schema` and validates each example against the mapped
draft 2020-12 schema. With `--check-formats`, the validator also uses
`FormatChecker` so fields such as `format: date-time` are checked.

When `jsonschema` is not installed, validation still parses every schema and
example, checks mapping, checks top-level schema structure, verifies required
top-level example fields, and rejects unknown top-level fields when the schema
sets `additionalProperties: false`. It prints a warning that full JSON Schema
validation requires `jsonschema`.

The fallback is a developer convenience only. It does not prove conditionals,
enums, nested object rules, formats, or all type constraints. CI uses
`--require-jsonschema`, so fallback mode cannot silently pass in CI.

## Unsafe-Content Scan

Validation blocks obvious secret material and risky plaintext field names such
as `secret_value`, `password`, `private_key`, and API-key fields unless the
surrounding text is clearly negative or blocking guidance.

Validation blocks unsafe production-ready claims, live connector enabled
language, remediation-without-approval phrasing, unrestricted tool-access
phrasing, cross-tenant access approval language, and external-send-without-
approval phrasing. Negative language such as blocked, denied, not allowed,
must not, and requires approval is expected and does not fail the scan.

This scan is a guardrail, not a data-loss-prevention system.

## CI Behavior

[phase0-validation.yml](../.github/workflows/phase0-validation.yml) runs on
`push`, `pull_request`, and `workflow_dispatch` without repository secrets. It
installs [requirements-dev.txt](../requirements-dev.txt), then runs:

```bash
python scripts/validate-contracts.py --require-jsonschema --check-formats --warnings-as-errors
python scripts/check-reason-codes.py
python scripts/check-doc-links.py
git diff --check
```

Because CI installs and requires `jsonschema` plus date-time format support,
full JSON Schema draft 2020-12 validation runs in CI.

Phase 1A runtime tests also run in CI:

```bash
python -m unittest discover -s tests -v
```

Runtime validation is stricter than the local docs fallback: the
`lima_office.contracts.ContractValidator` requires `jsonschema` and format
support and fails closed if they are unavailable.

## What Validation Does Not Prove

Validation does not prove that LIMA Office is production-ready, secure enough for
live customer data, approved for live connectors, authorized to send external
messages, or allowed to execute remediation. It does not verify identity,
approver MFA, tenant isolation at runtime, worker attestation, connector consent,
retention defaults, redaction taxonomy, audit export, customer exit/delete, or
LIMA IT separation of duties.

Validation does not replace Guardian. Future runtime behavior must still pass
through Guardian classification, approval policy, evidence capture, and
fail-closed handling before model calls, tool calls, file mutations, network
actions, connector access, outbound messages, scheduled work, secrets, or
privileged operations.

## Safe Registry Changes

To add a new reason code safely:

1. Add/update runtime registry entry in
   [lima_office/runtime/taxonomy.py](../lima_office/runtime/taxonomy.py).
2. Add `reason.code.registry` example row.
3. Add or update `reason.code.compatibility` example row.
4. Update contract examples that consume the code.
5. Add/adjust tests.
6. Run strict validation commands.

To add a reason-bearing field safely:

1. Add the field to the relevant contract with explicit reason-code semantics.
2. Require `taxonomy_version` in that contract.
3. Add/update examples with explicit `taxonomy_version`.
4. Add/update tests for unknown/deprecated/blocked/version behavior.
5. Run `python scripts/check-reason-codes.py` and confirm zero warnings/failures.

To add a new taxonomy version safely:

1. Update supported versions in
   [lima_office/runtime/taxonomy.py](../lima_office/runtime/taxonomy.py).
2. Add/adjust `reason.code.registry` and `reason.code.compatibility` examples.
3. Update reason-bearing contract examples to the intended version.
4. Add tests for supported and unsupported versions.
5. Run strict validation commands.

To deprecate/alias safely:

1. Mark status `deprecated` in registry metadata.
2. Add compatibility record (`deprecate`, `alias`, or `remove_planned`) with
   migration notes and affected contracts.
3. Keep deprecated meaning stable through migration window.
4. Ensure deprecated usage remains metadata-only where policy allows.
