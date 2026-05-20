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
