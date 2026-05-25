#!/usr/bin/env python3
"""Fail-closed reason-code conformance checks for contracts and examples."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "contracts" / "v1"
EXAMPLE_DIR = ROOT / "contracts" / "examples"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lima_office.runtime.errors import PolicyDenyError
from lima_office.runtime.taxonomy import (
    CONTRACT_FAMILY_BY_SCHEMA_KEY,
    validate_taxonomy_version,
    validate_reason_code_for_family,
    validate_registry_entry_metadata,
    validate_registry_runtime_parity,
    expected_taxonomy_family_for_schema_key,
    get_contract_family_for_schema_key,
)

REASON_VALUE_FIELDS = frozenset(
    {
        "reason_code",
        "reason_codes",
        "result_reason_code",
        "blocked_reason_code",
        "quarantine_reason_code",
        "denial_code",
        "previous_reason_code",
        "reasons",
        "visible_reason_codes",
        "reconciliation_reason_codes",
        "evidence_reason_codes",
        "export_delete_conflict_codes",
        "conflict_codes",
        "linkage_failure_reasons",
        "reconciliation_failure_reasons",
        "mismatch_reasons",
    }
)
REASON_CODE_POLICY_FIELDS = frozenset(
    {
        "reason_code_registry_refs",
        "reason_code_status",
        "unknown_reason_code_policy",
        "deprecated_reason_code_policy",
    }
)
REASON_VALUE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
PLACEHOLDER_PATTERN = re.compile(r".*_placeholder$")
SCHEMA_TAXONOMY_ALLOWLIST = frozenset()
PLACEHOLDER_ALLOWLIST = frozenset(
    {
        "blocked_mvp_placeholder",
    }
)

FIELD_CATEGORY_CONSTRAINTS: dict[str, frozenset[str]] = {
    "reconciliation_reason_codes": frozenset(
        {"reconciliation", "linkage", "tenant_isolation", "blocked_mvp"}
    ),
    "evidence_reason_codes": frozenset(
        {"evidence", "export_delete", "tenant_isolation", "blocked_mvp"}
    ),
    "export_delete_conflict_codes": frozenset({"export_delete", "tenant_isolation", "blocked_mvp"}),
    "conflict_codes": frozenset({"export_delete", "tenant_isolation", "blocked_mvp"}),
}

FAMILY_VALIDATION_EXEMPT_SCHEMA_KEYS = frozenset(
    {
        "reason.code.registry",
        "reason.code.compatibility",
    }
)

SUCCESS_STATUS_BY_FIELD = {
    "status": frozenset(
        {
            "approved",
            "allowed",
            "committed",
            "completed",
            "exported",
            "prepared",
            "succeeded",
            "reconciled",
            "valid_first_use",
        }
    ),
    "approval_result": frozenset({"approved"}),
    "decision": frozenset({"approved"}),
    "delete_review_status": frozenset({"approved"}),
    "event_status": frozenset({"succeeded"}),
    "export_review_status": frozenset({"approved", "prepared", "exported"}),
    "export_status": frozenset({"prepared", "exported"}),
    "result": frozenset({"approved"}),
    "reconciliation_status": frozenset({"reconciled"}),
    "replay_check_result": frozenset({"valid_first_use"}),
    "transaction_status": frozenset({"committed"}),
}


@dataclass(frozen=True)
class LocatedCode:
    code: str
    field: str
    path: str


@dataclass(frozen=True)
class LoadedJson:
    path: Path
    data: Any


@dataclass
class CheckResult:
    failures: list[str]
    warnings: list[str]

    def fail(self, message: str) -> None:
        self.failures.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def load_json(path: Path, result: CheckResult) -> LoadedJson | None:
    try:
        return LoadedJson(path=path, data=json.loads(path.read_text(encoding="utf-8")))
    except JSONDecodeError as exc:
        result.fail(f"{rel(path)}: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}")
    except OSError as exc:
        result.fail(f"{rel(path)}: cannot read file: {exc}")
    return None


def schema_key_from_path(path: Path) -> str:
    suffix = ".schema.json"
    if not path.name.endswith(suffix):
        raise ValueError(f"schema path does not end with {suffix}: {path}")
    return path.name[: -len(suffix)]


def schema_key_from_filename(path: Path, schema_keys: set[str]) -> str | None:
    base = path.name
    if base.endswith(".json"):
        base = base[:-5]
    if base.endswith(".example"):
        base = base[:-8]
    # Deterministic tie-break avoids non-reproducible mapping when names share a prefix length.
    for key in sorted(schema_keys, key=lambda item: (-len(item), item)):
        if base == key or base.startswith(f"{key}."):
            return key
    return None


def map_example_to_schema(example: LoadedJson, schema_keys: set[str]) -> str | None:
    if isinstance(example.data, dict):
        declared = example.data.get("contract_name")
        if isinstance(declared, str) and declared in schema_keys:
            return declared
    return schema_key_from_filename(example.path, schema_keys)


def infer_contract_family(schema_key: str, schema_data: Any) -> str | None:
    if schema_key in CONTRACT_FAMILY_BY_SCHEMA_KEY:
        return CONTRACT_FAMILY_BY_SCHEMA_KEY[schema_key]
    if isinstance(schema_data, dict):
        properties = schema_data.get("properties")
        if isinstance(properties, dict):
            contract_name = properties.get("contract_name")
            if isinstance(contract_name, dict):
                const_name = contract_name.get("const")
                if isinstance(const_name, str):
                    family = get_contract_family_for_schema_key(const_name)
                    if family is not None:
                        return family
    return get_contract_family_for_schema_key(schema_key)


def expected_taxonomy_family(schema_key: str) -> str | None:
    return expected_taxonomy_family_for_schema_key(schema_key)


def extract_codes_for_field(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def walk_reason_fields(value: Any, path: str = "$") -> list[tuple[str, Any, str]]:
    found: list[tuple[str, Any, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in REASON_VALUE_FIELDS or key == "failure_reason":
                found.append((key, child, child_path))
            found.extend(walk_reason_fields(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(walk_reason_fields(child, f"{path}[{index}]"))
    return found


def gather_reason_codes_from_schema(schema: LoadedJson) -> list[LocatedCode]:
    codes: list[LocatedCode] = []
    for field, value, field_path in walk_reason_fields(schema.data):
        for code in extract_codes_for_field(value):
            if field == "failure_reason" and not REASON_VALUE_PATTERN.fullmatch(code):
                continue
            if REASON_VALUE_PATTERN.fullmatch(code):
                codes.append(LocatedCode(code=code, field=field, path=field_path))
            continue
        if isinstance(value, dict):
            codes.extend(gather_reason_codes_from_schema_fragment(value, field, field_path))
    return codes


def gather_reason_codes_from_schema_fragment(
    schema_fragment: dict[str, Any], field: str, field_path: str
) -> list[LocatedCode]:
    found: list[LocatedCode] = []
    enum_values = schema_fragment.get("enum")
    if isinstance(enum_values, list):
        for item in enum_values:
            if isinstance(item, str) and REASON_VALUE_PATTERN.fullmatch(item):
                if field == "failure_reason" and not REASON_VALUE_PATTERN.fullmatch(item):
                    continue
                found.append(LocatedCode(code=item, field=field, path=f"{field_path}.enum"))
    const_value = schema_fragment.get("const")
    if isinstance(const_value, str) and REASON_VALUE_PATTERN.fullmatch(const_value):
        found.append(LocatedCode(code=const_value, field=field, path=f"{field_path}.const"))

    for key in ("items", "anyOf", "oneOf", "allOf"):
        child = schema_fragment.get(key)
        if isinstance(child, dict):
            found.extend(gather_reason_codes_from_schema_fragment(child, field, f"{field_path}.{key}"))
        elif isinstance(child, list):
            for index, item in enumerate(child):
                if isinstance(item, dict):
                    found.extend(
                        gather_reason_codes_from_schema_fragment(
                            item, field, f"{field_path}.{key}[{index}]"
                        )
                    )
    return found


def gather_reason_codes_from_example(example: LoadedJson) -> list[LocatedCode]:
    codes: list[LocatedCode] = []
    for field, value, field_path in walk_reason_fields(example.data):
        for code in extract_codes_for_field(value):
            if field == "failure_reason" and not REASON_VALUE_PATTERN.fullmatch(code):
                continue
            if REASON_VALUE_PATTERN.fullmatch(code):
                codes.append(LocatedCode(code=code, field=field, path=field_path))
    return codes


def schema_uses_reason_model(schema_data: Any) -> bool:
    fields = REASON_VALUE_FIELDS | REASON_CODE_POLICY_FIELDS | {"failure_reason"}

    def _walk(node: Any) -> bool:
        if isinstance(node, dict):
            properties = node.get("properties")
            if isinstance(properties, dict) and set(properties).intersection(fields):
                return True
            return any(_walk(child) for child in node.values())
        if isinstance(node, list):
            return any(_walk(child) for child in node)
        return False

    return _walk(schema_data)


def schema_requires_taxonomy_version(schema_data: Any) -> bool:
    if not isinstance(schema_data, dict):
        return False
    required = schema_data.get("required")
    if not isinstance(required, list):
        return False
    return "taxonomy_version" in required


def schema_has_taxonomy_version_property(schema_data: Any) -> bool:
    if not isinstance(schema_data, dict):
        return False
    properties = schema_data.get("properties")
    if not isinstance(properties, dict):
        return False
    return "taxonomy_version" in properties


def validate_supported_taxonomy_version(
    source_path: Path,
    payload: Any,
    result: CheckResult,
    *,
    expected_family: str | None = None,
) -> None:
    if not isinstance(payload, dict):
        result.fail(f"{rel(source_path)}: expected object payload for taxonomy_version validation")
        return
    version = payload.get("taxonomy_version")
    if not isinstance(version, str) or not version:
        result.fail(f"{rel(source_path)}: missing taxonomy_version for reason-bearing payload")
        return
    try:
        validate_taxonomy_version(version, expected_family=expected_family)
    except PolicyDenyError as exc:
        result.fail(f"{rel(source_path)}: {exc}")


def looks_successful(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False

    def _walk(value: Any) -> bool:
        if isinstance(value, dict):
            for key, child in value.items():
                if key in SUCCESS_STATUS_BY_FIELD and isinstance(child, str):
                    if child in SUCCESS_STATUS_BY_FIELD[key]:
                        return True
                if _walk(child):
                    return True
        elif isinstance(value, list):
            for item in value:
                if _walk(item):
                    return True
        return False

    return _walk(payload)


def is_placeholder_code(code: str) -> bool:
    return bool(PLACEHOLDER_PATTERN.fullmatch(code))


def load_registry_examples(result: CheckResult, example_dir: Path) -> dict[str, dict[str, Any]]:
    registry_entries: dict[str, dict[str, Any]] = {}
    for path in sorted(example_dir.rglob("reason.code.registry.*.json")):
        loaded = load_json(path, result)
        if loaded is None or not isinstance(loaded.data, dict):
            continue
        code = loaded.data.get("reason_code")
        if not isinstance(code, str) or not code:
            result.fail(f"{rel(path)}: missing reason_code")
            continue
        status = loaded.data.get("status")
        if not isinstance(status, str) or not status:
            result.fail(f"{rel(path)}: missing status")
            continue
        aliases = loaded.data.get("aliases")
        alias_values = [item for item in aliases if isinstance(item, str)] if isinstance(aliases, list) else []
        registry_entries[code] = {
            "status": status,
            "replaced_by": loaded.data.get("replaced_by"),
            "aliases": alias_values,
            "taxonomy_version": loaded.data.get("taxonomy_version"),
        }
    return registry_entries


def load_compatibility_examples(
    result: CheckResult, example_dir: Path
) -> tuple[set[str], list[LoadedJson]]:
    covered_deprecated_codes: set[str] = set()
    loaded_examples: list[LoadedJson] = []
    for path in sorted(example_dir.rglob("reason.code.compatibility.*.json")):
        loaded = load_json(path, result)
        if loaded is None or not isinstance(loaded.data, dict):
            continue
        loaded_examples.append(loaded)
        previous = loaded.data.get("previous_reason_code")
        if isinstance(previous, str) and previous:
            covered_deprecated_codes.add(previous)

        if loaded.data.get("compatibility_status") == "breaking_change":
            affected = loaded.data.get("affected_contracts")
            evidence_refs = loaded.data.get("evidence_refs")
            if not isinstance(affected, list) or not affected:
                result.fail(
                    f"{rel(path)}: breaking_change record must include non-empty affected_contracts"
                )
            if not isinstance(evidence_refs, list) or not evidence_refs:
                result.fail(f"{rel(path)}: breaking_change record must include non-empty evidence_refs")
    return covered_deprecated_codes, loaded_examples


def load_registry_catalog(
    result: CheckResult, catalog_path: Path
) -> tuple[str | None, dict[str, dict[str, Any]]]:
    loaded = load_json(catalog_path, result)
    if loaded is None or not isinstance(loaded.data, dict):
        return None, {}

    taxonomy_version = loaded.data.get("taxonomy_version")
    if not isinstance(taxonomy_version, str) or not taxonomy_version:
        result.fail(f"{rel(catalog_path)}: missing taxonomy_version")
        return None, {}
    try:
        validate_taxonomy_version(taxonomy_version, expected_family="reason")
    except PolicyDenyError as exc:
        result.fail(f"{rel(catalog_path)}: {exc}")

    rows = loaded.data.get("reason_codes")
    if not isinstance(rows, list):
        result.fail(f"{rel(catalog_path)}: reason_codes must be an array")
        return taxonomy_version, {}

    catalog: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            result.fail(f"{rel(catalog_path)}: reason_codes[{index}] must be an object")
            continue
        code = row.get("reason_code")
        if not isinstance(code, str) or not code:
            result.fail(f"{rel(catalog_path)}: reason_codes[{index}] missing reason_code")
            continue
        catalog[code] = row
    return taxonomy_version, catalog


def build_known_reason_catalog(
    registry_catalog: dict[str, dict[str, Any]],
    catalog_path: Path,
    result: CheckResult,
) -> tuple[set[str], dict[str, str], dict[str, str]]:
    parity_rows: dict[str, dict[str, Any]] = {}
    known_codes: set[str] = set()
    code_status: dict[str, str] = {}
    alias_to_canonical: dict[str, str] = {}

    for code, entry in sorted(registry_catalog.items()):
        aliases = sorted(
            [item for item in entry.get("aliases", []) if isinstance(item, str)]
        )
        parity_rows[code] = {
            "category": entry.get("category"),
            "status": entry.get("status"),
            "severity": entry.get("severity"),
            "evidence_required": entry.get("evidence_required"),
            "fail_closed_required": entry.get("fail_closed_required"),
            "replaced_by": entry.get("replaced_by"),
            "aliases": aliases,
        }
        known_codes.add(code)
        code_status[code] = str(entry.get("status") or "active")
        for alias in aliases:
            if alias in alias_to_canonical and alias_to_canonical[alias] != code:
                result.fail(
                    "reason-code alias collision: "
                    f"{alias} -> {alias_to_canonical[alias]} and {code}"
                )
            alias_to_canonical[alias] = code
            known_codes.add(alias)

    try:
        validate_registry_runtime_parity(parity_rows)
    except PolicyDenyError as exc:
        result.fail(f"{rel(catalog_path)}: {exc}")

    return known_codes, alias_to_canonical, code_status


def validate_code_usage(
    code: LocatedCode,
    *,
    source_path: Path,
    contract_family: str | None,
    known_codes: set[str],
    alias_to_canonical: dict[str, str],
    code_status: dict[str, str],
    deprecated_coverage: set[str],
    result: CheckResult,
) -> str | None:
    if is_placeholder_code(code.code):
        if code.code in PLACEHOLDER_ALLOWLIST:
            return code.code
        result.fail(f"{rel(source_path)}: {code.path}: unsupported placeholder reason code: {code.code}")
        return None

    canonical = alias_to_canonical.get(code.code, code.code)
    if canonical not in known_codes:
        result.fail(f"{rel(source_path)}: {code.path}: unknown reason code: {code.code}")
        return None

    status = code_status.get(canonical, "active")
    if status == "deprecated" and canonical not in deprecated_coverage:
        result.fail(
            f"{rel(source_path)}: {code.path}: deprecated reason code missing compatibility record: {canonical}"
        )
    if contract_family is not None:
        try:
            metadata = validate_reason_code_for_family(canonical, contract_family, allow_alias=False)
        except PolicyDenyError as exc:
            result.fail(f"{rel(source_path)}: {code.path}: {exc}")
            return None

        field_allowed = FIELD_CATEGORY_CONSTRAINTS.get(code.field)
        if field_allowed is not None and metadata["category"] not in field_allowed:
            result.fail(
                f"{rel(source_path)}: {code.path}: wrong-field reason category "
                f"{metadata['category']} for {code.field}"
            )
            return None
    return canonical


def run_check(root: Path = ROOT) -> int:
    result = CheckResult(failures=[], warnings=[])
    schema_dir = root / "contracts" / "v1"
    example_dir = root / "contracts" / "examples"
    registry_catalog_path = root / "contracts" / "taxonomy" / "reason-code-registry.catalog.json"
    if not schema_dir.is_dir():
        result.fail(f"{schema_dir}: missing contracts/v1 directory")
    if not example_dir.is_dir():
        result.fail(f"{example_dir}: missing contracts/examples directory")
    if not registry_catalog_path.is_file():
        result.fail(f"{rel(registry_catalog_path)}: missing registry catalog file")
    if result.failures:
        for failure in result.failures:
            print(f"FAIL: {failure}")
        print("Result: FAIL")
        return 1

    registry_examples = load_registry_examples(result, example_dir)
    deprecated_coverage, compatibility_examples = load_compatibility_examples(result, example_dir)
    _, registry_catalog = load_registry_catalog(result, registry_catalog_path)
    known_codes, alias_to_canonical, code_status = build_known_reason_catalog(
        registry_catalog, registry_catalog_path, result
    )

    schemas: list[LoadedJson] = []
    for path in sorted(schema_dir.rglob("*.schema.json")):
        loaded = load_json(path, result)
        if loaded is not None:
            schemas.append(loaded)
    examples: list[LoadedJson] = []
    for path in sorted(example_dir.rglob("*.json")):
        loaded = load_json(path, result)
        if loaded is not None:
            examples.append(loaded)

    schema_by_key: dict[str, LoadedJson] = {}
    schema_requires_taxonomy: dict[str, bool] = {}
    schema_uses_reason: dict[str, bool] = {}
    schema_family: dict[str, str | None] = {}
    schema_expected_taxonomy_family: dict[str, str | None] = {}
    schema_code_count = 0
    for schema in schemas:
        key = schema_key_from_path(schema.path)
        schema_by_key[key] = schema
        schema_uses_reason[key] = schema_uses_reason_model(schema.data)
        schema_family[key] = (
            None if key in FAMILY_VALIDATION_EXEMPT_SCHEMA_KEYS else infer_contract_family(key, schema.data)
        )
        schema_expected_taxonomy_family[key] = expected_taxonomy_family(key)
        schema_requires_taxonomy[key] = schema_requires_taxonomy_version(schema.data)
        if schema_uses_reason[key] and not schema_has_taxonomy_version_property(schema.data):
            result.fail(f"{rel(schema.path)}: reason-bearing schema is missing taxonomy_version property")
        if schema_uses_reason[key] and not schema_requires_taxonomy[key]:
            if key in SCHEMA_TAXONOMY_ALLOWLIST:
                result.warn(
                    f"{rel(schema.path)}: reason-bearing schema is allowlisted from "
                    "taxonomy_version required enforcement"
                )
            else:
                result.fail(f"{rel(schema.path)}: reason-bearing schema must require taxonomy_version")
        if schema_uses_reason[key]:
            expected_family = schema_expected_taxonomy_family.get(key)
            taxonomy_property = schema.data.get("properties", {}).get("taxonomy_version") if isinstance(schema.data, dict) else None
            if expected_family is not None and isinstance(taxonomy_property, dict):
                enum_values = taxonomy_property.get("enum")
                if isinstance(enum_values, list) and enum_values:
                    for value in enum_values:
                        if isinstance(value, str):
                            try:
                                validate_taxonomy_version(value, expected_family=expected_family)
                            except PolicyDenyError as exc:
                                result.fail(f"{rel(schema.path)}: taxonomy_version enum mismatch: {exc}")

        for code in gather_reason_codes_from_schema(schema):
            schema_code_count += 1
            validate_code_usage(
                code,
                source_path=schema.path,
                contract_family=schema_family.get(key),
                known_codes=known_codes,
                alias_to_canonical=alias_to_canonical,
                code_status=code_status,
                deprecated_coverage=deprecated_coverage,
                result=result,
            )

    example_code_count = 0
    blocked_in_success_count = 0
    for example in examples:
        key = map_example_to_schema(example, set(schema_by_key))
        if key is None:
            result.fail(f"{rel(example.path)}: cannot map example to schema")
            continue
        if schema_uses_reason.get(key, False):
            validate_supported_taxonomy_version(
                example.path,
                example.data,
                result,
                expected_family=schema_expected_taxonomy_family.get(key),
            )

        canonical_codes_in_example: list[str] = []
        for code in gather_reason_codes_from_example(example):
            example_code_count += 1
            canonical = validate_code_usage(
                code,
                source_path=example.path,
                contract_family=schema_family.get(key),
                known_codes=known_codes,
                alias_to_canonical=alias_to_canonical,
                code_status=code_status,
                deprecated_coverage=deprecated_coverage,
                result=result,
            )
            if canonical is not None:
                canonical_codes_in_example.append(canonical)

        if looks_successful(example.data):
            fail_closed_in_success = sorted(
                {
                    code
                    for code in canonical_codes_in_example
                    if code_status.get(code, "active") == "blocked"
                    or bool(validate_registry_entry_metadata(code).get("fail_closed_required"))
                    or str(validate_registry_entry_metadata(code).get("severity")) in {"blocked", "critical"}
                    or str(validate_registry_entry_metadata(code).get("category")) == "tenant_isolation"
                }
            )
            if fail_closed_in_success:
                blocked_in_success_count += 1
                result.fail(
                    f"{rel(example.path)}: fail-closed reason code(s) in successful/completed context: "
                    f"{', '.join(fail_closed_in_success)}"
                )

    # Compatibility records must reference known catalog/runtime codes.
    for compatibility in compatibility_examples:
        if not isinstance(compatibility.data, dict):
            continue
        for field in ("reason_code", "previous_reason_code"):
            value = compatibility.data.get(field)
            if value is None:
                continue
            if not isinstance(value, str) or not value:
                result.fail(f"{rel(compatibility.path)}: {field} must be a non-empty string or null")
                continue
            canonical = alias_to_canonical.get(value, value)
            if canonical not in known_codes:
                result.fail(f"{rel(compatibility.path)}: {field} is unknown in registry/runtime catalog: {value}")

    # Registry examples must match the canonical catalog.
    for code, entry in registry_examples.items():
        catalog_entry = registry_catalog.get(code)
        if catalog_entry is None:
            result.fail(f"{rel(registry_catalog_path)}: missing catalog row for example code {code}")
            continue
        if entry.get("status") != catalog_entry.get("status"):
            result.fail(
                f"{rel(registry_catalog_path)}: status mismatch for {code} "
                f"(example={entry.get('status')} catalog={catalog_entry.get('status')})"
            )

    print("LIMA Office reason-code conformance")
    print(f"- schemas scanned: {len(schemas)}")
    print(f"- examples scanned: {len(examples)}")
    print(f"- known canonical/alias codes: {len(known_codes)}")
    print(f"- reason-code values scanned in schemas: {schema_code_count}")
    print(f"- reason-code values scanned in examples: {example_code_count}")
    print(f"- blocked-in-success violations: {blocked_in_success_count}")
    print(f"- warnings: {len(result.warnings)}")
    print(f"- failures: {len(result.failures)}")

    for warning in result.warnings:
        print(f"WARNING: {warning}")
    for failure in result.failures:
        print(f"FAIL: {failure}")

    if result.failures:
        print("Result: FAIL")
        return 1
    print("Result: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(run_check())
