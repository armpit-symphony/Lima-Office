"""Strict runtime contract validation."""

from __future__ import annotations

import importlib
from typing import Any

from .loader import ContractLoader
from lima_office.runtime.errors import ContractValidationError


def _load_jsonschema() -> Any:
    try:
        return importlib.import_module("jsonschema")
    except ModuleNotFoundError:
        return None


class ContractValidator:
    """Runtime validator that requires real JSON Schema validation."""

    def __init__(self, loader: ContractLoader | None = None) -> None:
        self.loader = loader if loader is not None else ContractLoader().load()
        self._jsonschema = _load_jsonschema()
        if self._jsonschema is None:
            raise ContractValidationError("runtime contract validation requires the jsonschema package")
        if not hasattr(self._jsonschema, "Draft202012Validator") or not hasattr(self._jsonschema, "FormatChecker"):
            raise ContractValidationError("runtime contract validation requires jsonschema with Draft202012Validator")
        self._compiled: dict[str, Any] = {}

    def validate(self, payload: dict[str, Any], schema_ref: str | None = None) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise ContractValidationError("payload must be a JSON object")
        identifier = schema_ref or payload.get("contract_name")
        if not isinstance(identifier, str) or not identifier:
            raise ContractValidationError("payload contract_name or schema_ref is required")

        key = self.loader.resolve_key(identifier)
        validator = self._validator_for(key)
        errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.absolute_path))
        if errors:
            details = []
            for error in errors:
                path = "$"
                if error.absolute_path:
                    path = "$." + ".".join(str(part) for part in error.absolute_path)
                details.append(f"{path}: {error.message}")
            raise ContractValidationError("; ".join(details))
        return payload

    def _validator_for(self, key: str) -> Any:
        if key in self._compiled:
            return self._compiled[key]

        schema = self.loader.get_schema(key)
        draft_validator = self._jsonschema.Draft202012Validator
        try:
            draft_validator.check_schema(schema)
        except self._jsonschema.exceptions.SchemaError as exc:
            raise ContractValidationError(f"invalid schema {key!r}: {exc.message}") from exc

        validator = draft_validator(schema, format_checker=self._jsonschema.FormatChecker())
        self._compiled[key] = validator
        return validator
