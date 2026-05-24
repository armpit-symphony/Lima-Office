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

    def _run_checker(self, repo_root: Path) -> int:
        buffer = io.StringIO()
        with redirect_stdout(buffer), redirect_stderr(buffer):
            return int(self.checker.run_check(repo_root))

    def test_checker_passes_current_contracts_examples(self):
        repo_root = _repo_fixture_copy()
        try:
            rc = self._run_checker(repo_root)
        finally:
            shutil.rmtree(repo_root)
        self.assertEqual(0, rc)

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
