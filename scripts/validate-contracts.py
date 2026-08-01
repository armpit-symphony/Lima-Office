#!/usr/bin/env python3
"""Validate Phase 0 LIMA Office contract schemas and examples."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import re
import sys
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "contracts" / "v1"
EXAMPLE_DIR = ROOT / "contracts" / "examples"
DOCS_DIR = ROOT / "docs"

SCHEMA_SUFFIX = ".schema.json"

# Use this table only for intentionally exceptional examples whose filename and
# declared contract_name cannot safely identify the schema.
EXAMPLE_SCHEMA_OVERRIDES: dict[str, str] = {}

DECLARED_SCHEMA_FIELDS = ("$schema_ref", "schema_ref", "contract_name", "contract_type", "type")

COMMON_ENVELOPE_FIELDS = (
    "contract_name",
    "contract_version",
    "schema_version",
    "tenant_id",
    "customer_context_id",
    "environment",
    "correlation_id",
    "causation_id",
    "idempotency_key",
    "producer",
    "policy_version",
)


try:
    import jsonschema as jsonschema_pkg
    from jsonschema import Draft202012Validator, FormatChecker
    from jsonschema.exceptions import SchemaError

    JSONSCHEMA_AVAILABLE = True
    JSONSCHEMA_VERSION = importlib.metadata.version("jsonschema")
except ModuleNotFoundError:  # pragma: no cover - exercised where dependency is absent
    Draft202012Validator = None  # type: ignore[assignment]
    FormatChecker = None  # type: ignore[assignment]
    SchemaError = Exception  # type: ignore[assignment]
    JSONSCHEMA_AVAILABLE = False
    JSONSCHEMA_VERSION = "unavailable"


@dataclass(frozen=True)
class LoadedJson:
    path: Path
    data: Any


@dataclass
class ValidationResult:
    failures: list[str]
    warnings: list[str]

    def fail(self, message: str) -> None:
        self.failures.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def load_json(path: Path, result: ValidationResult) -> LoadedJson | None:
    try:
        return LoadedJson(path=path, data=json.loads(path.read_text(encoding="utf-8")))
    except JSONDecodeError as exc:
        result.fail(f"{rel(path)}: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}")
    except OSError as exc:
        result.fail(f"{rel(path)}: cannot read file: {exc}")
    return None


def schema_key_from_path(path: Path) -> str:
    name = path.name
    if not name.endswith(SCHEMA_SUFFIX):
        raise ValueError(f"schema path does not end with {SCHEMA_SUFFIX}: {path}")
    return name[: -len(SCHEMA_SUFFIX)]


def schema_key_from_ref(value: Any, schema_keys: set[str], schema_ids: dict[str, str]) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None

    ref = value.strip()
    if ref in schema_keys:
        return ref
    if ref in schema_ids:
        return schema_ids[ref]

    basename = ref.rsplit("/", 1)[-1]
    if basename in schema_ids:
        return schema_ids[basename]
    if basename.endswith(SCHEMA_SUFFIX):
        candidate = basename[: -len(SCHEMA_SUFFIX)]
        if candidate in schema_keys:
            return candidate

    return None


def schema_key_from_filename(path: Path, schema_keys: set[str]) -> str | None:
    base = path.name
    if base.endswith(".json"):
        base = base[:-5]
    if base.endswith(".example"):
        base = base[:-8]

    for key in sorted(schema_keys, key=len, reverse=True):
        if base == key or base.startswith(f"{key}."):
            return key
    return None


def declared_schema_key(example: LoadedJson, schema_keys: set[str], schema_ids: dict[str, str]) -> str | None:
    if not isinstance(example.data, dict):
        return None
    for field in DECLARED_SCHEMA_FIELDS:
        key = schema_key_from_ref(example.data.get(field), schema_keys, schema_ids)
        if key:
            return key
    return None


def map_example_to_schema(
    example: LoadedJson,
    schema_keys: set[str],
    schema_ids: dict[str, str],
    result: ValidationResult,
) -> str | None:
    override = EXAMPLE_SCHEMA_OVERRIDES.get(example.path.name)
    declared = declared_schema_key(example, schema_keys, schema_ids)
    filename = schema_key_from_filename(example.path, schema_keys)

    if override:
        if override not in schema_keys:
            result.fail(f"{rel(example.path)}: explicit mapping points to missing schema '{override}'")
            return None
        if declared and declared != override:
            result.fail(
                f"{rel(example.path)}: declared schema '{declared}' conflicts with explicit mapping '{override}'"
            )
            return None
        return override

    if declared:
        if filename and declared != filename:
            result.fail(f"{rel(example.path)}: declared schema '{declared}' conflicts with filename mapping '{filename}'")
            return None
        return declared

    if filename:
        return filename

    result.fail(
        f"{rel(example.path)}: cannot map example to a schema by declared schema_ref/contract_name/type or filename"
    )
    return None


def walk_json(value: Any) -> Iterable[Any]:
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_json(child)


def validate_schema_structure(schema: LoadedJson, key: str, result: ValidationResult) -> None:
    if not isinstance(schema.data, dict):
        result.fail(f"{rel(schema.path)}: schema root must be a JSON object")
        return
    if schema.data.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        result.fail(f"{rel(schema.path)}: schema must declare JSON Schema draft 2020-12")
    if not isinstance(schema.data.get("$id"), str) or not schema.data["$id"].endswith(f"/{key}{SCHEMA_SUFFIX}"):
        result.fail(f"{rel(schema.path)}: $id must end with /{key}{SCHEMA_SUFFIX}")
    if schema.data.get("type") != "object":
        result.fail(f"{rel(schema.path)}: top-level type must be object")
    if schema.data.get("additionalProperties") is not False:
        result.fail(f"{rel(schema.path)}: top-level additionalProperties must be false")

    required = schema.data.get("required")
    if not isinstance(required, list) or not required:
        result.fail(f"{rel(schema.path)}: schema must define non-empty required fields")
        required = []

    missing_envelope = [field for field in COMMON_ENVELOPE_FIELDS if field not in required]
    if missing_envelope:
        result.fail(f"{rel(schema.path)}: missing shared envelope required fields: {', '.join(missing_envelope)}")

    properties = schema.data.get("properties")
    if not isinstance(properties, dict):
        result.fail(f"{rel(schema.path)}: schema must define object properties")
        return
    contract_name = properties.get("contract_name")
    if not isinstance(contract_name, dict) or contract_name.get("const") != key:
        result.fail(f"{rel(schema.path)}: properties.contract_name.const must be '{key}'")

    for node in walk_json(schema.data):
        if isinstance(node, dict) and "$ref" in node:
            ref_value = node["$ref"]
            if isinstance(ref_value, str) and re.match(r"(?i)^https?://", ref_value):
                result.fail(f"{rel(schema.path)}: remote $ref is not allowed: {ref_value}")


def fallback_validate_example(example: LoadedJson, schema: LoadedJson, schema_key: str, result: ValidationResult) -> None:
    if not isinstance(example.data, dict):
        result.fail(f"{rel(example.path)}: example root must be a JSON object")
        return
    if not isinstance(schema.data, dict):
        return

    if example.data.get("contract_name") != schema_key:
        result.fail(f"{rel(example.path)}: contract_name must be '{schema_key}'")

    required = schema.data.get("required")
    properties = schema.data.get("properties")
    if isinstance(required, list):
        missing = [field for field in required if field not in example.data]
        if missing:
            result.fail(f"{rel(example.path)}: missing required top-level fields: {', '.join(missing)}")

    if isinstance(properties, dict) and schema.data.get("additionalProperties") is False:
        unknown = sorted(set(example.data) - set(properties))
        if unknown:
            result.fail(f"{rel(example.path)}: unknown top-level fields: {', '.join(unknown)}")


def validate_with_jsonschema(
    example: LoadedJson,
    schema: LoadedJson,
    result: ValidationResult,
    check_formats: bool,
) -> None:
    assert Draft202012Validator is not None
    format_checker = FormatChecker() if check_formats and FormatChecker is not None else None
    validator = Draft202012Validator(schema.data, format_checker=format_checker)
    errors = sorted(validator.iter_errors(example.data), key=lambda err: list(err.absolute_path))
    for error in errors:
        path = "$"
        if error.absolute_path:
            path = "$." + ".".join(str(part) for part in error.absolute_path)
        result.fail(f"{rel(example.path)}: {path}: {error.message}")


SAFE_CONTEXT_MARKERS = (
    "approval required",
    "blocked",
    "cannot",
    "deny",
    "denied",
    "denies",
    "does not",
    "do not",
    "fail closed",
    "forbid",
    "forbidden",
    "must never",
    "must not",
    "never",
    "no ",
    "not ",
    "not allowed",
    "not authorize",
    "not permission",
    "out of scope",
    "planning artifact",
    "planning artifacts",
    "prohibit",
    "prohibited",
    "requires approval",
    "risk",
    "risks",
    "scanner",
    "validation blocks",
)


ALWAYS_SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{36,}\b")),
    ("openai_api_key", re.compile(r"\bsk-[A-Za-z0-9][A-Za-z0-9_-]{20,}\b")),
    ("private_key_block", re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
)


CONTEXTUAL_UNSAFE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("plaintext_api_key_field", re.compile(r"(?i)(['\"`]?api[_ -]?key['\"`]?\s*[:=]|\bplaintext api key fields?\b)")),
    ("secret_value", re.compile(r"(?i)\bsecret_value\b")),
    ("password", re.compile(r"(?i)\bpasswords?\b")),
    ("private_key", re.compile(r"(?i)\bprivate_key\b")),
    (
        "production_claim",
        re.compile(
            r"(?i)\b(production[- ]ready|ready for production|safe for production|approved for production|production deployment enabled)\b"
        ),
    ),
    (
        "live_connector_enabled",
        re.compile(
            r"(?i)\b(live connectors? (enabled|ready|allowed|authorized)|connectors? (enabled|live|production[- ]ready)|oauth/provider wiring enabled)\b"
        ),
    ),
    (
        "remediation_without_approval",
        re.compile(
            r"(?i)\b(remediation (allowed|approved|authorized|may proceed|can run|can execute|execution allowed) without approval|without approval remediation)\b"
        ),
    ),
    (
        "unrestricted_tool_execution",
        re.compile(r"(?i)\b(unrestricted (tool execution|browser access|file access|network access|tool access))\b"),
    ),
    (
        "cross_tenant_access_allowed",
        re.compile(r"(?i)\bcross[- ]tenant (access|memory|evidence|sharing).{0,40}\b(allowed|enabled|authorized|approved)\b"),
    ),
    (
        "external_send_without_approval",
        re.compile(r"(?i)\b(external (send|email|message|chat).{0,40}without approval|without approval.{0,40}external (send|email|message|chat))\b"),
    ),
)


def context_is_safe(lines: list[str], index: int) -> bool:
    start = max(0, index - 2)
    end = min(len(lines), index + 2)
    context = " ".join(lines[start:end]).lower()
    return any(marker in context for marker in SAFE_CONTEXT_MARKERS)


def scan_file_for_unsafe_content(path: Path, result: ValidationResult) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        result.fail(f"{rel(path)}: cannot read for unsafe-content scan: {exc}")
        return

    lines = text.splitlines()
    for line_no, line in enumerate(lines, start=1):
        for name, pattern in ALWAYS_SECRET_PATTERNS:
            if pattern.search(line):
                result.fail(f"{rel(path)}:{line_no}: possible secret material detected by {name}")

        for name, pattern in CONTEXTUAL_UNSAFE_PATTERNS:
            if not pattern.search(line):
                continue
            if context_is_safe(lines, line_no - 1):
                continue
            result.fail(f"{rel(path)}:{line_no}: unsafe positive content matched {name}")


def unsafe_content_scan(result: ValidationResult) -> tuple[int, int]:
    example_files = sorted(EXAMPLE_DIR.rglob("*.json")) if EXAMPLE_DIR.exists() else []
    doc_candidates = []
    if DOCS_DIR.exists():
        doc_candidates.extend(DOCS_DIR.rglob("*.md"))
    doc_candidates.extend([ROOT / "README.md", ROOT / "contracts" / "README.md"])
    doc_files = sorted({path for path in doc_candidates if path.exists()})

    for path in [*example_files, *doc_files]:
        scan_file_for_unsafe_content(path, result)

    return len(example_files), len(doc_files)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate LIMA Office Phase 0 contracts.")
    parser.add_argument(
        "--require-jsonschema",
        action="store_true",
        help="fail if the jsonschema package is unavailable",
    )
    parser.add_argument(
        "--check-formats",
        action="store_true",
        help="enforce JSON Schema format checks such as date-time when jsonschema is available",
    )
    parser.add_argument(
        "--warnings-as-errors",
        action="store_true",
        help="treat warnings as failures",
    )
    return parser.parse_args()


def validate_contracts(args: argparse.Namespace) -> int:
    result = ValidationResult(failures=[], warnings=[])

    if args.require_jsonschema and not JSONSCHEMA_AVAILABLE:
        result.fail("jsonschema is required for this run but is not installed")
    if args.check_formats and not JSONSCHEMA_AVAILABLE:
        result.fail("format checking requires jsonschema")

    if not SCHEMA_DIR.is_dir():
        result.fail(f"{rel(SCHEMA_DIR)}: schema directory is missing")
        schemas: list[LoadedJson] = []
    else:
        schema_paths = sorted(SCHEMA_DIR.rglob(f"*{SCHEMA_SUFFIX}"))
        if not schema_paths:
            result.fail(f"{rel(SCHEMA_DIR)}: no schema files found")
        schemas = [loaded for path in schema_paths if (loaded := load_json(path, result))]

    if not EXAMPLE_DIR.is_dir():
        result.fail(f"{rel(EXAMPLE_DIR)}: example directory is missing")
        examples: list[LoadedJson] = []
    else:
        example_paths = sorted(EXAMPLE_DIR.rglob("*.json"))
        if not example_paths:
            result.fail(f"{rel(EXAMPLE_DIR)}: no example files found")
        examples = [loaded for path in example_paths if (loaded := load_json(path, result))]

    schema_by_key: dict[str, LoadedJson] = {}
    schema_ids: dict[str, str] = {}
    for schema in schemas:
        key = schema_key_from_path(schema.path)
        if key in schema_by_key:
            result.fail(f"{rel(schema.path)}: duplicate schema key '{key}'")
            continue
        schema_by_key[key] = schema
        validate_schema_structure(schema, key, result)
        if isinstance(schema.data, dict):
            schema_id = schema.data.get("$id")
            if isinstance(schema_id, str):
                if schema_id in schema_ids:
                    result.fail(f"{rel(schema.path)}: duplicate $id '{schema_id}'")
                schema_ids[schema_id] = key
                schema_ids[schema.path.name] = key

    if JSONSCHEMA_AVAILABLE:
        assert Draft202012Validator is not None
        for key, schema in schema_by_key.items():
            try:
                Draft202012Validator.check_schema(schema.data)
            except SchemaError as exc:
                result.fail(f"{rel(schema.path)}: invalid JSON Schema for '{key}': {exc.message}")
    else:
        result.warn("jsonschema is not installed; running syntax, mapping, and structural checks only.")

    examples_by_schema: dict[str, list[Path]] = {key: [] for key in schema_by_key}
    for example in examples:
        key = map_example_to_schema(example, set(schema_by_key), schema_ids, result)
        if not key:
            continue
        schema = schema_by_key.get(key)
        if not schema:
            result.fail(f"{rel(example.path)}: mapped schema '{key}' does not exist")
            continue
        examples_by_schema.setdefault(key, []).append(example.path)
        if JSONSCHEMA_AVAILABLE:
            validate_with_jsonschema(example, schema, result, args.check_formats)
        else:
            fallback_validate_example(example, schema, key, result)

    for key, schema in schema_by_key.items():
        if not examples_by_schema.get(key):
            result.fail(f"{rel(schema.path)}: schema has no mapped example")

    scanned_examples, scanned_docs = unsafe_content_scan(result)

    if args.warnings_as_errors and result.warnings:
        for warning in result.warnings:
            result.fail(f"warning treated as error: {warning}")

    mode = "full JSON Schema draft 2020-12" if JSONSCHEMA_AVAILABLE else "fallback structural"
    if JSONSCHEMA_AVAILABLE and args.check_formats:
        mode += " with format checks"

    print("LIMA Office contract validation")
    print(f"- schemas parsed: {len(schemas)}")
    print(f"- examples parsed: {len(examples)}")
    print(f"- mapped examples: {sum(len(paths) for paths in examples_by_schema.values())}")
    print(f"- schemas with examples: {sum(1 for paths in examples_by_schema.values() if paths)}")
    print(f"- validation mode: {mode}")
    print(f"- jsonschema version: {JSONSCHEMA_VERSION}")
    print(f"- unsafe-content scan: {scanned_examples} example files, {scanned_docs} markdown files")
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
    sys.exit(validate_contracts(parse_args()))
