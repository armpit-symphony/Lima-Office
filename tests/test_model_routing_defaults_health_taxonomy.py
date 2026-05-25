import copy
import importlib.util
import sys
import unittest
from pathlib import Path

from helpers import example, has_jsonschema, validator
from lima_office.runtime.errors import PolicyDenyError
from lima_office.runtime.model_routing import classify_model_route


ROOT = Path(__file__).resolve().parents[1]


def _load_checker_module():
    script_path = ROOT / "scripts" / "check-reason-codes.py"
    spec = importlib.util.spec_from_file_location("check_reason_codes_model_route", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load checker module from {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(has_jsonschema(), "jsonschema is not installed")
class ModelRoutingDefaultsHealthTaxonomyTests(unittest.TestCase):
    def setUp(self):
        self.validator = validator()
        self.checker = _load_checker_module()

    def test_model_route_examples_validate(self):
        self.validator.validate(example("model.route.example.json"), "model.route")
        self.validator.validate(example("model.route.mock-only-selected.example.json"), "model.route")
        self.validator.validate(example("model.route.tainted-privileged-denied.example.json"), "model.route")
        self.validator.validate(
            example("model.route.subscription-planned-blocked-mvp.example.json"),
            "model.route",
        )
        self.validator.validate(example("model.route.local-planned-degraded.example.json"), "model.route")

    def test_supervisor_health_model_route_example_validates(self):
        self.validator.validate(
            example("supervisor.health.model-route-degraded.example.json"),
            "supervisor.health",
        )

    def test_console_alert_model_route_example_validates(self):
        self.validator.validate(
            example("console.alert.model-route-blocked.example.json"),
            "console.alert",
        )

    def test_mock_only_safe_route_metadata_passes(self):
        result = classify_model_route(copy.deepcopy(example("model.route.mock-only-selected.example.json")))
        self.assertFalse(result["can_authorize"])
        self.assertEqual("mock_only", result["route_mode"])
        self.assertEqual("selected", result["route_status"])

    def test_subscription_planned_cannot_imply_live_provider_call(self):
        payload = copy.deepcopy(example("model.route.subscription-planned-blocked-mvp.example.json"))
        payload["provider_ref"]["live_call"] = True
        with self.assertRaises(PolicyDenyError):
            classify_model_route(payload)

    def test_local_planned_cannot_imply_local_inference_execution(self):
        payload = copy.deepcopy(example("model.route.local-planned-degraded.example.json"))
        payload["local_model_bundle_ref"]["execution_enabled"] = True
        with self.assertRaises(PolicyDenyError):
            classify_model_route(payload)

    def test_tainted_privileged_route_is_denied_or_blocked(self):
        payload = copy.deepcopy(example("model.route.tainted-privileged-denied.example.json"))
        payload["route_status"] = "selected"
        with self.assertRaises(PolicyDenyError):
            classify_model_route(payload)

    def test_suspected_taint_privileged_route_is_denied_or_blocked(self):
        payload = copy.deepcopy(example("model.route.tainted-privileged-denied.example.json"))
        payload["taint_status"] = "suspected"
        payload["route_status"] = "selected"
        with self.assertRaises(PolicyDenyError):
            classify_model_route(payload)

    def test_high_risk_requires_approval_or_blocked(self):
        payload = copy.deepcopy(example("model.route.mock-only-selected.example.json"))
        payload["risk_tier"] = "high"
        payload["approval_required"] = False
        payload["route_status"] = "selected"
        with self.assertRaises(PolicyDenyError):
            classify_model_route(payload)

    def test_untrusted_device_blocks_privileged_route(self):
        payload = copy.deepcopy(example("model.route.mock-only-selected.example.json"))
        payload["risk_tier"] = "high"
        payload["approval_required"] = True
        payload["route_reason_codes"] = ["model_route_device_untrusted"]
        payload["route_status"] = "selected"
        with self.assertRaises(PolicyDenyError):
            classify_model_route(payload)

    def test_unknown_route_mode_fails_closed(self):
        payload = copy.deepcopy(example("model.route.mock-only-selected.example.json"))
        payload["route_mode"] = "live_cloud"
        with self.assertRaises(PolicyDenyError):
            classify_model_route(payload)

    def test_unknown_model_role_fails_closed(self):
        payload = copy.deepcopy(example("model.route.mock-only-selected.example.json"))
        payload["model_role"] = "unknown_role"
        with self.assertRaises(PolicyDenyError):
            classify_model_route(payload)

    def test_unknown_taint_status_fails_closed(self):
        payload = copy.deepcopy(example("model.route.mock-only-selected.example.json"))
        payload["taint_status"] = "unclassified"
        with self.assertRaises(PolicyDenyError):
            classify_model_route(payload)

    def test_fallback_allowed_without_policy_fails(self):
        payload = copy.deepcopy(example("model.route.local-planned-degraded.example.json"))
        payload["fallback_allowed"] = True
        payload["fallback_policy"] = None
        with self.assertRaises(PolicyDenyError):
            classify_model_route(payload)

    def test_reason_code_gate_passes_model_route_and_health_codes(self):
        rc = int(self.checker.run_check(ROOT))
        self.assertEqual(0, rc)

    def test_helper_never_authorizes_or_calls_models(self):
        payload = copy.deepcopy(example("model.route.local-planned-degraded.example.json"))
        result = classify_model_route(payload)
        self.assertFalse(result["can_authorize"])
        self.assertTrue(result["fail_closed"] or result["degraded"])


if __name__ == "__main__":
    unittest.main()
