"""Lab packaging claim: authentication path only."""

from __future__ import annotations

import ast
import json
from pathlib import Path
import unittest

from lima_office.runtime.lab_packaging import (
    CUSTOMER_PILOT_ALLOWED,
    OPERATOR_AUTHENTICATION,
    OPERATOR_AUTHENTICATION_MANIFEST,
    PRODUCTION_READY,
    assert_packaging_invariants,
)
from lima_office.runtime.local_loopback_api import LocalLoopbackApi
from lima_office.runtime.profile_b_session import MemoryEvidenceStore, ProfileBSessionService
from lima_office.runtime.supervisor_console import _profile_b_projection


ROOT = Path(__file__).resolve().parents[1]


class LabPackagingClaimTests(unittest.TestCase):
    def test_constants_claim_auth_and_keep_production_and_pilot_false(self):
        assert_packaging_invariants()
        self.assertIs(PRODUCTION_READY, False)
        self.assertIs(CUSTOMER_PILOT_ALLOWED, False)
        self.assertIs(OPERATOR_AUTHENTICATION, True)
        self.assertIs(OPERATOR_AUTHENTICATION_MANIFEST, True)
        self.assertIs(OPERATOR_AUTHENTICATION, OPERATOR_AUTHENTICATION_MANIFEST)

    def test_schemas_and_examples_match_the_packaging_constants(self):
        expectations = {
            "local.api.v1.health.schema.json": {
                "production_ready": False,
                "customer_pilot_allowed": False,
                "operator_authentication": True,
            },
            "local.api.v1.descriptor.schema.json": {
                "production_ready": False,
                "customer_pilot_allowed": False,
                "operator_authentication_manifest": True,
            },
            "local.api.v1.error.schema.json": {
                "approval_authority": False,
                "production_ready": False,
                "customer_pilot_allowed": False,
            },
            "operator.profile_b.session.schema.json": {
                "approval_authority": False,
                "approval_token_allowed": False,
                "arc_dispatch_allowed": False,
                "survives_restart": False,
                "operator_authentication_manifest": True,
            },
        }
        for name, fields in expectations.items():
            schema = json.loads((ROOT / "contracts" / "v1" / name).read_text(encoding="utf-8"))
            for field, expected in fields.items():
                self.assertEqual(expected, schema["properties"][field]["const"], f"{name} {field}")
        session = json.loads(
            (ROOT / "contracts" / "v1" / "operator.profile_b.session.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual("stub_only", session["properties"]["positive_approval_step_up"]["const"])
        health_example = json.loads(
            (ROOT / "contracts" / "examples" / "local.api.v1.health.example.json").read_text(encoding="utf-8")
        )
        self.assertTrue(health_example["operator_authentication"])
        self.assertFalse(health_example["production_ready"])
        self.assertFalse(health_example["customer_pilot_allowed"])

    def test_health_descriptor_summary_and_console_agree(self):
        api = LocalLoopbackApi()
        health = api.health()
        descriptor = api.descriptor()
        error = api.error("unauthenticated", "missing session")
        summary = ProfileBSessionService(MemoryEvidenceStore()).public_summary()
        projection = _profile_b_projection(None)
        self.assertTrue(health["operator_authentication"])
        self.assertFalse(health["production_ready"])
        self.assertFalse(health["customer_pilot_allowed"])
        self.assertTrue(health["runtime_authority_blocked"])
        self.assertEqual(health["operator_authentication"], descriptor["operator_authentication_manifest"])
        self.assertFalse(descriptor["production_ready"])
        self.assertFalse(descriptor["customer_pilot_allowed"])
        self.assertFalse(error["production_ready"])
        self.assertFalse(error["customer_pilot_allowed"])
        self.assertFalse(error["approval_authority"])
        self.assertNotIn("operator_authentication", error)
        self.assertFalse(summary["active"])
        self.assertTrue(summary["operator_authentication_manifest"])
        self.assertFalse(summary["approval_authority"])
        self.assertFalse(summary["survives_restart"])
        self.assertFalse(summary["production_identity_verified"])
        self.assertEqual("stub_only", summary["positive_approval_step_up"])
        self.assertTrue(projection["operator_authentication_manifest"])
        self.assertFalse(projection["approval_authority"])
        self.assertFalse(projection["survives_restart"])
        self.assertEqual("stub_only", projection["positive_approval_step_up"])

    def test_challenge_policy_and_sparkbot_boundary_stay_put(self):
        source = (ROOT / "lima_office" / "runtime" / "profile_b_session.py").read_text(encoding="utf-8")
        module = ast.parse(source)
        ttl = {
            node.targets[0].id: node.value.value
            for node in module.body
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "CHALLENGE_TTL_SECONDS"
            and isinstance(node.value, ast.Constant)
        }
        self.assertEqual({"CHALLENGE_TTL_SECONDS": 120}, ttl)
        verifier = (ROOT / "lima_office" / "runtime" / "webauthn_verifier.py").read_text(encoding="utf-8")
        self.assertIn('RP_ID = "localhost"', verifier)
        self.assertNotIn("sparkbot", (ROOT / "lima_office" / "runtime" / "lab_packaging.py").read_text(encoding="utf-8").lower())

    def test_workflows_do_not_publish_a_release(self):
        workflow_dir = ROOT / ".github" / "workflows"
        files = sorted(workflow_dir.glob("*.yml"))
        self.assertGreaterEqual(len(files), 1)
        banned = (
            "gh release",
            "action-gh-release",
            "create-release",
            "softprops",
            "build-lab-preview",
            "git tag",
            "upload-artifact",
        )
        for path in files:
            text = path.read_text(encoding="utf-8").lower()
            for phrase in banned:
                self.assertNotIn(phrase, text, f"{path.name} contains {phrase}")
            self.assertIn("contents: read", text)


if __name__ == "__main__":
    unittest.main()
