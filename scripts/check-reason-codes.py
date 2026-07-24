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
    ALIAS_TO_CANONICAL,
    REASON_CODE_REGISTRY,
    validate_taxonomy_version,
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
        "health_reason_codes",
        "route_reason_codes",
        "fallback_reason_codes",
        "model_route_reason_codes",
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
    source_path: Path, payload: Any, result: CheckResult
) -> None:
    if not isinstance(payload, dict):
        result.fail(f"{rel(source_path)}: expected object payload for taxonomy_version validation")
        return
    version = payload.get("taxonomy_version")
    if not isinstance(version, str) or not version:
        result.fail(f"{rel(source_path)}: missing taxonomy_version for reason-bearing payload")
        return
    try:
        validate_taxonomy_version(version)
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


def build_known_reason_catalog(
    registry_examples: dict[str, dict[str, Any]],
) -> tuple[set[str], dict[str, str], dict[str, str]]:
    known_codes = set(REASON_CODE_REGISTRY.keys())
    code_status: dict[str, str] = {code: str(meta.get("status") or "active") for code, meta in REASON_CODE_REGISTRY.items()}
    alias_to_canonical = dict(ALIAS_TO_CANONICAL)

    for code, entry in registry_examples.items():
        known_codes.add(code)
        status = str(entry.get("status") or "active")
        code_status[code] = status
        for alias in entry.get("aliases", []):
            if alias in alias_to_canonical and alias_to_canonical[alias] != code:
                # Fail-closed on alias collisions by pointing to a synthetic unknown.
                alias_to_canonical[alias] = "__alias_collision__"
            else:
                alias_to_canonical[alias] = code
            known_codes.add(alias)

    return known_codes, alias_to_canonical, code_status


def validate_code_usage(
    code: LocatedCode,
    *,
    source_path: Path,
    known_codes: set[str],
    alias_to_canonical: dict[str, str],
    code_status: dict[str, str],
    deprecated_coverage: set[str],
    result: CheckResult,
) -> str | None:
    if is_placeholder_code(code.code):
        return code.code

    canonical = alias_to_canonical.get(code.code, code.code)
    if canonical == "__alias_collision__":
        result.fail(f"{rel(source_path)}: {code.path}: alias maps to multiple canonical codes: {code.code}")
        return None
    if canonical not in known_codes:
        result.fail(f"{rel(source_path)}: {code.path}: unknown reason code: {code.code}")
        return None

    status = code_status.get(canonical, "active")
    if status == "deprecated" and canonical not in deprecated_coverage:
        result.fail(
            f"{rel(source_path)}: {code.path}: deprecated reason code missing compatibility record: {canonical}"
        )
    return canonical


def run_check(root: Path = ROOT) -> int:
    result = CheckResult(failures=[], warnings=[])
    schema_dir = root / "contracts" / "v1"
    example_dir = root / "contracts" / "examples"
    if not schema_dir.is_dir():
        result.fail(f"{schema_dir}: missing contracts/v1 directory")
    if not example_dir.is_dir():
        result.fail(f"{example_dir}: missing contracts/examples directory")
    if result.failures:
        for failure in result.failures:
            print(f"FAIL: {failure}")
        print("Result: FAIL")
        return 1

    registry_examples = load_registry_examples(result, example_dir)
    deprecated_coverage, _ = load_compatibility_examples(result, example_dir)
    known_codes, alias_to_canonical, code_status = build_known_reason_catalog(registry_examples)

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
    schema_code_count = 0
    for schema in schemas:
        key = schema_key_from_path(schema.path)
        schema_by_key[key] = schema
        schema_uses_reason[key] = schema_uses_reason_model(schema.data)
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

        for code in gather_reason_codes_from_schema(schema):
            schema_code_count += 1
            validate_code_usage(
                code,
                source_path=schema.path,
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
            validate_supported_taxonomy_version(example.path, example.data, result)

        canonical_codes_in_example: list[str] = []
        for code in gather_reason_codes_from_example(example):
            example_code_count += 1
            canonical = validate_code_usage(
                code,
                source_path=example.path,
                known_codes=known_codes,
                alias_to_canonical=alias_to_canonical,
                code_status=code_status,
                deprecated_coverage=deprecated_coverage,
                result=result,
            )
            if canonical is not None:
                canonical_codes_in_example.append(canonical)

        if looks_successful(example.data):
            blocked = sorted(
                {
                    code
                    for code in canonical_codes_in_example
                    if code_status.get(code, "active") == "blocked"
                }
            )
            if blocked:
                blocked_in_success_count += 1
                result.fail(
                    f"{rel(example.path)}: blocked reason code(s) in successful/completed context: {', '.join(blocked)}"
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
