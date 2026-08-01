from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from copy import deepcopy
import hashlib
import json
import tempfile
import unittest

from lima_office.contracts import ContractLoader, ContractValidator
from lima_office.evidence.sqlite_store import SQLiteEvidenceStore
from lima_office.guardian.authority import GuardianCoreAuthority
from lima_office.runtime.errors import (
    ContractValidationError,
    EvidenceWriteError,
    PolicyDenyError,
    WorkerChannelAuthenticationError,
    WorkerEndpointUnavailableError,
)
from lima_office.supervisor.arc_worker import LocalArcWorkerPreviewEndpoint
from lima_office.supervisor.control_plane import SupervisorControlPlane
from lima_office.supervisor.worker_registry import WorkerRegistry


FIXED_TIME = datetime(2026, 7, 24, 4, 0, tzinfo=timezone.utc)


class FakeGuardianDecider:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def __call__(self, tool_name: str, args: dict[str, object], **kwargs: object) -> SimpleNamespace:
        self.calls.append({"tool_name": tool_name, "args": args, "kwargs": kwargs})
        if "external_write" in tool_name or "file_mutation" in tool_name:
            action = "confirm"
        elif "credential" in tool_name:
            action = "privileged_reveal"
        elif "shell" in tool_name or "unknown" in tool_name:
            action = "deny"
        else:
            action = "allow"
        return SimpleNamespace(action=action, high_risk=action != "allow", reason="lab policy")


class FakeLimaRunner:
    def __init__(self, *, source_policy: str = "guardian_core.policy") -> None:
        self.source_policy = source_policy
        self.calls: list[dict[str, object]] = []

    def __call__(self, request: dict[str, object]) -> dict[str, object]:
        self.calls.append(request)
        category = request["action_category"]
        if category == "informational":
            status, allowed, approval, risk = "allowed_dry_run", True, False, "low"
        elif category in {"external_write", "file_mutation"}:
            status, allowed, approval, risk = "confirm_required", False, True, "medium"
        elif category == "credential_access":
            status, allowed, approval, risk = "privileged_required", False, True, "high"
        else:
            status, allowed, approval, risk = "denied", False, False, "blocked"
        guardian_binding = deepcopy(request["guardian_binding"])
        binding_hash = "sha256:" + hashlib.sha256(
            json.dumps(
                guardian_binding,
                ensure_ascii=True,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()
        decision_id = f"decision:{request['request_id']}:{binding_hash}"
        return {
            "decision_id": decision_id,
            "request_id": request["request_id"],
            "consumer": request["consumer"],
            "status": status,
            "allowed": allowed,
            "requires_approval": approval,
            "risk_level": risk,
            "reason_codes": ["lab_policy"],
            "source_policy": self.source_policy,
            "executable": False,
            "execution_allowed": False,
            "side_effects_allowed": False,
            "metadata": {
                "request": deepcopy(request),
                "guardian_binding": guardian_binding,
                "guardian_binding_present": True,
                "guardian_binding_hash": binding_hash,
                "guardian_decision_id": guardian_binding["decision_id"],
                "guardian_binding_mode": guardian_binding["binding_mode"],
            },
            "audit_event": {
                "request_id": request["request_id"],
                "decision_id": decision_id,
                "metadata": {
                    "guardian_binding_present": True,
                    "guardian_binding_hash": binding_hash,
                    "guardian_decision_id": guardian_binding["decision_id"],
                    "guardian_binding_mode": guardian_binding["binding_mode"],
                },
            },
        }


class UnavailableGuardian:
    def evaluate(self, request: dict[str, object]) -> dict[str, object]:
        raise PolicyDenyError("Guardian unavailable")


class ArcGovernedControlPlaneTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.validator = ContractValidator(ContractLoader().load())
        self.registry = WorkerRegistry()
        self.registry.register_mock_worker(
            worker_id="arc-worker-001",
            tenant_id="tenant-lab-001",
            role="arc-office-worker",
            capabilities=["document_read", "it_diagnostics_read_only", "draft_workspace"],
        )
        self.guardian_decider = FakeGuardianDecider()
        self.lima_runner = FakeLimaRunner()
        self.endpoint = LocalArcWorkerPreviewEndpoint(
            worker_id="arc-worker-001",
            tenant_id="tenant-lab-001",
            capabilities={"document_read", "it_diagnostics_read_only", "draft_workspace"},
            validator=self.validator,
        )
        self.store_path = Path(self.temporary.name) / "control-plane.db"
        self.store = SQLiteEvidenceStore(self.store_path, self.validator)
        self.addCleanup(self.store.close)

    def _control_plane(
        self,
        *,
        guardian: object | None = None,
        lima_runner: FakeLimaRunner | None = None,
        store: SQLiteEvidenceStore | None = None,
        endpoint: LocalArcWorkerPreviewEndpoint | None = None,
    ) -> SupervisorControlPlane:
        return SupervisorControlPlane(
            tenant_id="tenant-lab-001",
            customer_context_id="customer-context-main",
            authenticated_actors={"operator-lab-001": "operator"},
            validator=self.validator,
            registry=self.registry,
            evidence_store=store or self.store,
            guardian_authority=guardian
            or GuardianCoreAuthority(self.validator, decider=self.guardian_decider),
            lima_runner=lima_runner or self.lima_runner,
            worker_endpoints={"arc-worker-001": endpoint or self.endpoint},
            clock=lambda: FIXED_TIME,
        )

    def _authenticated_control_plane(
        self,
        *,
        refresher: object | None,
        endpoint: object | None = None,
    ) -> SupervisorControlPlane:
        self.registry = WorkerRegistry()
        worker = self.registry.register_authenticated_worker(
            worker_id="arc-worker-001",
            tenant_id="tenant-lab-001",
            role="arc-office-worker",
            capabilities=[
                "document_read",
                "it_diagnostics_read_only",
                "draft_workspace",
            ],
            channel_identity_ref="worker-key-001",
            boot_id="boot-001",
            worker_version="arc-bot-shell-0.1.0",
            policy_hash="guardian-policy-lab-v1",
        )
        worker.state = "healthy"
        refreshers = (
            {"arc-worker-001": refresher}
            if callable(refresher)
            else {}
        )
        return SupervisorControlPlane(
            tenant_id="tenant-lab-001",
            customer_context_id="customer-context-main",
            authenticated_actors={"operator-lab-001": "operator"},
            validator=self.validator,
            registry=self.registry,
            evidence_store=self.store,
            guardian_authority=GuardianCoreAuthority(
                self.validator,
                decider=self.guardian_decider,
            ),
            lima_runner=self.lima_runner,
            worker_endpoints={
                "arc-worker-001": endpoint or self.endpoint
            },
            worker_health_refreshers=refreshers,
            policy_version="guardian-policy-lab-v1",
            require_authenticated_workers=True,
            clock=lambda: FIXED_TIME,
        )

    @staticmethod
    def _request(
        *,
        action: str = "safe_read",
        request_id: str = "request-001",
        idempotency_key: str = "idem-001",
    ) -> dict[str, str]:
        return {
            "request_id": request_id,
            "tenant_id": "tenant-lab-001",
            "actor_id": "operator-lab-001",
            "action": action,
            "resource_type": "worker_status",
            "resource_id": "arc-worker-001",
            "worker_id": "arc-worker-001",
            "idempotency_key": idempotency_key,
        }

    def test_safe_read_reaches_arc_acknowledgement_and_persists_evidence(self) -> None:
        result = self._control_plane().submit(self._request())

        self.assertEqual(result["status"], "acknowledged")
        self.assertEqual(result["classification_authority"], "supervisor_server_derived")
        self.assertEqual(result["action_category"], "informational")
        self.assertEqual(result["guardian"]["decision"], "allow_with_evidence")
        self.assertEqual(result["lima"]["status"], "allowed_dry_run")
        self.assertEqual(result["lima"]["source_policy"], "guardian_core.policy")
        self.assertEqual(
            result["lima"]["guardian_decision_id"],
            result["guardian"]["decision_id"],
        )
        self.assertEqual(
            result["lima"]["guardian_binding_mode"],
            "reference_only_non_authorizing",
        )
        self.assertTrue(
            result["lima"]["guardian_binding_hash"].startswith("sha256:")
        )
        self.assertEqual(result["assignment"]["status"], "acknowledged")
        self.assertTrue(result["runtime_authority_blocked"])
        self.assertFalse(result["executable"])
        self.assertFalse(result["execution_allowed"])
        self.assertFalse(result["side_effects_allowed"])
        self.assertEqual(len(self.guardian_decider.calls), 1)
        self.assertEqual(len(self.lima_runner.calls), 1)
        self.assertEqual(len(self.endpoint.received_previews), 1)
        lima_call = self.lima_runner.calls[0]
        self.assertEqual(
            lima_call["guardian_binding"]["decision_id"],
            result["guardian"]["decision_id"],
        )
        self.assertEqual(
            lima_call["guardian_binding"]["policy_snapshot_hash"],
            result["guardian"]["policy_snapshot_hash"],
        )
        self.assertEqual(
            lima_call["trust_context"]["worker_id"],
            "arc-worker-001",
        )
        self.assertEqual(
            [event["event_type"] for event in result["evidence"]],
            [
                "request_received",
                "guardian_request",
                "guardian_decision",
                "lima_decision",
                "assignment_preview",
                "worker_acknowledgement",
            ],
        )
        lima_event = next(
            event
            for event in result["evidence"]
            if event["event_type"] == "lima_decision"
        )
        self.assertEqual(
            lima_event["guardian_binding_hash"],
            result["lima"]["guardian_binding_hash"],
        )

    def test_lima_guardian_reference_tampering_fails_before_arc(self) -> None:
        tamper_cases = {
            "decision_id": ("guardian_binding", "decision_id", "other-decision"),
            "policy_snapshot_hash": (
                "guardian_binding",
                "policy_snapshot_hash",
                "sha256:" + ("0" * 64),
            ),
            "tenant": ("guardian_binding", "bound_tenant_id", "other-tenant"),
            "worker": ("guardian_binding", "bound_worker_id", "other-worker"),
            "action": ("guardian_binding", "bound_action_type", "status"),
            "expiry": (
                "guardian_binding",
                "expires_at",
                "2099-01-01T00:00:00Z",
            ),
            "binding_hash": (
                "metadata",
                "guardian_binding_hash",
                "sha256:" + ("f" * 64),
            ),
            "audit_hash": (
                "audit_metadata",
                "guardian_binding_hash",
                "sha256:" + ("e" * 64),
            ),
        }
        for index, (name, (target, field, value)) in enumerate(
            tamper_cases.items(),
            start=1,
        ):
            with self.subTest(name=name):
                base_runner = FakeLimaRunner()

                def tampering_runner(
                    request: dict[str, object],
                    *,
                    _target: str = target,
                    _field: str = field,
                    _value: str = value,
                ) -> dict[str, object]:
                    decision = base_runner(request)
                    if _target == "guardian_binding":
                        decision["metadata"]["guardian_binding"][_field] = _value
                    elif _target == "metadata":
                        decision["metadata"][_field] = _value
                    else:
                        decision["audit_event"]["metadata"][_field] = _value
                    return decision

                result = self._control_plane(
                    lima_runner=tampering_runner,
                ).submit(
                    self._request(
                        request_id=f"request-binding-tamper-{index}",
                        idempotency_key=f"idem-binding-tamper-{index}",
                    )
                )

                self.assertEqual(result["status"], "denied")
                self.assertIsNone(result["lima"])
                self.assertEqual(
                    result["evidence"][-1]["event_type"],
                    "failure",
                )
        self.assertEqual(self.endpoint.received_previews, [])

    def test_guardian_policy_identity_is_stable_and_preserves_resource_type(self) -> None:
        control_plane = self._control_plane()
        safe_request = control_plane._normalize_request(self._request())
        safe_guardian_request = control_plane._guardian_request(
            safe_request,
            "ev-request-001-request-received-1",
        )
        safe_decision = GuardianCoreAuthority(
            self.validator,
            decider=self.guardian_decider,
        ).evaluate(safe_guardian_request)

        second_request = control_plane._normalize_request(
            self._request(
                request_id="request-policy-identity-002",
                idempotency_key="idem-policy-identity-002",
            )
        )
        second_decision = GuardianCoreAuthority(
            self.validator,
            decider=self.guardian_decider,
        ).evaluate(
            control_plane._guardian_request(
                second_request,
                "ev-request-policy-identity-002-request-received-1",
            )
        )

        write_request = control_plane._normalize_request(
            self._request(
                action="external_write",
                request_id="request-policy-write-003",
                idempotency_key="idem-policy-write-003",
            )
        )
        write_decision = GuardianCoreAuthority(
            self.validator,
            decider=self.guardian_decider,
        ).evaluate(
            control_plane._guardian_request(
                write_request,
                "ev-request-policy-write-003-request-received-1",
            )
        )

        self.assertEqual(
            safe_decision["resource_ref"]["resource_type"],
            "worker_status",
        )
        self.assertEqual(
            safe_decision["policy_snapshot_hash"],
            second_decision["policy_snapshot_hash"],
        )
        self.assertNotEqual(
            safe_decision["policy_snapshot_hash"],
            safe_guardian_request["payload_hash"],
        )
        self.assertNotEqual(
            safe_decision["policy_snapshot_hash"],
            write_decision["policy_snapshot_hash"],
        )

    def test_caller_cannot_supply_classification_or_tool_identity(self) -> None:
        request = self._request()
        request["action_category"] = "informational"

        with self.assertRaises(ContractValidationError):
            self._control_plane().submit(request)

        self.assertEqual(self.guardian_decider.calls, [])
        self.assertEqual(self.lima_runner.calls, [])
        self.assertEqual(self.endpoint.received_previews, [])

    def test_malformed_request_fails_before_authority_or_evidence(self) -> None:
        request = self._request(request_id="request-malformed")
        del request["resource_id"]

        with self.assertRaises(ContractValidationError):
            self._control_plane().submit(request)

        self.assertEqual(self.guardian_decider.calls, [])
        self.assertEqual(self.lima_runner.calls, [])
        self.assertEqual(self.endpoint.received_previews, [])
        self.assertEqual(self.store.events_for_request("request-malformed", "tenant-lab-001"), [])

    def test_guardian_unavailable_denies_before_lima_or_arc(self) -> None:
        result = self._control_plane(guardian=UnavailableGuardian()).submit(self._request())

        self.assertEqual(result["status"], "denied")
        self.assertIsNone(result["guardian"])
        self.assertIsNone(result["lima"])
        self.assertEqual(self.lima_runner.calls, [])
        self.assertEqual(self.endpoint.received_previews, [])
        self.assertEqual(result["evidence"][-1]["event_type"], "denial")

    def test_lima_static_fallback_is_forbidden_on_supervisor_path(self) -> None:
        fallback = FakeLimaRunner(source_policy="lima_static_policy_fallback")
        result = self._control_plane(lima_runner=fallback).submit(self._request())

        self.assertEqual(result["status"], "denied")
        self.assertIsNotNone(result["guardian"])
        self.assertIsNone(result["lima"])
        self.assertEqual(self.endpoint.received_previews, [])
        self.assertEqual(result["evidence"][-1]["event_type"], "failure")

    def test_lima_reason_details_are_redacted_from_public_result(self) -> None:
        runner = FakeLimaRunner()

        def leaking_runner(request: dict[str, object]) -> dict[str, object]:
            decision = runner(request)
            decision["reason_codes"] = [
                "lab_policy",
                "Runtime error: C:\\internal\\module.py",
                "/private/runtime/path",
            ]
            return decision

        result = self._control_plane(lima_runner=leaking_runner).submit(self._request())

        self.assertEqual(result["lima"]["reason_codes"], ["lab_policy"])

    def test_external_write_stops_at_approval_request(self) -> None:
        result = self._control_plane().submit(
            self._request(action="external_write", request_id="request-write")
        )

        self.assertEqual(result["status"], "confirm_required")
        self.assertEqual(result["guardian"]["decision"], "requires_approval")
        self.assertEqual(result["lima"]["status"], "confirm_required")
        self.assertEqual(self.endpoint.received_previews, [])
        self.assertEqual(result["evidence"][-1]["event_type"], "approval_requested")

    def test_shell_credential_and_unknown_requests_stop_without_assignment(self) -> None:
        expected = {
            "shell": "denied",
            "credential_access": "privileged_required",
            "unknown": "denied",
        }
        for index, (action, expected_status) in enumerate(expected.items(), start=1):
            with self.subTest(action=action):
                result = self._control_plane().submit(
                    self._request(
                        action=action,
                        request_id=f"request-risk-{index}",
                        idempotency_key=f"idem-risk-{index}",
                    )
                )
                self.assertEqual(result["status"], expected_status)
                self.assertTrue(result["runtime_authority_blocked"])
                self.assertFalse(result["executable"])
                self.assertFalse(result["execution_allowed"])
                self.assertFalse(result["side_effects_allowed"])
        self.assertEqual(self.endpoint.received_previews, [])

    def test_wrong_tenant_and_actor_fail_before_authority_calls(self) -> None:
        wrong_tenant = self._request(request_id="request-wrong-tenant")
        wrong_tenant["tenant_id"] = "tenant-other"
        with self.assertRaises(PolicyDenyError):
            self._control_plane().submit(wrong_tenant)

        wrong_actor = self._request(request_id="request-wrong-actor")
        wrong_actor["actor_id"] = "unknown-actor"
        with self.assertRaises(PolicyDenyError):
            self._control_plane().submit(wrong_actor)

        self.assertEqual(self.guardian_decider.calls, [])
        self.assertEqual(self.lima_runner.calls, [])
        self.assertEqual(self.endpoint.received_previews, [])

    def test_expired_guardian_decision_denies_before_lima(self) -> None:
        authority = GuardianCoreAuthority(self.validator, decider=self.guardian_decider)

        class ExpiredAuthority:
            def evaluate(inner_self, request: dict[str, object]) -> dict[str, object]:
                decision = authority.evaluate(request)
                decision["expires_at"] = "2026-07-24T03:59:59Z"
                return decision

        result = self._control_plane(guardian=ExpiredAuthority()).submit(
            self._request(request_id="request-expired")
        )

        self.assertEqual(result["status"], "denied")
        self.assertEqual(self.lima_runner.calls, [])
        self.assertEqual(self.endpoint.received_previews, [])

    def test_lima_runtime_error_fails_closed_before_arc(self) -> None:
        def unavailable_runner(request: dict[str, object]) -> dict[str, object]:
            raise RuntimeError("internal path must not be returned")

        result = self._control_plane(lima_runner=unavailable_runner).submit(
            self._request(request_id="request-lima-unavailable")
        )

        self.assertEqual(result["status"], "denied")
        self.assertIsNone(result["lima"])
        self.assertNotIn("internal path", str(result))
        self.assertEqual(self.endpoint.received_previews, [])

    def test_offline_worker_is_blocked_after_governance_without_preview_delivery(self) -> None:
        self.registry.update_state("arc-worker-001", "offline", "test offline")

        result = self._control_plane().submit(self._request(request_id="request-offline"))

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_codes"], ["worker_stale"])
        self.assertEqual(self.endpoint.received_previews, [])
        self.assertEqual(result["evidence"][-1]["event_type"], "denial")

    def test_quarantined_worker_remains_blocked_without_preview_delivery(self) -> None:
        self.registry.quarantine("arc-worker-001", "test quarantine")

        result = self._control_plane().submit(
            self._request(request_id="request-quarantined", idempotency_key="idem-quarantined")
        )

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_codes"], ["worker_quarantined"])
        self.assertEqual(self.endpoint.received_previews, [])
        self.assertFalse(result["execution_allowed"])

    def test_operational_path_rejects_mock_worker_without_authenticated_registration(
        self,
    ) -> None:
        control_plane = SupervisorControlPlane(
            tenant_id="tenant-lab-001",
            customer_context_id="customer-context-main",
            authenticated_actors={"operator-lab-001": "operator"},
            validator=self.validator,
            registry=self.registry,
            evidence_store=self.store,
            guardian_authority=GuardianCoreAuthority(
                self.validator,
                decider=self.guardian_decider,
            ),
            lima_runner=self.lima_runner,
            worker_endpoints={"arc-worker-001": self.endpoint},
            require_authenticated_workers=True,
            clock=lambda: FIXED_TIME,
        )

        result = control_plane.submit(
            self._request(
                request_id="request-unauthenticated-worker",
                idempotency_key="idem-unauthenticated-worker",
            )
        )

        self.assertEqual("blocked", result["status"])
        self.assertEqual([], self.endpoint.received_previews)
        self.assertTrue(result["runtime_authority_blocked"])
        self.assertFalse(result["execution_allowed"])

    def test_operational_path_refreshes_authenticated_heartbeat_before_assignment(
        self,
    ) -> None:
        calls = []

        def refresh() -> object:
            calls.append("heartbeat")
            return self.registry.get("arc-worker-001")

        result = self._authenticated_control_plane(
            refresher=refresh,
        ).submit(
            self._request(
                request_id="request-health-refresh",
                idempotency_key="idem-health-refresh",
            )
        )

        self.assertEqual(["heartbeat"], calls)
        self.assertEqual("acknowledged", result["status"])
        self.assertEqual(
            [
                "request_received",
                "guardian_request",
                "guardian_decision",
                "lima_decision",
                "worker_heartbeat",
                "assignment_preview",
                "worker_acknowledgement",
            ],
            [event["event_type"] for event in result["evidence"]],
        )
        self.assertFalse(result["execution_allowed"])

    def test_unavailable_health_refresh_marks_worker_offline_and_blocks(
        self,
    ) -> None:
        def unavailable() -> object:
            raise WorkerEndpointUnavailableError("private detail")

        result = self._authenticated_control_plane(
            refresher=unavailable,
        ).submit(
            self._request(
                request_id="request-worker-disconnected",
                idempotency_key="idem-worker-disconnected",
            )
        )

        self.assertEqual("blocked", result["status"])
        self.assertEqual(["worker_stale"], result["reason_codes"])
        self.assertEqual(
            "offline",
            self.registry.get("arc-worker-001").state,
        )
        self.assertEqual(
            "offline",
            self.store.worker_records("tenant-lab-001")[0]["state"],
        )
        self.assertNotIn("private detail", str(result))
        self.assertEqual([], self.endpoint.received_previews)
        self.assertEqual(
            result["evidence"][-2]["event_id"],
            result["evidence"][-1]["parent_event_id"],
        )

    def test_invalid_health_response_quarantines_worker_and_blocks(
        self,
    ) -> None:
        def invalid() -> object:
            raise WorkerChannelAuthenticationError("signature detail")

        result = self._authenticated_control_plane(
            refresher=invalid,
        ).submit(
            self._request(
                request_id="request-worker-invalid",
                idempotency_key="idem-worker-invalid",
            )
        )

        self.assertEqual("blocked", result["status"])
        self.assertEqual(["worker_quarantined"], result["reason_codes"])
        self.assertEqual(
            "quarantined",
            self.registry.get("arc-worker-001").state,
        )
        self.assertEqual(
            "quarantined",
            self.store.worker_records("tenant-lab-001")[0]["state"],
        )
        self.assertNotIn("signature detail", str(result))
        self.assertEqual([], self.endpoint.received_previews)

    def test_unexpected_acknowledgement_failure_is_blocked_and_redacted(
        self,
    ) -> None:
        class FailingEndpoint:
            def acknowledge_preview(
                inner_self,
                assignment: dict[str, object],
            ) -> dict[str, object]:
                raise RuntimeError("private worker implementation detail")

        def refresh() -> object:
            return self.registry.get("arc-worker-001")

        result = self._authenticated_control_plane(
            refresher=refresh,
            endpoint=FailingEndpoint(),
        ).submit(
            self._request(
                request_id="request-worker-failure",
                idempotency_key="idem-worker-failure",
            )
        )

        self.assertEqual("blocked", result["status"])
        self.assertEqual(["health_degraded"], result["reason_codes"])
        self.assertNotIn("private worker implementation detail", str(result))
        self.assertEqual(
            "failed_closed",
            result["evidence"][-1]["outcome"],
        )
        self.assertFalse(result["execution_allowed"])

    def test_authenticated_routing_without_health_refresher_fails_closed(
        self,
    ) -> None:
        result = self._authenticated_control_plane(
            refresher=None,
        ).submit(
            self._request(
                request_id="request-health-refresh-missing",
                idempotency_key="idem-health-refresh-missing",
            )
        )

        self.assertEqual("blocked", result["status"])
        self.assertEqual(["worker_stale"], result["reason_codes"])
        self.assertEqual([], self.endpoint.received_previews)

    def test_supervisor_scales_same_non_executing_path_to_two_and_eight_workers(self) -> None:
        registry = WorkerRegistry(max_workers=8)
        endpoints: dict[str, LocalArcWorkerPreviewEndpoint] = {}
        for index in range(1, 9):
            worker_id = f"arc-worker-{index:03d}"
            registry.register_mock_worker(
                worker_id=worker_id,
                tenant_id="tenant-lab-001",
                role="arc-office-worker",
                capabilities=["document_read"],
            )
            endpoints[worker_id] = LocalArcWorkerPreviewEndpoint(
                worker_id=worker_id,
                tenant_id="tenant-lab-001",
                capabilities={"document_read"},
                validator=self.validator,
            )
        store = SQLiteEvidenceStore(Path(self.temporary.name) / "scale.db", self.validator)
        self.addCleanup(store.close)
        control_plane = SupervisorControlPlane(
            tenant_id="tenant-lab-001",
            customer_context_id="customer-context-main",
            authenticated_actors={"operator-lab-001": "operator"},
            validator=self.validator,
            registry=registry,
            evidence_store=store,
            guardian_authority=GuardianCoreAuthority(
                self.validator,
                decider=self.guardian_decider,
            ),
            lima_runner=self.lima_runner,
            worker_endpoints=endpoints,
            clock=lambda: FIXED_TIME,
        )
        workers = list(endpoints)
        two = control_plane.submit_many(
            self._request(request_id="request-batch-two", idempotency_key="idem-batch-two"),
            workers[:2],
        )
        store_eight = SQLiteEvidenceStore(
            Path(self.temporary.name) / "scale-eight.db",
            self.validator,
        )
        self.addCleanup(store_eight.close)
        control_plane_eight = SupervisorControlPlane(
            tenant_id="tenant-lab-001",
            customer_context_id="customer-context-main",
            authenticated_actors={"operator-lab-001": "operator"},
            validator=self.validator,
            registry=registry,
            evidence_store=store_eight,
            guardian_authority=GuardianCoreAuthority(
                self.validator,
                decider=self.guardian_decider,
            ),
            lima_runner=self.lima_runner,
            worker_endpoints=endpoints,
            clock=lambda: FIXED_TIME,
        )
        eight = control_plane_eight.submit_many(
            self._request(request_id="request-batch-eight", idempotency_key="idem-batch-eight"),
            workers,
        )

        self.assertEqual(two["worker_count"], 2)
        self.assertTrue(all(result["status"] == "acknowledged" for result in two["results"]))
        self.assertEqual(eight["worker_count"], 8)
        self.assertTrue(all(result["status"] == "acknowledged" for result in eight["results"]))
        self.assertTrue(eight["runtime_authority_blocked"])
        self.assertFalse(eight["executable"])

    def test_restart_preserves_history_and_duplicate_is_rejected(self) -> None:
        control_plane = self._control_plane()
        first = control_plane.submit(self._request())
        self.assertEqual(first["status"], "acknowledged")
        self.store.close()

        reopened = SQLiteEvidenceStore(self.store_path, self.validator)
        self.addCleanup(reopened.close)
        self.store = reopened
        control_plane = self._control_plane(store=reopened)
        replay = control_plane.submit(self._request())

        self.assertEqual(replay["status"], "denied")
        self.assertIn("nonce_replay_denied", replay["reason_codes"])
        self.assertEqual(replay["evidence"][-1]["event_type"], "replay_rejected")
        self.assertEqual(len(self.endpoint.received_previews), 1)

    def test_repeated_action_with_fresh_request_identity_is_not_a_replay(self) -> None:
        control_plane = self._control_plane()
        first = control_plane.submit(self._request())
        second = control_plane.submit(
            self._request(
                request_id="request-safe-read-002",
                idempotency_key="idem-safe-read-002",
            )
        )

        self.assertEqual(first["status"], "acknowledged")
        self.assertEqual(second["status"], "acknowledged")
        self.assertEqual(len(self.endpoint.received_previews), 2)

    def test_evidence_failure_blocks_before_guardian_lima_and_arc(self) -> None:
        failing_path = Path(self.temporary.name) / "failing.db"
        failing_store = SQLiteEvidenceStore(
            failing_path,
            self.validator,
            fail_writes=True,
        )
        self.addCleanup(failing_store.close)

        with self.assertRaises(EvidenceWriteError):
            self._control_plane(store=failing_store).submit(
                self._request(request_id="request-evidence-failure")
            )

        self.assertEqual(self.guardian_decider.calls, [])
        self.assertEqual(self.lima_runner.calls, [])
        self.assertEqual(self.endpoint.received_previews, [])


if __name__ == "__main__":
    unittest.main()
