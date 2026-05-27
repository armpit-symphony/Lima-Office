import copy
import socket
import unittest
from unittest.mock import patch

from helpers import example, has_jsonschema, validator
from lima_office.guardian import GuardianReplayDrillSimulator
from lima_office.runtime.errors import (
    GuardianReplayDrillTransitionError,
    GuardianReplayDrillValidationError,
    UnsafeRuntimeActionError,
)


REFERENCE_TIME = "2026-05-18T21:44:00Z"


def decision_payload() -> dict:
    payload = copy.deepcopy(example("guardian.decision.allowed-one-time.example.json"))
    payload["decision_id"] = "gd-replay-drill-001"
    payload["guardian_decision_id"] = "gd-replay-drill-001"
    payload["request_id"] = "req-replay-drill-001"
    payload["decision_nonce"] = "decision-nonce-replay-drill-001"
    payload["replay_record_id"] = None
    payload["replay_artifact_id"] = None
    payload["approval_binding_id"] = "bind-replay-drill-001"
    payload["binding_id"] = "bind-replay-drill-001"
    payload["token_verification_id"] = "tv-replay-drill-001"
    payload["approval_chain_id"] = "chain-replay-drill-001"
    payload["approval_request_id"] = None
    payload["approval_token_id"] = None
    payload["bound_task_id"] = "task-replay-drill-001"
    payload["bound_worker_id"] = "arc-it-helper-01"
    payload["created_at"] = "2026-05-18T21:43:20Z"
    payload["issued_at"] = "2026-05-18T21:43:20Z"
    payload["effective_at"] = "2026-05-18T21:43:20Z"
    payload["expires_at"] = "2026-05-18T21:48:20Z"
    payload["evidence_refs"] = ["ev-guardian-email-draft-001", "ev-token-verify-valid-001"]
    payload["evidence_artifact_ids"] = ["ev-guardian-email-draft-001", "ev-token-verify-valid-001"]
    return payload


def replay_valid_payload() -> dict:
    payload = copy.deepcopy(example("guardian.replay.valid-first-use.example.json"))
    payload["guardian_decision_id"] = "gd-replay-drill-001"
    payload["replay_record_id"] = "rr-replay-drill-001"
    payload["decision_nonce"] = "decision-nonce-replay-drill-001"
    payload["approval_binding_id"] = "bind-replay-drill-001"
    payload["token_verification_id"] = "tv-replay-drill-001"
    payload["task_id"] = "task-replay-drill-001"
    payload["worker_id"] = "arc-it-helper-01"
    payload["checked_at"] = REFERENCE_TIME
    payload["expires_at"] = "2026-05-18T21:48:20Z"
    payload["decision_scope_hash"] = "hash-ref-approved-scope-email-001"
    payload["tool_scope"] = {
        "resource_refs": ["draft-message-ref-customer-reply-001", "recipient-ref-external-contact-001"],
        "allowed_operations": ["operator_review_draft"],
        "prohibited_operations": ["send_external_message", "live_connector_write", "reuse_token"],
    }
    payload["evidence_refs"] = ["ev-guardian-email-draft-001", "ev-token-verify-valid-001"]
    payload["post_action_evidence_refs"] = ["ev-guardian-email-draft-001"]
    return payload


def replay_denied_payload() -> dict:
    payload = copy.deepcopy(example("guardian.replay.replay-denied.example.json"))
    payload["guardian_decision_id"] = "gd-replay-drill-001"
    payload["replay_record_id"] = "rr-replay-drill-001"
    payload["decision_nonce"] = "decision-nonce-replay-drill-001"
    payload["approval_binding_id"] = "bind-replay-drill-001"
    payload["token_verification_id"] = "tv-replay-drill-001"
    payload["task_id"] = "task-replay-drill-001"
    payload["worker_id"] = "arc-it-helper-01"
    payload["checked_at"] = REFERENCE_TIME
    payload["mismatch_reasons"] = ["nonce_replayed"]
    payload["denial_evidence_ref"] = "ev-guardian-replay-denied-001"
    payload["pre_action_evidence_refs"] = ["ev-guardian-replay-denied-001"]
    payload["evidence_refs"] = ["ev-guardian-replay-denied-001"]
    return payload


def replay_expired_payload() -> dict:
    payload = copy.deepcopy(example("guardian.replay.expired.example.json"))
    payload["guardian_decision_id"] = "gd-replay-drill-001"
    payload["replay_record_id"] = "rr-replay-drill-001"
    payload["decision_nonce"] = "decision-nonce-replay-drill-001"
    payload["approval_binding_id"] = "bind-replay-drill-001"
    payload["token_verification_id"] = "tv-replay-drill-001"
    payload["task_id"] = "task-replay-drill-001"
    payload["worker_id"] = "arc-it-helper-01"
    payload["checked_at"] = REFERENCE_TIME
    payload["mismatch_reasons"] = ["decision_expired"]
    payload["denial_evidence_ref"] = "ev-guardian-expired-001"
    payload["pre_action_evidence_refs"] = ["ev-guardian-expired-001"]
    payload["evidence_refs"] = ["ev-guardian-expired-001"]
    return payload


def replay_stale_payload() -> dict:
    payload = replay_expired_payload()
    payload["replay_check_result"] = "stale"
    payload["mismatch_reasons"] = ["decision_stale"]
    payload["denial_evidence_ref"] = "ev-guardian-stale-001"
    payload["pre_action_evidence_refs"] = ["ev-guardian-stale-001"]
    payload["evidence_refs"] = ["ev-guardian-stale-001"]
    return payload


def replay_mismatch_payload() -> dict:
    payload = copy.deepcopy(example("guardian.replay.scope-mismatch.example.json"))
    payload["guardian_decision_id"] = "gd-replay-drill-001"
    payload["replay_record_id"] = "rr-replay-drill-001"
    payload["decision_nonce"] = "decision-nonce-replay-drill-001"
    payload["approval_binding_id"] = "bind-replay-drill-001"
    payload["token_verification_id"] = "tv-replay-drill-001"
    payload["task_id"] = "task-replay-drill-001"
    payload["worker_id"] = "arc-it-helper-01"
    return payload


def replay_blocked_payload() -> dict:
    payload = copy.deepcopy(example("guardian.replay.blocked-mvp.example.json"))
    payload["guardian_decision_id"] = "gd-replay-drill-001"
    payload["decision_nonce"] = "decision-nonce-replay-drill-001"
    payload["replay_record_id"] = "rr-replay-drill-001"
    payload["denial_evidence_ref"] = "ev-guardian-live-connector-blocked-001"
    payload["pre_action_evidence_refs"] = ["ev-guardian-live-connector-blocked-001"]
    payload["evidence_refs"] = ["ev-guardian-live-connector-blocked-001"]
    payload["mismatch_reasons"] = ["blocked_mvp"]
    return payload


def reserved_record_payload() -> dict:
    payload = copy.deepcopy(example("replay.store.record.consumed.example.json"))
    payload["replay_record_id"] = "rr-replay-drill-001"
    payload["guardian_decision_id"] = "gd-replay-drill-001"
    payload["decision_nonce"] = "decision-nonce-replay-drill-001"
    payload["approval_binding_id"] = "bind-replay-drill-001"
    payload["token_verification_id"] = "tv-replay-drill-001"
    payload["approval_token_id"] = "apt-replay-drill-001"
    payload["canonical_task_id"] = "task-replay-drill-001"
    payload["canonical_worker_id"] = "arc-it-helper-01"
    payload["nonce_status"] = "reserved"
    payload["atomicity_status"] = "pending"
    payload["consumed_at"] = None
    payload["failure_reason"] = None
    payload["denial_evidence_ref"] = None
    payload["checked_at"] = REFERENCE_TIME
    payload["created_at"] = REFERENCE_TIME
    return payload


def consumed_record_payload() -> dict:
    payload = copy.deepcopy(example("replay.store.record.consumed.example.json"))
    payload["replay_record_id"] = "rr-replay-drill-001"
    payload["guardian_decision_id"] = "gd-replay-drill-001"
    payload["decision_nonce"] = "decision-nonce-replay-drill-001"
    payload["approval_binding_id"] = "bind-replay-drill-001"
    payload["token_verification_id"] = "tv-replay-drill-001"
    payload["approval_token_id"] = "apt-replay-drill-001"
    payload["canonical_task_id"] = "task-replay-drill-001"
    payload["canonical_worker_id"] = "arc-it-helper-01"
    payload["consumed_at"] = REFERENCE_TIME
    payload["checked_at"] = REFERENCE_TIME
    payload["created_at"] = REFERENCE_TIME
    return payload


def failed_closed_record_payload() -> dict:
    payload = copy.deepcopy(example("replay.store.record.failed-closed.example.json"))
    payload["replay_record_id"] = "rr-replay-drill-001"
    payload["guardian_decision_id"] = "gd-replay-drill-001"
    payload["decision_nonce"] = "decision-nonce-replay-drill-001"
    payload["approval_binding_id"] = "bind-replay-drill-001"
    payload["token_verification_id"] = "tv-replay-drill-001"
    payload["approval_token_id"] = "apt-replay-drill-001"
    payload["checked_at"] = REFERENCE_TIME
    payload["created_at"] = REFERENCE_TIME
    payload["failure_reason"] = "mock replay store failed closed"
    payload["evidence_refs"] = ["ev-replay-store-unavailable-001"]
    return payload


def approval_binding_payload() -> dict:
    payload = copy.deepcopy(example("approval.binding.bound-valid.example.json"))
    payload["binding_id"] = "bind-replay-drill-001"
    payload["approval_chain_id"] = "chain-replay-drill-001"
    payload["approval_request_id"] = "apr-replay-drill-001"
    payload["approval_result_id"] = "apres-replay-drill-001"
    payload["approval_token_id"] = "apt-replay-drill-001"
    payload["token_verification_id"] = "tv-replay-drill-001"
    payload["guardian_decision_id"] = "gd-replay-drill-001"
    payload["task_id"] = "task-replay-drill-001"
    payload["worker_id"] = "arc-it-helper-01"
    payload["checked_at"] = REFERENCE_TIME
    payload["expires_at"] = "2026-05-18T21:48:20Z"
    return payload


def token_verification_payload() -> dict:
    payload = copy.deepcopy(example("token.verification.valid.example.json"))
    payload["token_verification_id"] = "tv-replay-drill-001"
    payload["approval_token_id"] = "apt-replay-drill-001"
    payload["approval_request_id"] = "apr-replay-drill-001"
    payload["task_id"] = "task-replay-drill-001"
    payload["guardian_decision_id"] = "gd-replay-drill-001"
    payload["checked_at"] = REFERENCE_TIME
    return payload


def requested_action_payload() -> dict:
    return {
        "tenant_id": "tenant-lab-001",
        "customer_context_id": "customer-context-main",
        "task_id": "task-replay-drill-001",
        "worker_id": "arc-it-helper-01",
        "guardian_decision_id": "gd-replay-drill-001",
        "approval_binding_id": "bind-replay-drill-001",
        "binding_id": "bind-replay-drill-001",
        "token_verification_id": "tv-replay-drill-001",
        "action_type": "draft_external_message_review",
        "tool_scope": {
            "resource_refs": ["draft-message-ref-customer-reply-001", "recipient-ref-external-contact-001"],
            "allowed_operations": ["operator_review_draft"],
            "prohibited_operations": ["send_external_message", "live_connector_write", "reuse_token"],
        },
        "decision_scope_hash": "hash-ref-approved-scope-email-001",
        "evidence_required": True,
        "evidence_refs": ["ev-guardian-email-draft-001", "ev-token-verify-valid-001"],
    }


@unittest.skipUnless(has_jsonschema(), "jsonschema is not installed")
class GuardianReplayDrillSimulatorTests(unittest.TestCase):
    def setUp(self):
        self.validator = validator()
        self.simulator = GuardianReplayDrillSimulator(self.validator, reference_time=REFERENCE_TIME)

    def _register_and_reserve(self, *, decision: dict | None = None):
        decision_payload_data = decision or decision_payload()
        self.simulator.register(decision_payload_data)
        self.simulator.transition("gd-replay-drill-001", "decision_registered", decision_payload_data)
        self.simulator.transition("gd-replay-drill-001", "nonce_reserved", reserved_record_payload())

    def test_valid_guardian_replay_examples_validate(self):
        self.validator.validate(example("guardian.decision.allowed-one-time.example.json"), "guardian.decision")
        self.validator.validate(example("guardian.replay.valid-first-use.example.json"), "guardian.replay")
        self.validator.validate(example("replay.store.record.consumed.example.json"), "replay.store.record")

    def test_safe_replay_path_passes(self):
        self._register_and_reserve()
        self.simulator.transition(
            "gd-replay-drill-001",
            "first_use_validated",
            replay_valid_payload(),
            requested_action=requested_action_payload(),
            approval_binding=approval_binding_payload(),
            token_verification=token_verification_payload(),
        )
        result = self.simulator.transition("gd-replay-drill-001", "nonce_consumed", consumed_record_payload())
        self.assertEqual("nonce_consumed", result["drill_state"])
        self.assertIn("decision-nonce-replay-drill-001", self.simulator.consumed_nonces)

    def test_nonce_consumed_to_replay_denied_passes(self):
        self._register_and_reserve()
        self.simulator.transition(
            "gd-replay-drill-001",
            "first_use_validated",
            replay_valid_payload(),
            requested_action=requested_action_payload(),
            approval_binding=approval_binding_payload(),
            token_verification=token_verification_payload(),
        )
        self.simulator.transition("gd-replay-drill-001", "nonce_consumed", consumed_record_payload())
        result = self.simulator.transition("gd-replay-drill-001", "replay_denied", replay_denied_payload())
        self.assertEqual("replay_denied", result["drill_state"])

    def test_expired_decision_goes_to_expired_denied_and_cannot_validate(self):
        decision = decision_payload()
        decision["expires_at"] = "2026-05-18T21:43:30Z"
        self._register_and_reserve(decision=decision)
        with self.assertRaises(GuardianReplayDrillTransitionError):
            self.simulator.transition(
                "gd-replay-drill-001",
                "first_use_validated",
                replay_valid_payload(),
                requested_action=requested_action_payload(),
            )
        result = self.simulator.transition("gd-replay-drill-001", "expired_denied", replay_expired_payload())
        self.assertEqual("expired_denied", result["drill_state"])

    def test_stale_decision_goes_to_stale_denied_and_cannot_validate(self):
        decision = decision_payload()
        decision["issued_at"] = "2026-05-18T21:30:00Z"
        decision["effective_at"] = "2026-05-18T21:30:00Z"
        decision["created_at"] = "2026-05-18T21:30:00Z"
        decision["expires_at"] = "2026-05-18T21:50:00Z"
        self._register_and_reserve(decision=decision)
        with self.assertRaises(GuardianReplayDrillTransitionError):
            self.simulator.transition(
                "gd-replay-drill-001",
                "first_use_validated",
                replay_valid_payload(),
                requested_action=requested_action_payload(),
            )
        result = self.simulator.transition("gd-replay-drill-001", "stale_denied", replay_stale_payload())
        self.assertEqual("stale_denied", result["drill_state"])

    def test_future_effective_at_beyond_skew_fails(self):
        decision = decision_payload()
        decision["effective_at"] = "2026-05-18T21:45:00Z"
        self._register_and_reserve(decision=decision)
        with self.assertRaises(GuardianReplayDrillTransitionError):
            self.simulator.transition(
                "gd-replay-drill-001",
                "first_use_validated",
                replay_valid_payload(),
                requested_action=requested_action_payload(),
            )

    def test_contradictory_timestamps_fail(self):
        decision = decision_payload()
        decision["effective_at"] = "2026-05-18T21:43:00Z"
        self._register_and_reserve(decision=decision)
        with self.assertRaises(GuardianReplayDrillTransitionError):
            self.simulator.transition(
                "gd-replay-drill-001",
                "first_use_validated",
                replay_valid_payload(),
                requested_action=requested_action_payload(),
            )

    def test_missing_nonce_fails(self):
        decision = decision_payload()
        decision["decision_nonce"] = None
        with self.assertRaises(GuardianReplayDrillValidationError):
            self.simulator.register(decision)

    def test_duplicate_nonce_consumption_fails(self):
        self._register_and_reserve()
        self.simulator.transition(
            "gd-replay-drill-001",
            "first_use_validated",
            replay_valid_payload(),
            requested_action=requested_action_payload(),
        )
        self.simulator.transition("gd-replay-drill-001", "nonce_consumed", consumed_record_payload())

        duplicate = decision_payload()
        duplicate["decision_id"] = "gd-replay-drill-duplicate-001"
        duplicate["guardian_decision_id"] = "gd-replay-drill-duplicate-001"
        duplicate["request_id"] = "req-replay-drill-duplicate-001"
        self.simulator.register(duplicate)
        self.simulator.transition("gd-replay-drill-duplicate-001", "decision_registered", duplicate)
        with self.assertRaises(GuardianReplayDrillTransitionError):
            self.simulator.transition("gd-replay-drill-duplicate-001", "nonce_reserved", reserved_record_payload())

    def test_cross_tenant_replay_fails(self):
        self._register_and_reserve()
        replay = replay_valid_payload()
        replay["tenant_id"] = "tenant-other"
        with self.assertRaises(GuardianReplayDrillTransitionError):
            self.simulator.transition("gd-replay-drill-001", "first_use_validated", replay, requested_action=requested_action_payload())

    def test_approval_binding_mismatch_fails(self):
        self._register_and_reserve()
        binding = approval_binding_payload()
        binding["binding_id"] = "bind-other"
        with self.assertRaises(GuardianReplayDrillTransitionError):
            self.simulator.transition(
                "gd-replay-drill-001",
                "first_use_validated",
                replay_valid_payload(),
                requested_action=requested_action_payload(),
                approval_binding=binding,
            )

    def test_token_verification_mismatch_fails(self):
        self._register_and_reserve()
        token = token_verification_payload()
        token["token_verification_id"] = "tv-other"
        with self.assertRaises(GuardianReplayDrillTransitionError):
            self.simulator.transition(
                "gd-replay-drill-001",
                "first_use_validated",
                replay_valid_payload(),
                requested_action=requested_action_payload(),
                token_verification=token,
            )

    def test_action_and_tool_scope_mismatch_fails(self):
        self._register_and_reserve()
        mismatched = requested_action_payload()
        mismatched["action_type"] = "file_review"
        mismatched["tool_scope"]["resource_refs"] = ["draft-message-ref-other-002"]
        with self.assertRaises(GuardianReplayDrillTransitionError):
            self.simulator.transition(
                "gd-replay-drill-001",
                "first_use_validated",
                replay_valid_payload(),
                requested_action=mismatched,
            )

    def test_worker_mismatch_fails(self):
        self._register_and_reserve()
        mismatched = requested_action_payload()
        mismatched["worker_id"] = "arc-other"
        with self.assertRaises(GuardianReplayDrillTransitionError):
            self.simulator.transition(
                "gd-replay-drill-001",
                "first_use_validated",
                replay_valid_payload(),
                requested_action=mismatched,
            )

    def test_blocked_mvp_decision_cannot_validate(self):
        decision = copy.deepcopy(example("guardian.decision.blocked-mvp.example.json"))
        decision["decision_nonce"] = "decision-nonce-blocked-mvp-001"
        with self.assertRaises(GuardianReplayDrillTransitionError):
            self.simulator.register(decision)

    def test_replay_denied_without_required_evidence_fails(self):
        self._register_and_reserve()
        self.simulator.transition(
            "gd-replay-drill-001",
            "first_use_validated",
            replay_valid_payload(),
            requested_action=requested_action_payload(),
        )
        self.simulator.transition("gd-replay-drill-001", "nonce_consumed", consumed_record_payload())
        denied = replay_denied_payload()
        denied["denial_evidence_ref"] = None
        denied["pre_action_evidence_refs"] = []
        with self.assertRaises((GuardianReplayDrillTransitionError, GuardianReplayDrillValidationError)):
            self.simulator.transition("gd-replay-drill-001", "replay_denied", denied)

    def test_failed_closed_without_required_evidence_fails(self):
        self._register_and_reserve()
        failed = failed_closed_record_payload()
        failed["evidence_refs"] = []
        with self.assertRaises((GuardianReplayDrillTransitionError, GuardianReplayDrillValidationError)):
            self.simulator.transition("gd-replay-drill-001", "failed_closed_recorded", failed)

    def test_history_is_in_memory_only(self):
        self._register_and_reserve()
        history = self.simulator.history("gd-replay-drill-001")
        self.assertGreaterEqual(len(history), 3)
        self.assertEqual("planned", history[0]["to_state"])
        self.assertEqual("nonce_reserved", history[-1]["to_state"])

    def test_simulator_never_writes_files(self):
        self._register_and_reserve()
        with patch("pathlib.Path.write_text", side_effect=AssertionError("unexpected file write")):
            with patch("pathlib.Path.write_bytes", side_effect=AssertionError("unexpected file write")):
                self.simulator.transition(
                    "gd-replay-drill-001",
                    "first_use_validated",
                    replay_valid_payload(),
                    requested_action=requested_action_payload(),
                )

    def test_simulator_never_calls_network(self):
        self._register_and_reserve()
        with patch.object(socket, "create_connection", side_effect=AssertionError("unexpected network call")):
            self.simulator.transition(
                "gd-replay-drill-001",
                "first_use_validated",
                replay_valid_payload(),
                requested_action=requested_action_payload(),
            )

    def test_simulator_never_persists_nonce_state(self):
        with self.assertRaises(UnsafeRuntimeActionError):
            self.simulator.persist_nonce_state("nonce-state")

    def test_simulator_never_authorizes_real_action(self):
        with self.assertRaises(UnsafeRuntimeActionError):
            self.simulator.authorize_real_action("task-001")


if __name__ == "__main__":
    unittest.main()
