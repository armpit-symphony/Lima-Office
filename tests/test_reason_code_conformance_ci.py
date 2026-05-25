import importlib.util
import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_checker_module():
    script_path = ROOT / "scripts" / "check-reason-codes.py"
    spec = importlib.util.spec_from_file_location("check_reason_codes_ci", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load checker module from {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _repo_fixture_copy() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="reason-code-ci-"))
    shutil.copytree(ROOT / "contracts", tmp / "contracts")
    return tmp


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


class ReasonCodeConformanceCITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.checker = _load_checker_module()

    def _run_checker_with_output(self, repo_root: Path) -> tuple[int, str]:
        buffer = io.StringIO()
        with redirect_stdout(buffer), redirect_stderr(buffer):
            rc = int(self.checker.run_check(repo_root))
        return rc, buffer.getvalue()

    def _run_checker(self, repo_root: Path) -> int:
        rc, _ = self._run_checker_with_output(repo_root)
        return rc

    def test_checker_passes_current_contracts_examples(self):
        repo_root = _repo_fixture_copy()
        try:
            rc, output = self._run_checker_with_output(repo_root)
        finally:
            shutil.rmtree(repo_root)
        self.assertEqual(0, rc)
        self.assertIn("warnings: 0", output)

    def test_unknown_reason_code_fails(self):
        repo_root = _repo_fixture_copy()
        try:
            path = repo_root / "contracts" / "examples" / "governance.audit_export.requested-placeholder.example.json"
            payload = _read_json(path)
            payload["reason_codes"] = ["unknown_reason_code_ci_test"]
            _write_json(path, payload)
            rc = self._run_checker(repo_root)
        finally:
            shutil.rmtree(repo_root)
        self.assertNotEqual(0, rc)

    def test_deprecated_without_compatibility_record_fails(self):
        repo_root = _repo_fixture_copy()
        try:
            path = repo_root / "contracts" / "examples" / "reason.code.compatibility.deprecate-alias.example.json"
            payload = _read_json(path)
            payload["previous_reason_code"] = "different_previous_code"
            _write_json(path, payload)
            rc = self._run_checker(repo_root)
        finally:
            shutil.rmtree(repo_root)
        self.assertNotEqual(0, rc)

    def test_deprecated_alias_in_metadata_only_context_passes(self):
        repo_root = _repo_fixture_copy()
        try:
            path = repo_root / "contracts" / "examples" / "governance.audit_export.export-denied.example.json"
            payload = _read_json(path)
            payload["reason_codes"] = ["export_delete_review_required_legacy"]
            _write_json(path, payload)
            rc = self._run_checker(repo_root)
        finally:
            shutil.rmtree(repo_root)
        self.assertEqual(0, rc)

    def test_blocked_code_in_success_context_fails(self):
        repo_root = _repo_fixture_copy()
        try:
            path = repo_root / "contracts" / "examples" / "evidence.export_manifest.exported-redacted-metadata-only.example.json"
            payload = _read_json(path)
            payload["reason_codes"] = ["blocked_mvp_export_delete_execution"]
            _write_json(path, payload)
            rc = self._run_checker(repo_root)
        finally:
            shutil.rmtree(repo_root)
        self.assertNotEqual(0, rc)

    def test_blocked_code_in_denied_context_passes(self):
        repo_root = _repo_fixture_copy()
        try:
            path = repo_root / "contracts" / "examples" / "governance.audit_export.export-denied.example.json"
            payload = _read_json(path)
            payload["reason_codes"] = ["blocked_mvp_export_delete_execution"]
            _write_json(path, payload)
            rc = self._run_checker(repo_root)
        finally:
            shutil.rmtree(repo_root)
        self.assertEqual(0, rc)

    def test_breaking_change_without_affected_contracts_fails(self):
        repo_root = _repo_fixture_copy()
        try:
            path = repo_root / "contracts" / "examples" / "reason.code.compatibility.breaking-change-blocked.example.json"
            payload = _read_json(path)
            payload["affected_contracts"] = []
            _write_json(path, payload)
            rc = self._run_checker(repo_root)
        finally:
            shutil.rmtree(repo_root)
        self.assertNotEqual(0, rc)

    def test_taxonomy_version_missing_where_required_fails(self):
        repo_root = _repo_fixture_copy()
        try:
            path = repo_root / "contracts" / "examples" / "reason.code.registry.reconciliation-active.example.json"
            payload = _read_json(path)
            payload.pop("taxonomy_version", None)
            _write_json(path, payload)
            rc = self._run_checker(repo_root)
        finally:
            shutil.rmtree(repo_root)
        self.assertNotEqual(0, rc)

    def test_reason_bearing_schema_missing_taxonomy_requirement_fails(self):
        repo_root = _repo_fixture_copy()
        try:
            path = repo_root / "contracts" / "v1" / "approval.binding.schema.json"
            payload = _read_json(path)
            payload["required"] = [field for field in payload.get("required", []) if field != "taxonomy_version"]
            _write_json(path, payload)
            rc = self._run_checker(repo_root)
        finally:
            shutil.rmtree(repo_root)
        self.assertNotEqual(0, rc)

    def test_unsupported_taxonomy_version_fails(self):
        repo_root = _repo_fixture_copy()
        try:
            path = repo_root / "contracts" / "examples" / "governance.audit_export.requested-placeholder.example.json"
            payload = _read_json(path)
            payload["taxonomy_version"] = "taxonomy-recon-v999"
            _write_json(path, payload)
            rc = self._run_checker(repo_root)
        finally:
            shutil.rmtree(repo_root)
        self.assertNotEqual(0, rc)

    def test_supported_taxonomy_version_passes(self):
        repo_root = _repo_fixture_copy()
        try:
            path = repo_root / "contracts" / "examples" / "governance.audit_export.requested-placeholder.example.json"
            payload = _read_json(path)
            payload["taxonomy_version"] = "taxonomy-recon-v1"
            _write_json(path, payload)
            rc = self._run_checker(repo_root)
        finally:
            shutil.rmtree(repo_root)
        self.assertEqual(0, rc)

    def test_non_reason_bearing_example_does_not_require_taxonomy_version(self):
        repo_root = _repo_fixture_copy()
        try:
            path = repo_root / "contracts" / "examples" / "connector.trust.example.json"
            payload = _read_json(path)
            payload.pop("taxonomy_version", None)
            _write_json(path, payload)
            rc = self._run_checker(repo_root)
        finally:
            shutil.rmtree(repo_root)
        self.assertEqual(0, rc)

    def test_unknown_result_reason_code_fails(self):
        repo_root = _repo_fixture_copy()
        try:
            path = repo_root / "contracts" / "examples" / "approval.result.approved.example.json"
            payload = _read_json(path)
            payload["result_reason_code"] = "unknown_result_reason_code_ci_test"
            _write_json(path, payload)
            rc = self._run_checker(repo_root)
        finally:
            shutil.rmtree(repo_root)
        self.assertNotEqual(0, rc)

    def test_denial_code_context_still_requires_taxonomy_version(self):
        repo_root = _repo_fixture_copy()
        try:
            path = repo_root / "contracts" / "examples" / "tool.invocation.example.json"
            payload = _read_json(path)
            payload.pop("taxonomy_version", None)
            _write_json(path, payload)
            rc = self._run_checker(repo_root)
        finally:
            shutil.rmtree(repo_root)
        self.assertNotEqual(0, rc)

    def test_wrong_family_reason_code_fails(self):
        repo_root = _repo_fixture_copy()
        try:
            path = repo_root / "contracts" / "examples" / "governance.audit_export.export-denied.example.json"
            payload = _read_json(path)
            payload["reason_codes"] = ["recon_mismatched_approval_binding"]
            _write_json(path, payload)
            rc = self._run_checker(repo_root)
        finally:
            shutil.rmtree(repo_root)
        self.assertNotEqual(0, rc)

    def test_tenant_isolation_code_passes_in_blocked_context(self):
        repo_root = _repo_fixture_copy()
        try:
            path = repo_root / "contracts" / "examples" / "guardian.replay.scope-mismatch.example.json"
            payload = _read_json(path)
            payload["mismatch_reasons"] = ["tenant_mismatch"]
            _write_json(path, payload)
            rc = self._run_checker(repo_root)
        finally:
            shutil.rmtree(repo_root)
        self.assertEqual(0, rc)

    def test_tenant_isolation_code_fails_in_success_context(self):
        repo_root = _repo_fixture_copy()
        try:
            path = repo_root / "contracts" / "examples" / "approval.result.approved.example.json"
            payload = _read_json(path)
            payload["result_reason_code"] = "tenant_mismatch"
            _write_json(path, payload)
            rc = self._run_checker(repo_root)
        finally:
            shutil.rmtree(repo_root)
        self.assertNotEqual(0, rc)

    def test_evidence_code_in_guardian_family_fails(self):
        repo_root = _repo_fixture_copy()
        try:
            path = repo_root / "contracts" / "examples" / "guardian.decision.allowed-one-time.example.json"
            payload = _read_json(path)
            payload["linkage_failure_reasons"] = ["evidence_ref_missing"]
            _write_json(path, payload)
            rc = self._run_checker(repo_root)
        finally:
            shutil.rmtree(repo_root)
        self.assertNotEqual(0, rc)

    def test_deprecated_alias_still_respects_family_rules(self):
        repo_root = _repo_fixture_copy()
        denied_rc = 0
        try:
            allowed_path = repo_root / "contracts" / "examples" / "governance.audit_export.export-denied.example.json"
            allowed_payload = _read_json(allowed_path)
            allowed_payload["reason_codes"] = ["export_delete_review_required_legacy"]
            _write_json(allowed_path, allowed_payload)
            allowed_rc = self._run_checker(repo_root)
            self.assertEqual(0, allowed_rc)

            denied_path = repo_root / "contracts" / "examples" / "approval.result.approved.example.json"
            denied_payload = _read_json(denied_path)
            denied_payload["result_reason_code"] = "export_delete_review_required_legacy"
            _write_json(denied_path, denied_payload)
            denied_rc = self._run_checker(repo_root)
        finally:
            shutil.rmtree(repo_root)
        self.assertNotEqual(0, denied_rc)

    def test_runtime_only_code_missing_in_registry_fails(self):
        repo_root = _repo_fixture_copy()
        try:
            catalog_path = repo_root / "contracts" / "taxonomy" / "reason-code-registry.catalog.json"
            payload = _read_json(catalog_path)
            payload["reason_codes"] = [row for row in payload.get("reason_codes", []) if row.get("reason_code") != "approval_missing"]
            _write_json(catalog_path, payload)
            rc = self._run_checker(repo_root)
        finally:
            shutil.rmtree(repo_root)
        self.assertNotEqual(0, rc)

    def test_registry_only_code_missing_in_runtime_fails(self):
        repo_root = _repo_fixture_copy()
        try:
            catalog_path = repo_root / "contracts" / "taxonomy" / "reason-code-registry.catalog.json"
            payload = _read_json(catalog_path)
            payload.setdefault("reason_codes", []).append(
                {
                    "reason_code": "registry_only_code_ci_test",
                    "category": "governance",
                    "status": "active",
                    "severity": "warning",
                    "evidence_required": False,
                    "fail_closed_required": False,
                    "replaced_by": None,
                    "aliases": [],
                }
            )
            _write_json(catalog_path, payload)
            rc = self._run_checker(repo_root)
        finally:
            shutil.rmtree(repo_root)
        self.assertNotEqual(0, rc)

    def test_compatibility_record_for_unknown_reason_code_fails(self):
        repo_root = _repo_fixture_copy()
        try:
            path = repo_root / "contracts" / "examples" / "reason.code.compatibility.add-compatible.example.json"
            payload = _read_json(path)
            payload["reason_code"] = "unknown_reason_code_ci_test"
            _write_json(path, payload)
            rc = self._run_checker(repo_root)
        finally:
            shutil.rmtree(repo_root)
        self.assertNotEqual(0, rc)

    def test_wrong_taxonomy_family_fails(self):
        repo_root = _repo_fixture_copy()
        try:
            path = repo_root / "contracts" / "examples" / "approval.binding.bound-valid.example.json"
            payload = _read_json(path)
            payload["taxonomy_version"] = "taxonomy-reason-v1"
            _write_json(path, payload)
            rc = self._run_checker(repo_root)
        finally:
            shutil.rmtree(repo_root)
        self.assertNotEqual(0, rc)

    def test_deprecated_code_with_compatibility_still_requires_taxonomy_version(self):
        repo_root = _repo_fixture_copy()
        try:
            path = repo_root / "contracts" / "examples" / "governance.audit_export.export-denied.example.json"
            payload = _read_json(path)
            payload["reason_codes"] = ["export_delete_review_required_legacy"]
            payload.pop("taxonomy_version", None)
            _write_json(path, payload)
            rc = self._run_checker(repo_root)
        finally:
            shutil.rmtree(repo_root)
        self.assertNotEqual(0, rc)

    def test_blocked_code_in_denied_context_still_requires_taxonomy_version(self):
        repo_root = _repo_fixture_copy()
        try:
            path = repo_root / "contracts" / "examples" / "governance.audit_export.export-denied.example.json"
            payload = _read_json(path)
            payload["reason_codes"] = ["blocked_mvp_export_delete_execution"]
            payload.pop("taxonomy_version", None)
            _write_json(path, payload)
            rc = self._run_checker(repo_root)
        finally:
            shutil.rmtree(repo_root)
        self.assertNotEqual(0, rc)

    def test_script_returns_non_zero_on_failure(self):
        repo_root = _repo_fixture_copy()
        try:
            path = repo_root / "contracts" / "examples" / "governance.audit_export.requested-placeholder.example.json"
            payload = _read_json(path)
            payload["reason_codes"] = ["unknown_reason_code_ci_test"]
            _write_json(path, payload)
            rc = self._run_checker(repo_root)
        finally:
            shutil.rmtree(repo_root)
        self.assertGreater(rc, 0)

    def test_checker_is_read_only_and_non_authorizing(self):
        repo_root = _repo_fixture_copy()
        try:
            before = sorted(str(path.relative_to(repo_root)) for path in repo_root.rglob("*"))
            rc = self._run_checker(repo_root)
            after = sorted(str(path.relative_to(repo_root)) for path in repo_root.rglob("*"))
        finally:
            shutil.rmtree(repo_root)
        self.assertEqual(0, rc)
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
