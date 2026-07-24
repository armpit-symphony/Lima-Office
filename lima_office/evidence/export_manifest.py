"""Mock-only evidence export-manifest helper for Phase 1A tests."""

from __future__ import annotations

import copy
from typing import Any

from lima_office.contracts.validator import ContractValidator
from lima_office.runtime.invariants import assert_evidence_export_manifest_consistent


class EvidenceExportManifestBuilder:
    """Builds metadata-only export manifests from evidence refs only."""

    def __init__(self, validator: ContractValidator) -> None:
        self.validator = validator

    def validate_manifest(
        self,
        manifest: dict[str, Any],
        *,
        evidence_by_id: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        validated = self.validator.validate(copy.deepcopy(manifest), "evidence.export_manifest")
        checked = assert_evidence_export_manifest_consistent(validated, evidence_by_id=evidence_by_id)
        return copy.deepcopy(checked)
