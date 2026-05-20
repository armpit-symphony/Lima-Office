"""Load versioned LIMA Office JSON Schemas."""

from __future__ import annotations

import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from lima_office.runtime.errors import ContractLoadError


SCHEMA_SUFFIX = ".schema.json"


def default_schema_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "contracts" / "v1"


class ContractLoader:
    """Fail-closed loader for v1 contract schemas."""

    def __init__(self, schema_dir: Path | str | None = None) -> None:
        self.schema_dir = Path(schema_dir) if schema_dir is not None else default_schema_dir()
        self._schemas_by_key: dict[str, dict[str, Any]] = {}
        self._schema_paths_by_key: dict[str, Path] = {}
        self._contract_to_key: dict[str, str] = {}

    @property
    def schema_keys(self) -> tuple[str, ...]:
        return tuple(sorted(self._schemas_by_key))

    @property
    def contract_names(self) -> tuple[str, ...]:
        return tuple(sorted(self._contract_to_key))

    def load(self) -> "ContractLoader":
        if not self.schema_dir.is_dir():
            raise ContractLoadError(f"schema directory is missing: {self.schema_dir}")

        schema_paths = sorted(self.schema_dir.glob(f"*{SCHEMA_SUFFIX}"))
        if not schema_paths:
            raise ContractLoadError(f"no schema files found in {self.schema_dir}")

        schemas_by_key: dict[str, dict[str, Any]] = {}
        schema_paths_by_key: dict[str, Path] = {}
        contract_to_key: dict[str, str] = {}

        for path in schema_paths:
            key = self._key_from_path(path)
            if key in schemas_by_key:
                raise ContractLoadError(f"ambiguous schema key {key!r}")
            try:
                schema = json.loads(path.read_text(encoding="utf-8"))
            except JSONDecodeError as exc:
                raise ContractLoadError(
                    f"{path}: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
                ) from exc
            except OSError as exc:
                raise ContractLoadError(f"{path}: cannot read schema: {exc}") from exc

            if not isinstance(schema, dict):
                raise ContractLoadError(f"{path}: schema root must be an object")
            contract_name = self._contract_name_from_schema(path, key, schema)
            if contract_name in contract_to_key:
                raise ContractLoadError(f"{path}: ambiguous contract name {contract_name!r}")

            schemas_by_key[key] = schema
            schema_paths_by_key[key] = path
            contract_to_key[contract_name] = key

        self._schemas_by_key = schemas_by_key
        self._schema_paths_by_key = schema_paths_by_key
        self._contract_to_key = contract_to_key
        return self

    def get_schema(self, identifier: str) -> dict[str, Any]:
        key = self.resolve_key(identifier)
        try:
            return self._schemas_by_key[key]
        except KeyError as exc:
            raise ContractLoadError(f"schema not loaded for {identifier!r}") from exc

    def schema_path(self, identifier: str) -> Path:
        key = self.resolve_key(identifier)
        try:
            return self._schema_paths_by_key[key]
        except KeyError as exc:
            raise ContractLoadError(f"schema path not loaded for {identifier!r}") from exc

    def resolve_key(self, identifier: str) -> str:
        if not identifier:
            raise ContractLoadError("schema identifier is required")
        normalized = identifier.strip().replace("\\", "/").rsplit("/", 1)[-1]
        if normalized.endswith(SCHEMA_SUFFIX):
            normalized = normalized[: -len(SCHEMA_SUFFIX)]
        elif normalized.endswith(".json"):
            normalized = normalized[:-5]

        if normalized in self._schemas_by_key:
            return normalized
        if normalized in self._contract_to_key:
            return self._contract_to_key[normalized]
        raise ContractLoadError(f"unknown contract schema {identifier!r}")

    @staticmethod
    def _key_from_path(path: Path) -> str:
        name = path.name
        if not name.endswith(SCHEMA_SUFFIX):
            raise ContractLoadError(f"{path}: schema filename must end with {SCHEMA_SUFFIX}")
        return name[: -len(SCHEMA_SUFFIX)]

    @staticmethod
    def _contract_name_from_schema(path: Path, key: str, schema: dict[str, Any]) -> str:
        properties = schema.get("properties")
        if not isinstance(properties, dict):
            raise ContractLoadError(f"{path}: schema properties object is required")
        contract_name = properties.get("contract_name")
        if not isinstance(contract_name, dict) or contract_name.get("const") != key:
            raise ContractLoadError(f"{path}: contract_name const must match {key!r}")
        return key
