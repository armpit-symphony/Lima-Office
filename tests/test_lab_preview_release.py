"""Release artifact invariants for the attended Arc + LIMA Office preview."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build-lab-preview.py"
SPEC = importlib.util.spec_from_file_location("build_lab_preview", BUILDER)
assert SPEC is not None and SPEC.loader is not None
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


class LabPreviewReleaseTests(unittest.TestCase):
    def test_manifest_selects_the_exact_locked_stack(self):
        office_commit = "1" * 40
        manifest = builder.build_manifest("test-preview", office_commit)
        lock = json.loads((ROOT / "stack.lock.json").read_text(encoding="utf-8"))
        dependencies = lock["dependencies"]

        self.assertEqual(office_commit, manifest["components"]["lima_office"]["commit"])
        self.assertEqual(
            dependencies["arc-bot-shell"]["commit"],
            manifest["components"]["arc_worker"]["commit"],
        )
        self.assertEqual(
            dependencies["lima-runtime"]["commit"],
            manifest["components"]["lima_runtime"]["commit"],
        )
        self.assertEqual(
            dependencies["guardian-suite"]["commit"],
            manifest["components"]["guardian"]["commit"],
        )

    def test_manifest_keeps_the_lab_boundary_fail_closed(self):
        manifest = builder.build_manifest("test-preview", "1" * 40)
        self.assertFalse(manifest["production_ready"])
        self.assertFalse(manifest["customer_pilot_allowed"])
        self.assertFalse(manifest["operator_authentication"])
        self.assertEqual(
            [
                "document_list",
                "document_read",
                "local_model_preview",
                "registration_practice",
                "registration_mock_review",
            ],
            manifest["allowed_capabilities"],
        )
        self.assertTrue(manifest["local_model"]["separate_opt_ins_required"])
        self.assertEqual(25, manifest["registration_practice"]["scenario_count"])
        self.assertEqual(3, manifest["registration_practice"]["template_count"])
        self.assertTrue(
            manifest["registration_practice"]["human_review_required"]
        )
        self.assertFalse(manifest["registration_practice"]["submission_allowed"])
        self.assertFalse(
            manifest["registration_practice"]["external_submission_allowed"]
        )
        self.assertEqual("localhost_only", manifest["topology"]["network_scope"])
        self.assertEqual(8, manifest["topology"]["arc_worker_max"])
        self.assertIn("hidden_background_actions", manifest["blocked_capabilities"])

    def test_builder_emits_a_deterministic_payload_and_checksum(self):
        with tempfile.TemporaryDirectory(prefix="preview-artifact-test-") as raw:
            output = Path(raw)
            artifact, checksum, manifest = builder.build_artifact(
                "test-preview",
                output,
                office_commit="1" * 40,
                require_clean=False,
            )
            self.assertTrue(artifact.is_file())
            self.assertTrue(checksum.is_file())
            expected = hashlib.sha256(artifact.read_bytes()).hexdigest()
            self.assertTrue(checksum.read_text(encoding="ascii").startswith(expected))
            with zipfile.ZipFile(artifact) as archive:
                self.assertEqual(
                    {
                        "README.md",
                        "install-lab-preview.ps1",
                        "manifest.json",
                        "smoke-lab-preview.ps1",
                        "setup-local-model.ps1",
                        "start-lab-preview.ps1",
                    },
                    set(archive.namelist()),
                )
                archived = json.loads(archive.read("manifest.json"))
            self.assertEqual(manifest, archived)

    def test_installer_does_not_create_hidden_or_model_runtime(self):
        source = (ROOT / "release" / "lab-preview" / "install-lab-preview.ps1").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("RegisterStartup", source)
        self.assertNotIn("schtasks", source.lower())
        self.assertNotIn("ollama pull", source.lower())
        self.assertIn("startup_registered = $false", source)
        self.assertIn("model_installed = $false", source)

    def test_harness_main_owns_the_server_lifecycle(self):
        source = (ROOT / "scripts" / "arc-runtime-harness.py").read_text(encoding="utf-8")
        module = ast.parse(source)
        top_level_functions = {
            node.name: node for node in module.body if isinstance(node, ast.FunctionDef)
        }
        self.assertIn("_training_assistant", top_level_functions)
        main = top_level_functions["main"]
        calls = [node for node in ast.walk(main) if isinstance(node, ast.Call)]
        self.assertTrue(
            any(
                isinstance(call.func, ast.Attribute)
                and call.func.attr == "serve_forever"
                for call in calls
            )
        )

    def test_start_script_keeps_document_and_model_guards_separate(self):
        source = (ROOT / "release" / "lab-preview" / "start-lab-preview.ps1").read_text(
            encoding="utf-8"
        )
        document_denial = 'throw "Working mode requires an explicit safe document root."\n}'
        model_guard = 'if (($LocalModelSupervisorOptIn -or $LocalModelArcOptIn)'
        self.assertIn(document_denial, source)
        self.assertLess(source.index(document_denial), source.index(model_guard))

    def test_harness_exposes_bounded_registration_practice_routes(self):
        source = (ROOT / "scripts" / "arc-runtime-harness.py").read_text(
            encoding="utf-8"
        )
        for route in (
            "/api/training/registration/catalog",
            "/api/training/registration/run",
            "/api/training/registration/run-suite",
            "/api/training/registration/review",
        ):
            self.assertIn(route, source)
        self.assertNotIn("/api/training/registration/submit", source)
        contract = (ROOT / "docs" / "LAB4_LOCAL_FORM_TEST_RANGE.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("There is no registration submit route", contract)
        self.assertIn("Operator PIN/login work is deferred", contract)


if __name__ == "__main__":
    unittest.main()
