"""Cross-contract invariant checks for Phase 1A mock runtime flows."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from lima_office.runtime.errors import CrossContractInvariantError, EvidenceRequiredError, PolicyDenyError


DEFAULT_REFERENCE_TIME = "2026-05-20T00:01:00Z"
MAX_GUARDIAN_DECISION_AGE_SECONDS = 300

RUNNING_STATUSES = {"approved_to_run", "in_progress", "completed", "completed_mock", "evidence_recorded"}
DENIED_POLICY_RESULTS = {"deny", "block_mvp", "quarantine_subject"}
TAINTED_STATUSES = {"untrusted", "suspected", "confirmed"}
PRIVILEGED_ACTION_CLASSES = {
    "external_message_send",
    "file_delete",
    "file_overwrite",
    "customer_record_update",
    "software_install_update",
    "remediation",
    "sensitive_data_access",
    "production_server_touch",
    "regulated_system_use",
}
BLOCKED_TOOL_OPERATIONS = {
    "send_external_message",
    "live_connector_write",
    "run_remediation",
    "install_update_software",
    "touch_production_server",
    "unrestricted_browser",
    "unrestricted_filesystem",
    "unrestricted_network",
}
BLOCKED_MVP_APPROVAL_ACTIONS = {
    "external_message_send",
    "external_send",
    "connector_access",
    "live_connector_access",
    "software_install_update",
    "remediation",
    "lima_it_remediation",
    "production_server_touch",
    "regulated_system_use",
}


def assert_guardian_decision_authorizes_task(
    task: dict[str, Any],
    guardian_decision: dict[str, Any],
    *,
    reference_time: str | None = DEFAULT_REFERENCE_TIME,
) -> None:
    """Require a fresh allow decision bound to the same tenant/task."""

    decision = guardian_decision.get("decision")
    if decision not in {"allow", "allow_with_evidence"}:
        raise PolicyDenyError(guardian_decision.get("denial_reason") or "Guardian decision does not authorize task")
    _assert_same_field(task, guardian_decision, "tenant_id", "Guardian decision tenant mismatch")
    _assert_same_field(task, guardian_decision, "customer_context_id", "Guardian decision customer context mismatch")
    if guardian_decision.get("decision_id") != task.get("guardian_decision_id"):
        raise PolicyDenyError("Guardian decision is not bound to task guardian_decision_id")
    subject = guardian_decision.get("subject")
    if isinstance(subject, dict) and subject.get("subject_type") == "task":
        if subject.get("subject_id") != task.get("task_id"):
            raise PolicyDenyError("Guardian decision subject is not bound to task")
    if guardian_decision.get("evidence_required") is not True or not guardian_decision.get("evidence_artifact_ids"):
        raise EvidenceRequiredError("Guardian decision must require evidence and include evidence refs")
    prompt_injection = guardian_decision.get("prompt_injection")
    if isinstance(prompt_injection, dict) and prompt_injection.get("injection_suspected"):
        raise PolicyDenyError("tainted Guardian decision cannot authorize task")
    _assert_guardian_decision_fresh(guardian_decision, reference_time=reference_time)


def assert_token_verification_authorizes_task(
    task: dict[str, Any],
    token_verification: dict[str, Any] | None,
    approval_binding: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Require a valid token verification when the task asks for approval."""

    if not task.get("approval_required"):
        return None
    if token_verification is None:
        raise PolicyDenyError("approval-required task requires token verification metadata")
    _assert_same_field(task, token_verification, "tenant_id", "token verification tenant mismatch")
    _assert_same_field(task, token_verification, "customer_context_id", "token verification customer context mismatch")
    _assert_matches(task, token_verification, "task_id", "token verification task mismatch")
    _assert_matches(task, token_verification, "approval_token_id", "token verification approval token mismatch")
    _assert_matches(task, token_verification, "approval_request_id", "token verification approval request mismatch")
    _assert_matches(task, token_verification, "guardian_decision_id", "token verification Guardian decision mismatch")
    _assert_matches(task, token_verification, "token_verification_id", "token verification ID mismatch")
    if token_verification.get("scope_match_result") != "match":
        raise PolicyDenyError("token verification scope mismatch")
    if token_verification.get("verification_result") != "valid":
        raise PolicyDenyError(token_verification.get("denial_reason") or "token verification failed closed")
    if token_verification.get("token_status_observed") != "active":
        raise PolicyDenyError("approval token is not active")
    if token_verification.get("can_proceed") is not True or token_verification.get("fail_closed") is not False:
        raise PolicyDenyError("token verification does not permit proceeding")
    if approval_binding is not None:
        assert_approval_binding_authorizes_action(
            approval_binding,
            {
                "tenant_id": task.get("tenant_id"),
                "customer_context_id": task.get("customer_context_id"),
                "task_id": task.get("task_id"),
                "worker_id": task.get("assigned_worker_id"),
                "guardian_decision_id": task.get("guardian_decision_id"),
                "approval_request_id": task.get("approval_request_id"),
                "approval_result_id": task.get("approval_result_id"),
                "approval_token_id": task.get("approval_token_id"),
                "token_verification_id": task.get("token_verification_id"),
                "evidence_required": True,
                "evidence_refs": task.get("evidence_artifact_ids"),
            },
            reference_time=None,
            consume_nonce=False,
        )
    return token_verification


def assert_approval_binding_authorizes_action(
    approval_binding: dict[str, Any],
    requested_action: dict[str, Any],
    *,
    reference_time: str | None = DEFAULT_REFERENCE_TIME,
    consumed_nonces: set[str] | None = None,
    consume_nonce: bool = False,
) -> dict[str, Any]:
    """Require one exact, fresh, non-replayed binding for an approval-gated mock action."""

    if approval_binding.get("contract_name") != "approval.binding":
        raise PolicyDenyError("approval binding record is required")
    if approval_binding.get("status") != "bound":
        raise PolicyDenyError("approval binding is not active")
    if approval_binding.get("verification_result") != "valid":
        raise PolicyDenyError("approval binding verification is not valid")
    if approval_binding.get("token_use_policy") != "one_time":
        raise PolicyDenyError("MVP approval binding requires one-time token use")
    if approval_binding.get("blocked_mvp_action") is True:
        raise PolicyDenyError("blocked-MVP approval binding cannot authorize action")
    if approval_binding.get("action_type") in BLOCKED_MVP_APPROVAL_ACTIONS:
        raise PolicyDenyError("approval binding action type is blocked in MVP")
    if approval_binding.get("approval_token_id") is None or approval_binding.get("token_verification_id") is None:
        raise PolicyDenyError("approval binding requires token and verification refs")
    if approval_binding.get("consumed_at") is not None:
        raise PolicyDenyError("approval binding has already been consumed")
    if approval_binding.get("revoked_at") is not None:
        raise PolicyDenyError("approval binding has been revoked")
    if approval_binding.get("separation_check_result") != "pass":
        raise PolicyDenyError("approval binding lacks approver separation")
    if approval_binding.get("requester_ref") == approval_binding.get("approver_ref"):
        raise PolicyDenyError("approval binding requester and approver must be separated")
    if not approval_binding.get("identity_assurance_refs"):
        raise PolicyDenyError("approval binding lacks identity assurance refs")
    if approval_binding.get("input_taint_status") in TAINTED_STATUSES or approval_binding.get("taint_ref_ids"):
        raise PolicyDenyError("tainted approval chain cannot authorize privileged action")
    if approval_binding.get("evidence_required") is not True or not approval_binding.get("evidence_refs"):
        raise EvidenceRequiredError("approval binding requires evidence refs")

    _assert_binding_times_fresh(approval_binding, requested_action, reference_time=reference_time)
    _assert_binding_matches_action(approval_binding, requested_action)
    _assert_binding_scope_allows_action(approval_binding, requested_action)
    _assert_binding_evidence_present(approval_binding, requested_action)

    nonce_ref = approval_binding.get("nonce_ref")
    if not isinstance(nonce_ref, str) or not nonce_ref:
        raise PolicyDenyError("approval binding requires a nonce ref")
    if consumed_nonces is not None:
        if nonce_ref in consumed_nonces:
            raise PolicyDenyError("approval binding nonce has already been consumed")
        if consume_nonce:
            consumed_nonces.add(nonce_ref)
    return approval_binding


def assert_task_completion_allowed(
    task: dict[str, Any],
    *,
    guardian_decision: dict[str, Any] | None,
    token_verification: dict[str, Any] | None,
    evidence_artifact_ids: list[str] | None,
    reference_time: str | None = DEFAULT_REFERENCE_TIME,
) -> None:
    """Block terminal success when Guardian, approval, or evidence links are missing."""

    if guardian_decision is None:
        raise PolicyDenyError("Guardian decision is required before task completion")
    assert_guardian_decision_authorizes_task(task, guardian_decision, reference_time=reference_time)
    assert_token_verification_authorizes_task(task, token_verification)
    if task.get("status") in {"blocked", "denied", "failed", "blocked_evidence_unavailable", "cancelled", "timed_out"}:
        raise CrossContractInvariantError("blocked or failed task cannot complete successfully")
    if not evidence_artifact_ids:
        raise EvidenceRequiredError("task completion requires evidence artifact refs")


def assert_tool_invocation_consistent(
    tool_invocation: dict[str, Any],
    *,
    task: dict[str, Any] | None = None,
    worker: Any | None = None,
    approval_result: dict[str, Any] | None = None,
    approval_binding: dict[str, Any] | None = None,
) -> None:
    """Validate a tool invocation record against task, worker, taint, and approval state."""

    if task is not None:
        _assert_same_field(task, tool_invocation, "tenant_id", "tool invocation tenant mismatch")
        _assert_same_field(task, tool_invocation, "customer_context_id", "tool invocation customer context mismatch")
        _assert_matches(task, tool_invocation, "task_id", "tool invocation task mismatch")
    if worker is not None:
        if tool_invocation.get("tenant_id") != getattr(worker, "tenant_id", None):
            raise CrossContractInvariantError("tool invocation worker tenant mismatch")
        actor = tool_invocation.get("actor")
        if isinstance(actor, dict) and actor.get("actor_type") == "worker" and actor.get("actor_id") != worker.worker_id:
            raise CrossContractInvariantError("tool invocation worker identity mismatch")
    if approval_result is not None and _approval_result_blocks_runtime(approval_result):
        if tool_invocation.get("status") in RUNNING_STATUSES or tool_invocation.get("approval_token_id"):
            raise PolicyDenyError("blocked-MVP approval result cannot authorize tool invocation")
    if approval_binding is not None:
        assert_approval_binding_authorizes_action(
            approval_binding,
            _requested_action_from_tool(tool_invocation, task=task, worker=worker),
            reference_time=None,
            consume_nonce=False,
        )
    tainted = tool_invocation.get("input_taint_status") in TAINTED_STATUSES or bool(tool_invocation.get("taint_ref_ids"))
    requested_tool = tool_invocation.get("requested_tool") if isinstance(tool_invocation.get("requested_tool"), dict) else {}
    side_effect_class = tool_invocation.get("side_effect_class")
    privileged_tool = (
        requested_tool.get("tool_type") in {"connector", "network", "browser", "shell", "local_app", "lima_it"}
        or side_effect_class in {"approval_required_write", "blocked_mvp"}
        or bool(set(_scope_operations(tool_invocation)) & BLOCKED_TOOL_OPERATIONS)
    )
    if tainted and privileged_tool and tool_invocation.get("policy_result") not in DENIED_POLICY_RESULTS:
        raise PolicyDenyError("tainted input cannot authorize privileged tool invocation")
    if tool_invocation.get("policy_result") in DENIED_POLICY_RESULTS and tool_invocation.get("status") in RUNNING_STATUSES:
        raise PolicyDenyError("denied Guardian policy result cannot run tool invocation")


def assert_worker_can_receive_task(worker: Any, task: dict[str, Any]) -> None:
    """Require worker tenant, state, and capability compatibility for a task."""

    if getattr(worker, "tenant_id", None) != task.get("tenant_id"):
        raise CrossContractInvariantError("worker tenant mismatch")
    if not worker.can_accept_task():
        raise CrossContractInvariantError(f"worker {worker.worker_id} cannot accept tasks while {worker.state}")
    heartbeat = getattr(worker, "heartbeat", None)
    if isinstance(heartbeat, dict):
        heartbeat_age = heartbeat.get("heartbeat_age_seconds")
        if isinstance(heartbeat_age, int) and heartbeat_age > 180:
            raise CrossContractInvariantError("worker heartbeat is stale")
    required_tool_packs = set(task.get("required_tool_packs", []))
    worker_capabilities = set(getattr(worker, "capabilities", ()))
    missing = sorted(required_tool_packs - worker_capabilities)
    if missing:
        raise CrossContractInvariantError(f"worker lacks required tool packs: {', '.join(missing)}")


def assert_memory_access_consistent(memory_access: dict[str, Any], *, task: dict[str, Any] | None = None) -> None:
    """Validate memory access tenant and taint invariants."""

    if task is not None:
        _assert_same_field(task, memory_access, "tenant_id", "memory access tenant mismatch")
        _assert_same_field(task, memory_access, "customer_context_id", "memory access customer context mismatch")
        _assert_matches(task, memory_access, "task_id", "memory access task mismatch")
    if memory_access.get("tenant_match_required") is not True:
        raise CrossContractInvariantError("memory access must require tenant match")
    if memory_access.get("cross_tenant_access") is not False:
        raise CrossContractInvariantError("cross-tenant memory access is blocked")
    if memory_access.get("tenant_namespace") != memory_access.get("tenant_id"):
        raise CrossContractInvariantError("memory access tenant namespace mismatch")
    tainted = memory_access.get("prompt_injection_scan_status") in {"suspected", "blocked"} or bool(
        memory_access.get("taint_ref_ids")
    )
    durable_write = memory_access.get("access_type") == "write_summary" or memory_access.get("operation") == "write_summary"
    if tainted and durable_write and memory_access.get("policy_result") not in DENIED_POLICY_RESULTS:
        raise PolicyDenyError("tainted input cannot authorize durable memory write")
    if memory_access.get("status") == "completed" and memory_access.get("policy_result") not in {"allow", "allow_with_evidence"}:
        raise PolicyDenyError("denied memory access cannot complete")


def assert_lima_it_handoff_consistent(
    handoff: dict[str, Any],
    *,
    task: dict[str, Any] | None = None,
) -> None:
    """Keep LIMA IT remediation non-executing in Phase 1A."""

    if task is not None:
        _assert_same_field(task, handoff, "tenant_id", "LIMA IT handoff tenant mismatch")
        _assert_same_field(task, handoff, "customer_context_id", "LIMA IT handoff customer context mismatch")
        if handoff.get("task_id") is not None:
            _assert_matches(task, handoff, "task_id", "LIMA IT handoff task mismatch")
    remediation_scope = handoff.get("remediation_scope") if isinstance(handoff.get("remediation_scope"), dict) else {}
    remediation_requested = handoff.get("handoff_type") == "remediation_request" or remediation_scope.get("requested")
    if handoff.get("remediation_execution_authorized", False) is not False or handoff.get("remediation_authorized") is not False:
        raise PolicyDenyError("LIMA IT remediation execution is blocked in Phase 1A")
    if remediation_requested:
        if handoff.get("status") not in {"awaiting_approval", "remediation_approval_required", "blocked", "denied", "cancelled"}:
            raise PolicyDenyError("LIMA IT remediation request must remain blocked or approval-gated")
        if handoff.get("approval_token_id") is not None:
            raise PolicyDenyError("LIMA IT remediation cannot carry an approval token in MVP")
    else:
        if handoff.get("read_only_diagnostic") is not True:
            raise PolicyDenyError("non-remediation LIMA IT handoff must be read-only diagnostic metadata")
        if remediation_scope.get("production_system_touch") != "none":
            raise PolicyDenyError("read-only LIMA IT diagnostic cannot touch production systems")


def assert_helper_scope_allows_task(helper_scope: dict[str, Any], task: dict[str, Any]) -> None:
    """Require supervisor-side helper scopes to stay within declared role/capability."""

    _assert_same_field(task, helper_scope, "tenant_id", "helper scope tenant mismatch")
    _assert_same_field(task, helper_scope, "customer_context_id", "helper scope customer context mismatch")
    if helper_scope.get("status") != "active":
        raise PolicyDenyError("helper scope is not active")
    if helper_scope.get("supervisor_side_only") is not True or helper_scope.get("independent_worker") is not False:
        raise CrossContractInvariantError("helper scope must remain supervisor-side only")
    if task.get("task_class") not in set(helper_scope.get("allowed_task_classes", [])):
        raise PolicyDenyError("helper scope does not allow task class")
    task_packs = set(task.get("required_tool_packs", []))
    allowed_packs = set(helper_scope.get("allowed_tool_packs", []))
    if not task_packs <= allowed_packs:
        raise PolicyDenyError("helper scope does not allow required tool packs")
    allowed_classes = set(helper_scope.get("data_classifications_allowed", []))
    if task.get("data_classification") not in allowed_classes:
        raise PolicyDenyError("helper scope does not allow data classification")
    blocked_capabilities = set(helper_scope.get("blocked_capabilities", []))
    allowed_actions = set((task.get("task_scope") or {}).get("allowed_actions", []))
    if allowed_actions & blocked_capabilities:
        raise PolicyDenyError("helper scope would exceed blocked capabilities")


def assert_evidence_failure_state_consistent(evidence_failure: dict[str, Any]) -> None:
    """Ensure evidence failure records do not silently report success."""

    if evidence_failure.get("failure_stage") == "pre_action":
        if evidence_failure.get("pre_action_blocked") is not True or evidence_failure.get("action_blocked") is not True:
            raise EvidenceRequiredError("pre-action evidence failure must block action")
    if evidence_failure.get("failure_stage") == "post_action":
        if evidence_failure.get("post_action_degraded") is not True:
            raise CrossContractInvariantError("post-action evidence failure must produce degraded state")


def _assert_guardian_decision_fresh(
    guardian_decision: dict[str, Any],
    *,
    reference_time: str | None,
) -> None:
    if reference_time is None:
        return
    reference = _parse_datetime(reference_time)
    expires_at = guardian_decision.get("expires_at")
    if not isinstance(expires_at, str):
        raise PolicyDenyError("Guardian decision without expiry cannot authorize action")
    if _parse_datetime(expires_at) <= reference:
        raise PolicyDenyError("expired Guardian decision cannot authorize action")
    created_at = guardian_decision.get("created_at")
    if isinstance(created_at, str):
        age_seconds = (reference - _parse_datetime(created_at)).total_seconds()
        if age_seconds > MAX_GUARDIAN_DECISION_AGE_SECONDS:
            raise PolicyDenyError("stale Guardian decision cannot authorize action")


def _assert_binding_times_fresh(
    approval_binding: dict[str, Any],
    requested_action: dict[str, Any],
    *,
    reference_time: str | None,
) -> None:
    if reference_time is not None:
        reference = _parse_datetime(reference_time)
        expires_at = approval_binding.get("expires_at")
        if not isinstance(expires_at, str):
            raise PolicyDenyError("approval binding without expiry cannot authorize action")
        if _parse_datetime(expires_at) <= reference:
            raise PolicyDenyError("expired approval binding cannot authorize action")

    checked_at = approval_binding.get("checked_at")
    expires_at = approval_binding.get("expires_at")
    if isinstance(checked_at, str) and isinstance(expires_at, str):
        if _parse_datetime(checked_at) > _parse_datetime(expires_at):
            raise PolicyDenyError("approval binding was checked after expiry")

    guardian_decision = requested_action.get("guardian_decision")
    if isinstance(guardian_decision, dict):
        _assert_guardian_decision_fresh(guardian_decision, reference_time=reference_time)


def _assert_binding_matches_action(approval_binding: dict[str, Any], requested_action: dict[str, Any]) -> None:
    fields = (
        "tenant_id",
        "customer_context_id",
        "task_id",
        "tool_invocation_id",
        "worker_id",
        "guardian_decision_id",
        "approval_request_id",
        "approval_result_id",
        "approval_token_id",
        "token_verification_id",
        "binding_id",
        "approval_chain_id",
        "policy_version",
        "policy_snapshot_hash",
        "approved_scope_hash",
    )
    for field in fields:
        value = requested_action.get(field)
        if value is not None and approval_binding.get(field) != value:
            raise PolicyDenyError(f"approval binding {field} mismatch")
    action_type = requested_action.get("action_type")
    if action_type in BLOCKED_MVP_APPROVAL_ACTIONS:
        raise PolicyDenyError("requested action is blocked in MVP")
    if action_type is not None and approval_binding.get("action_type") != action_type:
        raise PolicyDenyError("approval binding action_type mismatch")


def _assert_binding_scope_allows_action(approval_binding: dict[str, Any], requested_action: dict[str, Any]) -> None:
    requested_scope = requested_action.get("tool_scope")
    if requested_scope is None:
        return
    if not isinstance(requested_scope, dict):
        raise PolicyDenyError("requested tool scope must be an object")
    binding_scope = approval_binding.get("tool_scope")
    if not isinstance(binding_scope, dict):
        raise PolicyDenyError("approval binding has no tool scope")
    bound_resources = set(binding_scope.get("resource_refs", []))
    requested_resources = set(requested_scope.get("resource_refs", []))
    if not requested_resources or not requested_resources <= bound_resources:
        raise PolicyDenyError("approval binding resource scope mismatch")
    bound_allowed = set(binding_scope.get("allowed_operations", []))
    requested_allowed = set(requested_scope.get("allowed_operations", []))
    if not requested_allowed or not requested_allowed <= bound_allowed:
        raise PolicyDenyError("approval binding operation scope mismatch")
    bound_prohibited = set(binding_scope.get("prohibited_operations", []))
    if requested_allowed & bound_prohibited:
        raise PolicyDenyError("approval binding requested a prohibited operation")
    if requested_allowed & BLOCKED_TOOL_OPERATIONS:
        raise PolicyDenyError("approval binding cannot authorize blocked tool operation")


def _assert_binding_evidence_present(approval_binding: dict[str, Any], requested_action: dict[str, Any]) -> None:
    if requested_action.get("evidence_required") is False:
        raise EvidenceRequiredError("approval-bound action must require evidence")
    requested_refs = requested_action.get("evidence_refs")
    if requested_refs is not None and not requested_refs:
        raise EvidenceRequiredError("approval-bound action requires evidence refs")
    binding_refs = set(approval_binding.get("evidence_refs", []))
    if requested_refs is not None and not set(requested_refs) <= binding_refs:
        raise EvidenceRequiredError("requested evidence refs are not bound to approval")


def _requested_action_from_tool(
    tool_invocation: dict[str, Any],
    *,
    task: dict[str, Any] | None,
    worker: Any | None,
) -> dict[str, Any]:
    return {
        "tenant_id": tool_invocation.get("tenant_id"),
        "customer_context_id": tool_invocation.get("customer_context_id"),
        "task_id": tool_invocation.get("task_id"),
        "tool_invocation_id": tool_invocation.get("tool_invocation_id"),
        "worker_id": getattr(worker, "worker_id", None) if worker is not None else tool_invocation.get("bound_worker_id"),
        "guardian_decision_id": tool_invocation.get("guardian_decision_id"),
        "approval_chain_id": tool_invocation.get("approval_chain_id"),
        "binding_id": tool_invocation.get("binding_id"),
        "approval_result_id": tool_invocation.get("approval_result_id"),
        "approval_token_id": tool_invocation.get("approval_token_id"),
        "token_verification_id": tool_invocation.get("token_verification_id"),
        "policy_version": tool_invocation.get("policy_version"),
        "action_type": tool_invocation.get("bound_action_type"),
        "tool_scope": tool_invocation.get("tool_scope"),
        "evidence_required": tool_invocation.get("evidence_required"),
        "evidence_refs": tool_invocation.get("evidence_artifact_ids"),
        "assigned_worker_id": task.get("assigned_worker_id") if task is not None else None,
    }


def _approval_result_blocks_runtime(approval_result: dict[str, Any]) -> bool:
    return (
        approval_result.get("blocked_mvp_action") is True
        or approval_result.get("result") != "approved"
        or approval_result.get("result_reason_code") == "blocked_mvp"
    )


def _scope_operations(tool_invocation: dict[str, Any]) -> list[str]:
    tool_scope = tool_invocation.get("tool_scope")
    if not isinstance(tool_scope, dict):
        return []
    return list(tool_scope.get("allowed_operations", [])) + list(tool_scope.get("prohibited_operations", []))


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _assert_same_field(left: dict[str, Any], right: dict[str, Any], field: str, message: str) -> None:
    if left.get(field) != right.get(field):
        raise CrossContractInvariantError(message)


def _assert_matches(left: dict[str, Any], right: dict[str, Any], field: str, message: str) -> None:
    if left.get(field) != right.get(field):
        raise PolicyDenyError(message)
