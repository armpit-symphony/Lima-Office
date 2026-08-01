"""Execution grant issuance proofs for the Supervisor control plane.

These tests drive the real ``lima.runtime`` rather than a fake runner, because
``issue_execution_grant`` deliberately refuses anything that is not a genuine
``GovernedDecision``. Guardian Core is pinned through ``sys.modules`` so the
verdict never depends on whether a real Guardian happens to be importable.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any
import sys
import tempfile
import unittest

from lima_office.contracts import ContractLoader, ContractValidator
from lima_office.evidence.sqlite_store import SQLiteEvidenceStore
from lima_office.guardian.authority import GuardianCoreAuthority
from lima_office.supervisor.arc_worker import LocalArcWorkerPreviewEndpoint
from lima_office.supervisor.control_plane import (
    EXECUTABLE_CAPABILITIES,
    SupervisorControlPlane,
    load_execution_grant_issuer,
    load_lima_runner,
)
from lima_office.supervisor.worker_registry import WorkerRegistry

from test_arc_governed_control_plane import FakeGuardianDecider


# Anchored to the real clock. The Guardian decision reference validates its own
# expiry against datetime.now, not against an injected clock, so a hard-coded
# timestamp would age into "guardian_binding is expired" and deny every request.
FIXED_TIME = datetime.now(timezone.utc).replace(microsecond=0)
CAPABILITIES = ["document_read", "it_diagnostics_read_only", "draft_workspace"]


def _install_fake_guardian_core(action: str = "allow") -> list[ModuleType]:
    """Pin LIMA's Guardian Core verdict independently of the environment."""

    guardian_core_module = ModuleType("guardian_core")
    policy_module = ModuleType("guardian_core.policy")

    def decide_tool_use(
        tool_name: str,
        args: dict[str, Any] | None = None,
        *,
        room_execution_allowed: bool | None = None,
        is_operator: bool = False,
        is_privileged: bool = False,
        extra_policies: dict[str, dict[str, Any]] | None = None,
    ) -> Any:
        class _Decision:
            pass

        decision = _Decision()
        decision.tool_name = tool_name
        decision.action = action
        decision.high_risk = False
        decision.reason = "fake guardian core decision"
        decision.scope = "read"
        decision.resource = "test"
        decision.action_type = "test"
        return decision

    policy_module.decide_tool_use = decide_tool_use  # type: ignore[attr-defined]
    guardian_core_module.policy = policy_module  # type: ignore[attr-defined]
    return [guardian_core_module, policy_module]


class ExecutionGrantEnforcementTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)

        core, policy = _install_fake_guardian_core("allow")
        self._previous = {
            name: sys.modules.get(name)
            for name in ("guardian_core", "guardian_core.policy")
        }
        sys.modules["guardian_core"] = core
        sys.modules["guardian_core.policy"] = policy
        self.addCleanup(self._restore_guardian_core)

        self.validator = ContractValidator(ContractLoader().load())
        self.registry = WorkerRegistry()
        self.registry.register_mock_worker(
            worker_id="arc-worker-001",
            tenant_id="tenant-lab-001",
            role="arc-office-worker",
            capabilities=list(CAPABILITIES),
        )
        self.guardian_decider = FakeGuardianDecider()
        self.endpoint = LocalArcWorkerPreviewEndpoint(
            worker_id="arc-worker-001",
            tenant_id="tenant-lab-001",
            capabilities=set(CAPABILITIES),
            validator=self.validator,
        )
        self.store = SQLiteEvidenceStore(
            Path(self.temporary.name) / "control-plane.db",
            self.validator,
        )
        self.addCleanup(self.store.close)

        self.lima_runner = load_lima_runner()
        self.assertIsNotNone(
            self.lima_runner,
            "these tests require the pinned lima-runtime to be installed",
        )
        self.issuer = load_execution_grant_issuer()
        self.assertIsNotNone(
            self.issuer,
            "these tests require a lima-runtime providing issue_execution_grant",
        )

    def _restore_guardian_core(self) -> None:
        for name, module in self._previous.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module

    def _control_plane(
        self,
        *,
        execution_opt_in: bool = False,
        issuer: Any = "default",
    ) -> SupervisorControlPlane:
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
            worker_endpoints={"arc-worker-001": self.endpoint},
            execution_opt_in=execution_opt_in,
            execution_grant_issuer=self.issuer if issuer == "default" else issuer,
            clock=lambda: FIXED_TIME,
        )

    @staticmethod
    def _request(
        *,
        action: str = "safe_read",
        request_id: str = "request-grant-001",
        idempotency_key: str = "idem-grant-001",
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

    # ------------------------------------------------------------------
    # Baseline: real LIMA still produces a non-authorizing decision.
    # ------------------------------------------------------------------

    def test_real_lima_decision_is_reached_and_authorizes_nothing(self) -> None:
        result = self._control_plane().submit(self._request())

        self.assertEqual(result["status"], "acknowledged")
        self.assertEqual(result["lima"]["status"], "allowed_dry_run")
        self.assertEqual(result["lima"]["source_policy"], "guardian_core.policy")
        for field in ("executable", "execution_allowed", "side_effects_allowed"):
            self.assertIs(result[field], False)

    # ------------------------------------------------------------------
    # The opt-in gate.
    # ------------------------------------------------------------------

    def test_no_grant_is_issued_by_default(self) -> None:
        result = self._control_plane().submit(self._request())

        self.assertEqual(result["status"], "acknowledged")
        self.assertIsNone(result["execution_grant"])
        self.assertNotIn(
            "execution_grant_issued",
            [event["event_type"] for event in result["evidence"]],
        )

    def test_opt_in_issues_a_bound_single_use_grant(self) -> None:
        result = self._control_plane(execution_opt_in=True).submit(self._request())

        grant = result["execution_grant"]
        self.assertIsNotNone(grant, "operator opt-in should yield a grant")
        self.assertIs(grant["execution_allowed"], True)
        self.assertIs(grant["requires_operator_opt_in"], True)
        self.assertIs(grant["side_effects_allowed"], False)
        self.assertEqual(grant["granted_capability"], "document_read")
        self.assertEqual(grant["bound_tenant_id"], "tenant-lab-001")
        self.assertEqual(grant["bound_worker_id"], "arc-worker-001")
        self.assertEqual(grant["request_id"], "request-grant-001")
        self.assertEqual(grant["decision_id"], result["lima"]["decision_id"])
        self.assertIn(
            "execution_grant_issued",
            [event["event_type"] for event in result["evidence"]],
        )

    def test_grant_does_not_relax_the_decision_or_the_result_flags(self) -> None:
        result = self._control_plane(execution_opt_in=True).submit(self._request())

        self.assertIsNotNone(result["execution_grant"])
        for field in ("executable", "execution_allowed", "side_effects_allowed"):
            self.assertIs(result[field], False)
        for field in ("executable", "execution_allowed", "side_effects_allowed"):
            self.assertIs(result["lima"].get(field, False), False)

    def test_grant_is_absent_from_the_worker_assignment_preview(self) -> None:
        result = self._control_plane(execution_opt_in=True).submit(self._request())

        assignment = result["assignment"]
        self.assertIsNotNone(assignment)
        self.assertNotIn("execution_grant", assignment)
        self.assertIs(assignment["executable"], False)
        self.assertIs(assignment["execution_allowed"], False)
        self.assertIs(assignment["side_effects_allowed"], False)

    # ------------------------------------------------------------------
    # Capability narrowing.
    # ------------------------------------------------------------------

    def test_only_read_only_capabilities_are_grantable(self) -> None:
        self.assertEqual(EXECUTABLE_CAPABILITIES, frozenset({"document_read"}))

    def test_non_grantable_capability_yields_no_grant_even_with_opt_in(self) -> None:
        result = self._control_plane(execution_opt_in=True).submit(
            self._request(
                action="status",
                request_id="request-grant-002",
                idempotency_key="idem-grant-002",
            )
        )

        self.assertEqual(result["status"], "acknowledged")
        self.assertIsNone(result["execution_grant"])

    # ------------------------------------------------------------------
    # Fail-closed paths.
    # ------------------------------------------------------------------

    def test_missing_issuer_yields_no_grant(self) -> None:
        result = self._control_plane(execution_opt_in=True, issuer=None).submit(
            self._request()
        )

        self.assertEqual(result["status"], "acknowledged")
        self.assertIsNone(result["execution_grant"])

    def test_failing_issuer_denies_without_breaking_the_request(self) -> None:
        def broken_issuer(*args: object, **kwargs: object) -> object:
            raise RuntimeError(r"C:\private\lab\secret.toml leaked")

        result = self._control_plane(
            execution_opt_in=True,
            issuer=broken_issuer,
        ).submit(self._request())

        self.assertEqual(result["status"], "acknowledged")
        self.assertIsNone(result["execution_grant"])
        self.assertNotIn("secret.toml", repr(result))

    # ------------------------------------------------------------------
    # Single use.
    # ------------------------------------------------------------------

    def test_grant_identity_can_only_be_consumed_once(self) -> None:
        result = self._control_plane(execution_opt_in=True).submit(self._request())
        grant = result["execution_grant"]
        self.assertIsNotNone(grant)

        replay = self.store.reserve_execution_grant(
            tenant_id=grant["bound_tenant_id"],
            worker_id=grant["bound_worker_id"],
            grant_id=grant["grant_id"],
            nonce=grant["nonce"],
            request_id=grant["request_id"],
            expires_at=grant["expires_at"],
            created_at=FIXED_TIME.isoformat().replace("+00:00", "Z"),
        )
        self.assertFalse(replay, "a consumed grant identity must not reserve again")

    def test_distinct_requests_receive_distinct_grants(self) -> None:
        control_plane = self._control_plane(execution_opt_in=True)
        first = control_plane.submit(self._request())
        second = control_plane.submit(
            self._request(
                request_id="request-grant-003",
                idempotency_key="idem-grant-003",
            )
        )

        self.assertIsNotNone(first["execution_grant"])
        self.assertIsNotNone(second["execution_grant"])
        self.assertNotEqual(
            first["execution_grant"]["grant_id"],
            second["execution_grant"]["grant_id"],
        )
        self.assertNotEqual(
            first["execution_grant"]["nonce"],
            second["execution_grant"]["nonce"],
        )


if __name__ == "__main__":
    unittest.main()
