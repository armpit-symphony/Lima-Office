import copy
import importlib.util
import sys
import unittest
from pathlib import Path

from helpers import example, has_jsonschema, validator
from lima_office.runtime.connector_reconciliation import classify_connector_reconciliation


ROOT = Path(__file__).resolve().parents[1]


def _load_checker_module():
    script_path = ROOT / "scripts" / "check-reason-codes.py"
    spec = importlib.util.spec_from_file_location("check_reason_codes_connector_reconcile", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load checker module from {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _tool_invocation_connector_payload() -> dict:
    payload = copy.deepcopy(example("tool.invocation.example.json"))
    payload["taxonomy_version"] = "taxonomy-reason-v1"
    payload["tenant_id"] = "tenant-lab-001"
    payload["customer_context_id"] = "customer-context-main"
    payload["requested_tool"] = {
        "tool_type": "connector",
        "tool_name": "connector.mock.email",
        "tool_version": "contract-only"
    }
    payload["tool_scope"] = {
        "resource_refs": ["connector-email-metadata-001"],
        "allowed_operations": ["metadata_read"],
        "prohibited_operations": ["external_send", "form_submit"],
        "file_scope": "none",
        "network_scope": "mock_only",
        "connector_scope": "mock_readiness_only"
    }
    payload["risk_tier"] = "medium"
    payload["status"] = "requested"
    payload["input_taint_status"] = "none"
    payload["connector_readiness_ref"] = "connector-readiness-email-001"
    payload["connector_scope_review_ref"] = "connector-scope-review-001"
    payload["connector_consent_ref"] = "connector-consent-email-001"
    payload["provider_profile_ref"] = "provider-profile-email-001"
    payload["connector_revocation_drill_ref"] = "connector-revocation-drill-001"
    payload["evidence_refs"] = ["ev-tool-connector-001"]
    return payload


def _connector_trust_payload() -> dict:
    payload = copy.deepcopy(example("connector.trust.example.json"))
    payload["taxonomy_version"] = "taxonomy-reason-v1"
    payload["connector_id"] = "connector-email-metadata-001"
    payload["provider_profile_ref"] = "provider-profile-email-001"
    payload["connector_readiness_ref"] = "connector-readiness-email-001"
    payload["connector_scope_review_ref"] = "connector-scope-review-001"
    payload["revocation_drill_refs"] = ["connector-revocation-drill-001"]
    payload["disable_switch_ref"] = "disable-switch-ref-001"
    payload["evidence_refs"] = ["ev-connector-trust-001"]
    return payload


@unittest.skipUnless(has_jsonschema(), "jsonschema is not installed")
class ConnectorTrustBoundaryLinkageInvariantTests(unittest.TestCase):
    def setUp(self):
        self.validator = validator()
        self.checker = _load_checker_module()

    def _build_linkage_inputs(self):
        provider = copy.deepcopy(example("connector.provider_profile.email-medium-risk.example.json"))
        readiness = copy.deepcopy(example("connector.readiness.email-approved-for-lab.example.json"))
        scope = copy.deepcopy(example("connector.scope_review.least-privilege-satisfied.example.json"))
        consent = copy.deepcopy(example("governance.connector_consent.revoked.example.json"))
        consent["consent_status"] = "granted_placeholder"
        consent["status"] = "mock_ready"
        trust = _connector_trust_payload()
        trust["revocation_status"] = "revocable"
        drill = copy.deepcopy(example("connector.revocation_drill.revocation-passed.example.json"))
        tool = _tool_invocation_connector_payload()
        approval = copy.deepcopy(example("approval.binding.bound-valid.example.json"))
        approval["taxonomy_version"] = "taxonomy-reason-v1"
        approval["tenant_id"] = "tenant-lab-001"
        approval["customer_context_id"] = "customer-context-main"
        approval["binding_id"] = "approval-binding-connector-read-001"
        guardian = copy.deepcopy(example("guardian.decision.blocked-mvp.example.json"))
        guardian["taxonomy_version"] = "taxonomy-reason-v1"
        guardian["tenant_id"] = "tenant-lab-001"
        guardian["customer_context_id"] = "customer-context-main"
        guardian["decision"] = "deny"
        guardian["guardian_decision_id"] = "gd-connector-read-001"
        guardian["connector_readiness_ref"] = "connector-readiness-email-001"
        guardian["connector_scope_review_ref"] = "connector-scope-review-001"
        guardian["connector_consent_ref"] = "connector-consent-email-001"
        guardian["provider_profile_ref"] = "provider-profile-email-001"
        guardian["connector_revocation_drill_ref"] = "connector-revocation-drill-001"
        artifact = copy.deepcopy(example("evidence.artifact.example.json"))
        artifact["taxonomy_version"] = "taxonomy-reason-v1"
        artifact["tenant_id"] = "tenant-lab-001"
        artifact["customer_context_id"] = "customer-context-main"
        artifact["artifact_id"] = "ev-artifact-connector-001"
        return provider, readiness, scope, trust, consent, drill, tool, approval, guardian, artifact

    def test_reconciliation_examples_validate(self):
        self.validator.validate(
            example("connector.reconciliation.reconciled.example.json"),
            "connector.reconciliation",
        )
        self.validator.validate(
            example("connector.reconciliation.consent-revoked-drift.example.json"),
            "connector.reconciliation",
        )
        self.validator.validate(
            example("connector.reconciliation.scope-overbroad-blocked.example.json"),
            "connector.reconciliation",
        )
        self.validator.validate(
            example("connector.reconciliation.provider-critical-failed-closed.example.json"),
            "connector.reconciliation",
        )
        self.validator.validate(
            example("connector.reconciliation.cross-tenant-blocked.example.json"),
            "connector.reconciliation",
        )
        self.validator.validate(
            example("console.alert.connector-reconciliation-drift.example.json"),
            "console.alert",
        )
        self.validator.validate(
            example("supervisor.health.connector-reconciliation-blocked.example.json"),
            "supervisor.health",
        )

    def test_valid_connector_linkage_reconciles_metadata_only(self):
        provider, readiness, scope, trust, consent, drill, tool, approval, guardian, artifact = (
            self._build_linkage_inputs()
        )
        result = classify_connector_reconciliation(
            provider_profile=provider,
            readiness=readiness,
            scope_review=scope,
            connector_trust=trust,
            consent=consent,
            revocation_drill=drill,
            tool_invocation=tool,
            approval_binding=approval,
            guardian_decision=guardian,
            evidence_artifact=artifact,
        )
        self.assertEqual("reconciled", result["reconciliation_status"])
        self.assertFalse(result["blocked"])
        self.assertFalse(result["can_authorize"])

    def test_consent_revoked_but_readiness_approved_fails(self):
        provider, readiness, scope, trust, consent, drill, tool, approval, guardian, artifact = (
            self._build_linkage_inputs()
        )
        consent["consent_status"] = "revoked"
        result = classify_connector_reconciliation(
            provider_profile=provider,
            readiness=readiness,
            scope_review=scope,
            connector_trust=trust,
            consent=consent,
            revocation_drill=drill,
            tool_invocation=tool,
            approval_binding=approval,
            guardian_decision=guardian,
            evidence_artifact=artifact,
        )
        self.assertEqual("failed_closed", result["reconciliation_status"])
        self.assertIn("consent_revoked_but_readiness_approved", result["drift_classes"])

    def test_scope_overbroad_but_invocation_requested_fails(self):
        provider, readiness, scope, trust, consent, drill, tool, approval, guardian, artifact = (
            self._build_linkage_inputs()
        )
        scope["least_privilege_status"] = "overbroad"
        result = classify_connector_reconciliation(
            provider_profile=provider,
            readiness=readiness,
            scope_review=scope,
            connector_trust=trust,
            consent=consent,
            revocation_drill=drill,
            tool_invocation=tool,
            approval_binding=approval,
            guardian_decision=guardian,
            evidence_artifact=artifact,
        )
        self.assertIn("scope_overbroad_but_invocation_requested", result["drift_classes"])

    def test_provider_critical_but_ready_without_required_evidence_fails(self):
        provider, readiness, scope, trust, consent, drill, tool, approval, guardian, artifact = (
            self._build_linkage_inputs()
        )
        provider["risk_level"] = "critical"
        provider["provider_status"] = "profiled"
        provider["evidence_refs"] = []
        result = classify_connector_reconciliation(
            provider_profile=provider,
            readiness=readiness,
            scope_review=scope,
            connector_trust=trust,
            consent=consent,
            revocation_drill=drill,
            tool_invocation=tool,
            approval_binding=approval,
            guardian_decision=guardian,
            evidence_artifact=artifact,
        )
        self.assertEqual("failed_closed", result["reconciliation_status"])
        self.assertIn("provider_critical_but_ready", result["drift_classes"])

    def test_revocation_drill_failed_but_connector_enabled_fails(self):
        provider, readiness, scope, trust, consent, drill, tool, approval, guardian, artifact = (
            self._build_linkage_inputs()
        )
        drill["drill_status"] = "failed_closed"
        result = classify_connector_reconciliation(
            provider_profile=provider,
            readiness=readiness,
            scope_review=scope,
            connector_trust=trust,
            consent=consent,
            revocation_drill=drill,
            tool_invocation=tool,
            approval_binding=approval,
            guardian_decision=guardian,
            evidence_artifact=artifact,
        )
        self.assertIn("revocation_drill_failed_but_connector_enabled", result["drift_classes"])

    def test_disable_switch_missing_but_readiness_approved_fails(self):
        provider, readiness, scope, trust, consent, drill, tool, approval, guardian, artifact = (
            self._build_linkage_inputs()
        )
        provider["disable_switch_status"] = "missing"
        result = classify_connector_reconciliation(
            provider_profile=provider,
            readiness=readiness,
            scope_review=scope,
            connector_trust=trust,
            consent=consent,
            revocation_drill=drill,
            tool_invocation=tool,
            approval_binding=approval,
            guardian_decision=guardian,
            evidence_artifact=artifact,
        )
        self.assertIn("disable_switch_missing_but_ready", result["drift_classes"])

    def test_outbound_action_without_approval_binding_guardian_or_evidence_fails(self):
        provider, readiness, scope, trust, consent, drill, tool, _, _, _ = self._build_linkage_inputs()
        tool["tool_scope"]["allowed_operations"] = ["external_send"]
        result = classify_connector_reconciliation(
            provider_profile=provider,
            readiness=readiness,
            scope_review=scope,
            connector_trust=trust,
            consent=consent,
            revocation_drill=drill,
            tool_invocation=tool,
            approval_binding=None,
            guardian_decision=None,
            evidence_artifact=None,
        )
        self.assertIn("outbound_action_missing_approval", result["drift_classes"])

    def test_tainted_connector_payload_used_for_privileged_tool_fails(self):
        provider, readiness, scope, trust, consent, drill, tool, approval, guardian, artifact = (
            self._build_linkage_inputs()
        )
        tool["input_taint_status"] = "confirmed"
        tool["risk_tier"] = "high"
        result = classify_connector_reconciliation(
            provider_profile=provider,
            readiness=readiness,
            scope_review=scope,
            connector_trust=trust,
            consent=consent,
            revocation_drill=drill,
            tool_invocation=tool,
            approval_binding=approval,
            guardian_decision=guardian,
            evidence_artifact=artifact,
        )
        self.assertIn("tainted_connector_payload_used_for_tool", result["drift_classes"])

    def test_cross_tenant_connector_linkage_fails(self):
        provider, readiness, scope, trust, consent, drill, tool, approval, guardian, artifact = (
            self._build_linkage_inputs()
        )
        consent["tenant_id"] = "tenant-lab-999"
        result = classify_connector_reconciliation(
            provider_profile=provider,
            readiness=readiness,
            scope_review=scope,
            connector_trust=trust,
            consent=consent,
            revocation_drill=drill,
            tool_invocation=tool,
            approval_binding=approval,
            guardian_decision=guardian,
            evidence_artifact=artifact,
        )
        self.assertEqual("failed_closed", result["reconciliation_status"])
        self.assertIn("connector_cross_tenant_linkage", result["drift_classes"])

    def test_connector_trust_revoked_but_guardian_allow_fails(self):
        provider, readiness, scope, trust, consent, drill, tool, approval, guardian, artifact = (
            self._build_linkage_inputs()
        )
        trust["revocation_status"] = "revoked"
        guardian["decision"] = "allow"
        result = classify_connector_reconciliation(
            provider_profile=provider,
            readiness=readiness,
            scope_review=scope,
            connector_trust=trust,
            consent=consent,
            revocation_drill=drill,
            tool_invocation=tool,
            approval_binding=approval,
            guardian_decision=guardian,
            evidence_artifact=artifact,
        )
        self.assertIn("connector_trust_revoked_but_guardian_allow", result["drift_classes"])

    def test_missing_evidence_fails(self):
        provider, readiness, scope, trust, consent, drill, tool, approval, guardian, artifact = (
            self._build_linkage_inputs()
        )
        provider["evidence_refs"] = []
        readiness["evidence_refs"] = []
        scope["evidence_refs"] = []
        consent["evidence_refs"] = []
        drill["evidence_refs"] = []
        tool["evidence_refs"] = []
        trust["evidence_refs"] = []
        result = classify_connector_reconciliation(
            provider_profile=provider,
            readiness=readiness,
            scope_review=scope,
            connector_trust=trust,
            consent=consent,
            revocation_drill=drill,
            tool_invocation=tool,
            approval_binding=approval,
            guardian_decision=guardian,
            evidence_artifact=artifact,
        )
        self.assertIn("connector_evidence_missing", result["drift_classes"])

    def test_helper_never_stores_reads_secrets_or_calls_external_apis(self):
        source = (ROOT / "lima_office" / "runtime" / "connector_reconciliation.py").read_text(
            encoding="utf-8"
        )
        banned_tokens = ("requests.", "httpx.", "socket.", "urllib.", "subprocess.", "oauth.")
        for token in banned_tokens:
            self.assertNotIn(token, source)

    def test_helper_never_authorizes_real_connector_use(self):
        provider, readiness, scope, trust, consent, drill, tool, approval, guardian, artifact = (
            self._build_linkage_inputs()
        )
        result = classify_connector_reconciliation(
            provider_profile=provider,
            readiness=readiness,
            scope_review=scope,
            connector_trust=trust,
            consent=consent,
            revocation_drill=drill,
            tool_invocation=tool,
            approval_binding=approval,
            guardian_decision=guardian,
            evidence_artifact=artifact,
        )
        self.assertFalse(result["can_authorize"])

    def test_reason_code_gate_passes_new_connector_reconciliation_codes(self):
        rc = int(self.checker.run_check(ROOT))
        self.assertEqual(0, rc)


if __name__ == "__main__":
    unittest.main()
