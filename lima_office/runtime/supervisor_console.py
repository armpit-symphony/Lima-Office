"""Safe projections for the attended LIMA Office Supervisor Console.

The console renders already-owned Supervisor and Arc state.  Its only live
model surface is the separately Guardian-gated, transient conversation service;
this projection cannot dispatch work or grant authority.
"""

from __future__ import annotations

from collections.abc import Mapping
import os
from pathlib import Path
import shutil
from typing import Any

from lima_office.runtime.approval_readiness import profile_a_lab_state


def _safe_nonnegative_int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return max(0, value)
    return 0


def _safe_text(value: Any, default: str, limit: int) -> str:
    return value[:limit] if isinstance(value, str) and value else default


def codex_subscription_readiness(
    *,
    codex_home: Path | None = None,
    codex_cli: str | None = None,
) -> dict[str, Any]:
    """Return non-secret readiness metadata for the local Codex session.

    Presence is intentionally reported separately from invocation authority.
    This check never opens ``auth.json`` and never invokes Codex.
    """

    profile_root = codex_home or Path(
        os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))
    )
    auth_file = profile_root / "auth.json"
    try:
        profile_detected = auth_file.is_file() and auth_file.stat().st_size > 2
    except OSError:
        profile_detected = False

    explicit_cli = (codex_cli or os.environ.get("LIMA_OFFICE_CODEX_CLI", "")).strip()
    resolved_cli = explicit_cli or shutil.which("codex") or ""
    if not resolved_cli:
        windows_candidates = (
            Path.home() / "AppData" / "Roaming" / "npm" / "codex.cmd",
            Path.home() / "AppData" / "Local" / "OpenAI" / "Codex" / "bin" / "codex.exe",
        )
        resolved_cli = next(
            (str(candidate) for candidate in windows_candidates if candidate.is_file()),
            "",
        )

    cli_detected = bool(resolved_cli)
    if profile_detected and cli_detected:
        status = "profile_detected"
        detail = (
            "Local ChatGPT/Codex sign-in and CLI were detected. "
            "An attended read-only turn still requires explicit confirmation, "
            "Guardian authorization, and evidence."
        )
    elif profile_detected:
        status = "cli_missing"
        detail = "A local ChatGPT/Codex profile was detected, but the Codex CLI was not found."
    elif cli_detected:
        status = "sign_in_needed"
        detail = "Codex CLI was detected, but no local ChatGPT/Codex sign-in profile was found."
    else:
        status = "setup_needed"
        detail = "Codex CLI and a local ChatGPT/Codex sign-in are required for the next slice."

    return {
        "provider": "openai_codex_subscription",
        "connection_method": "local_codex_cli",
        "status": status,
        "detail": detail,
        "auth_profile_detected": profile_detected,
        "cli_detected": cli_detected,
        "credentials_exposed": False,
        "live_invocation_enabled": False,
        "tools_enabled": False,
        "sandbox_required": "read_only",
        "ephemeral_session_required": True,
    }


def _safe_worker(worker: Any) -> dict[str, Any] | None:
    if not isinstance(worker, Mapping):
        return None
    projected: dict[str, Any] = {}
    for key in (
        "worker_id",
        "worker_role",
        "state",
        "eligible",
        "assignable",
        "authenticated",
        "health_status",
        "last_heartbeat_at",
    ):
        value = worker.get(key)
        if isinstance(value, (str, bool, int, float)) or value is None:
            projected[key] = value
    reason_codes = worker.get("reason_codes")
    if isinstance(reason_codes, list):
        projected["reason_codes"] = [
            str(code)[:120] for code in reason_codes[:12] if isinstance(code, str)
        ]
    return projected or None


def _safe_evidence_event(event: Any) -> dict[str, Any] | None:
    if not isinstance(event, Mapping):
        return None
    projected: dict[str, Any] = {}
    for key in ("event_id", "evidence_ref", "occurred_at", "created_at", "event_type"):
        value = event.get(key)
        if isinstance(value, str):
            projected[key] = value[:240]
    return projected or None


def _safe_proposal(proposal: Any) -> dict[str, Any] | None:
    if not isinstance(proposal, Mapping):
        return None
    projected: dict[str, Any] = {}
    for key in (
        "proposal_id", "revision", "state", "source_helper_result_id",
        "scenario_id", "task_class", "priority", "human_input_required",
        "owner_decision", "guardian_decision_id", "pre_action_evidence_ref",
        "post_action_evidence_ref", "approval_required_for_future_execution",
        "approval_token_issued", "arc_dispatch_allowed", "arc_dispatched",
        "model_called", "tools_used", "connector_accessed", "submission_allowed",
        "external_side_effects", "created_at", "updated_at",
    ):
        value = proposal.get(key)
        if isinstance(value, (str, bool, int)) or value is None:
            projected[key] = value
    for key in ("selected_step_ids", "issue_fields", "transition_reason_codes"):
        values = proposal.get(key)
        if isinstance(values, list):
            projected[key] = [value[:120] for value in values[:12] if isinstance(value, str)]
    return projected if isinstance(projected.get("proposal_id"), str) else None


def _safe_approval_preview(preview: Any) -> dict[str, Any] | None:
    if not isinstance(preview, Mapping):
        return None
    projected: dict[str, Any] = {}
    for key in (
        "approval_preview_id", "revision", "source_proposal_id",
        "source_proposal_revision", "source_proposal_state", "source_proposal_hash",
        "state", "review_outcome", "guardian_decision_id",
        "pre_action_evidence_ref", "post_action_evidence_ref",
        "synthetic_data_only", "free_form_content_allowed",
        "real_approval_request_created", "approval_result_created",
        "approval_token_issued", "approval_binding_created",
        "token_verification_performed", "replay_record_created",
        "assigned_worker_id", "arc_dispatch_allowed", "arc_dispatched",
        "model_called", "tools_used", "connector_accessed", "submission_allowed",
        "external_side_effects", "preview_expires_at", "created_at", "updated_at",
        "source_current", "expired_for_review", "review_available",
    ):
        value = preview.get(key)
        if isinstance(value, (str, bool, int)) or value is None:
            projected[key] = value
    reason_codes = preview.get("transition_reason_codes")
    projected["transition_reason_codes"] = [
        value[:120] for value in reason_codes[:4] if isinstance(value, str)
    ] if isinstance(reason_codes, list) else []
    scope = preview.get("preview_scope")
    if isinstance(scope, Mapping):
        projected["preview_scope"] = {
            "requested_action_class": _safe_text(scope.get("requested_action_class"), "unknown", 80),
            "external_effect": _safe_text(scope.get("external_effect"), "none", 40),
            "resource_refs": [value[:240] for value in scope.get("resource_refs", [])[:4] if isinstance(value, str)],
            "allowed_operations": [value[:120] for value in scope.get("allowed_operations", [])[:4] if isinstance(value, str)],
            "prohibited_operations": [value[:120] for value in scope.get("prohibited_operations", [])[:16] if isinstance(value, str)],
            "data_classification": _safe_text(scope.get("data_classification"), "synthetic_fixture_only", 80),
            "risk_tier": _safe_text(scope.get("risk_tier"), "low", 20),
            "scope_hash": _safe_text(scope.get("scope_hash"), "missing", 80),
            "max_uses": _safe_nonnegative_int(scope.get("max_uses")),
        }
    requirements = preview.get("approver_requirements")
    if isinstance(requirements, Mapping):
        projected["approver_requirements"] = {
            "approver_roles": [value[:80] for value in requirements.get("approver_roles", [])[:4] if isinstance(value, str)],
            "identity_binding_required": requirements.get("identity_binding_required") is True,
            "identity_binding_status": _safe_text(requirements.get("identity_binding_status"), "not_bound_in_preview", 80),
            "fresh_intent_required": requirements.get("fresh_intent_required") is True,
            "separation_of_duties_review_required": requirements.get("separation_of_duties_review_required") is True,
        }
    return projected if isinstance(projected.get("approval_preview_id"), str) else None


def build_supervisor_console_state(
    harness_state: Mapping[str, Any],
    build_info: Mapping[str, Any],
    *,
    codex_home: Path | None = None,
    codex_cli: str | None = None,
    conversation_state: Mapping[str, Any] | None = None,
    helper_state: Mapping[str, Any] | None = None,
    proposal_state: Mapping[str, Any] | None = None,
    approval_preview_state: Mapping[str, Any] | None = None,
    operator_session_state: Mapping[str, Any] | None = None,
    pending_approval_request_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a redacted, non-executing business-owner console projection."""

    office = harness_state.get("office_integration")
    office = office if isinstance(office, Mapping) else {}
    inventory = office.get("inventory")
    inventory = inventory if isinstance(inventory, Mapping) else None
    raw_workers = inventory.get("workers", []) if inventory else []
    workers = [
        projected
        for projected in (_safe_worker(worker) for worker in raw_workers)
        if projected is not None
    ]

    operator_ide = harness_state.get("operator_ide")
    operator_ide = operator_ide if isinstance(operator_ide, Mapping) else {}
    tasks = operator_ide.get("tasks")
    approvals = operator_ide.get("pending_approvals")
    task_count = len(tasks) if isinstance(tasks, list) else 0
    approval_count = len(approvals) if isinstance(approvals, list) else 0

    recent = harness_state.get("recent_evidence")
    recent = recent if isinstance(recent, list) else []
    evidence = [
        projected
        for projected in (_safe_evidence_event(event) for event in recent[-8:])
        if projected is not None
    ]

    training = harness_state.get("training_progress")
    training = training if isinstance(training, Mapping) else {}
    registration = harness_state.get("registration_practice")
    registration = registration if isinstance(registration, Mapping) else {}
    conversation = (
        conversation_state if isinstance(conversation_state, Mapping) else {}
    )
    helper = helper_state if isinstance(helper_state, Mapping) else {}
    task_proposals = proposal_state if isinstance(proposal_state, Mapping) else {}
    approval_previews = (
        approval_preview_state if isinstance(approval_preview_state, Mapping) else {}
    )
    operator_session = (
        operator_session_state if isinstance(operator_session_state, Mapping) else {}
    )
    pending_requests_state = (
        pending_approval_request_state
        if isinstance(pending_approval_request_state, Mapping) else {}
    )
    raw_binding = operator_session.get("binding")
    binding = None
    if isinstance(raw_binding, Mapping):
        binding = {
            key: raw_binding[key]
            for key in (
                "binding_id", "operator_id", "auth_method", "assurance_level",
                "status", "process_bound", "survives_process_restart", "pin_required",
                "mfa_verified", "production_identity_verified", "approval_authority",
                "pending_request_creation_allowed", "issued_at", "expires_at",
            )
            if isinstance(raw_binding.get(key), (str, bool))
        }
    active_binding_id = (
        binding.get("binding_id")
        if operator_session.get("active") is True and isinstance(binding, Mapping)
        else None
    )
    pending_requests = []
    for item in pending_requests_state.get("requests", []):
        if not isinstance(item, Mapping):
            continue
        request_id = item.get("approval_request_id")
        if not isinstance(request_id, str):
            continue
        scope = item.get("requested_scope")
        scope = scope if isinstance(scope, Mapping) else {}
        status = _safe_text(item.get("status"), "missing", 40)
        expired = item.get("expired_for_decision") is True
        original_requester = item.get("bound_requester_ref")
        pending_requests.append({
            "approval_request_id": request_id[:160],
            "source_approval_preview_id": _safe_text(
                item.get("source_approval_preview_id"), "missing", 160),
            "task_id": _safe_text(item.get("task_id"), "missing", 160),
            "action_class": _safe_text(item.get("action_class"), "missing", 80),
            "status": status,
            "approval_result": _safe_text(item.get("approval_result"), "missing", 40),
            "scope_hash": _safe_text(item.get("scope_hash"), "missing", 80),
            "record_hash": _safe_text(item.get("record_hash"), "missing", 80),
            "approval_result_id": (
                _safe_text(item.get("approval_result_id"), "missing", 160)
                if item.get("approval_result_created") is True else None
            ),
            "result_reason_code": (
                _safe_text(item.get("result_reason_code"), "missing", 80)
                if item.get("approval_result_created") is True else None
            ),
            "decision_kind": (
                _safe_text(item.get("decision_kind"), "missing", 80)
                if item.get("approval_result_created") is True else None
            ),
            "external_effect": _safe_text(scope.get("external_effect"), "none", 40),
            "allowed_operations": [
                value[:80] for value in scope.get("allowed_operations", [])[:4]
                if isinstance(value, str)
            ],
            "operator_session_binding_id": _safe_text(
                item.get("operator_session_binding_id"), "missing", 160),
            "approval_result_created": item.get("approval_result_created") is True,
            "approval_binding_created": item.get("approval_binding_created") is True,
            "token_verification_performed": item.get("token_verification_performed") is True,
            "replay_record_created": item.get("replay_record_created") is True,
            "assigned_worker_id": None,
            "arc_dispatch_allowed": item.get("arc_dispatch_allowed") is True,
            "arc_dispatched": item.get("arc_dispatched") is True,
            "external_side_effects": item.get("external_side_effects") is True,
            "expired_for_decision": expired,
            "can_deny": status == "pending_review" and not expired
                and isinstance(active_binding_id, str),
            "can_cancel": status == "pending_review" and not expired
                and isinstance(active_binding_id, str)
                and active_binding_id == original_requester,
            "can_record_expiry": status == "pending_review" and expired,
            "expires_at": _safe_text(item.get("expires_at"), "missing", 40),
            "created_at": _safe_text(item.get("created_at"), "missing", 40),
        })
    proposals = [
        projected
        for projected in (
            _safe_proposal(item) for item in task_proposals.get("proposals", [])
        )
        if projected is not None
    ]
    previews = [
        projected
        for projected in (
            _safe_approval_preview(item)
            for item in approval_previews.get("previews", [])
        )
        if projected is not None
    ]
    helper_scenarios = []
    for item in helper.get("scenarios", []):
        if not isinstance(item, Mapping):
            continue
        scenario_id = item.get("scenario_id")
        title = item.get("title")
        if isinstance(scenario_id, str) and isinstance(title, str):
            helper_scenarios.append(
                {"scenario_id": scenario_id[:64], "title": title[:120]}
            )
    raw_last_helper = helper.get("last_review")
    last_helper = None
    if isinstance(raw_last_helper, Mapping):
        last_helper = {
            key: raw_last_helper[key]
            for key in (
                "helper_result_id", "scenario_id", "status", "disposition",
                "finding_count", "guardian_decision_id", "evidence_ref",
                "completed_at",
            )
            if isinstance(raw_last_helper.get(key), (str, int))
            and not isinstance(raw_last_helper.get(key), bool)
        }
    model = codex_subscription_readiness(
        codex_home=codex_home,
        codex_cli=codex_cli,
    )
    model["live_invocation_enabled"] = conversation.get("enabled") is True

    return {
        "status": "ready" if office.get("connected") is True else "degraded",
        "product": "LIMA Office",
        "surface": "business_owner_supervisor_console",
        "maturity": "attended_localhost_lab_preview",
        "mode": harness_state.get("mode", "training"),
        "build": {
            "version": _safe_text(build_info.get("version"), "development", 64),
            "arc_commit": _safe_text(build_info.get("arc_commit"), "unknown", 40),
            "source_modified": bool(build_info.get("source_modified", True)),
        },
        "supervisor": {
            "connected": office.get("connected") is True,
            "guardian_required": True,
            "classification_authority": _safe_text(
                office.get("classification_authority"),
                "supervisor_server_derived",
                80,
            ),
            "automatic_refresh": False,
            "runtime_authority_blocked": True,
            "execution_allowed": False,
            "side_effects_allowed": False,
        },
        "model": model,
        "approval_profile": profile_a_lab_state(),
        "conversation": {
            "enabled": conversation.get("enabled") is True,
            "mode": _safe_text(
                conversation.get("mode"), "disabled", 64
            ),
            "persistence": _safe_text(
                conversation.get("persistence"), "none", 64
            ),
            "data_classes_allowed": [
                value
                for value in conversation.get("data_classes_allowed", [])
                if value in {"public", "internal"}
            ],
            "requires_confirmation": conversation.get("requires_confirmation")
            is True,
            "tools_enabled": False,
            "arc_dispatch_enabled": False,
            "external_side_effects": False,
            "last_turn": conversation.get("last_turn")
            if isinstance(conversation.get("last_turn"), Mapping)
            else None,
        },
        "helper": {
            "role": "office_operations_helper",
            "status": _safe_text(helper.get("status"), "unavailable", 64),
            "supervisor_side_only": True,
            "independent_worker": False,
            "may_dispatch_workers": False,
            "may_request_approval_token": False,
            "runtime_enabled": helper.get("runtime_enabled") is True,
            "review_type": "registration_sop_review",
            "requires_confirmation": True,
            "synthetic_data_only": True,
            "deterministic_review": True,
            "model_calls_enabled": False,
            "tools_enabled": False,
            "memory_enabled": False,
            "external_side_effects": False,
            "allowed_preview_work": [
                "sop_review",
                "task_decomposition",
                "missing_field_check",
                "draft_review",
                "arc_result_review",
            ],
            "scenarios": helper_scenarios,
            "last_review": last_helper,
        },
        "work": {
            "task_count": task_count,
            "pending_approval_count": approval_count,
            "dispatch_enabled": False,
            "external_submission_allowed": False,
            "proposal_runtime_enabled": task_proposals.get("runtime_enabled") is True,
            "proposal_count": len(proposals),
            "proposal_priorities": [
                value for value in task_proposals.get("allowed_priorities", [])
                if value in {"low", "normal"}
            ],
            "proposal_step_ids": [
                value for value in task_proposals.get("allowed_step_ids", [])
                if value in {
                    "review_synthetic_scenario", "resolve_human_input_fields",
                    "owner_review_prepared_form",
                }
            ],
            "proposals": proposals,
            "approval_tokens_enabled": False,
            "arc_dispatch_enabled": False,
        },
        "approval_previews": {
            "runtime_enabled": approval_previews.get("runtime_enabled") is True,
            "preview_only": True,
            "count": len(previews),
            "ready_count": sum(1 for item in previews if item.get("state") == "preview_ready"),
            "real_approval_requests_enabled": pending_requests_state.get("request_creation_enabled") is True,
            "approval_results_enabled": False,
            "non_authorizing_terminal_results_enabled": pending_requests_state.get(
                "non_authorizing_terminal_results_enabled"
            ) is True,
            "approval_tokens_enabled": False,
            "approval_bindings_enabled": False,
            "token_verification_enabled": False,
            "replay_records_enabled": False,
            "arc_dispatch_enabled": False,
            "items": previews,
        },
        "operator_session": {
            "runtime_enabled": operator_session.get("runtime_enabled") is True,
            "active": operator_session.get("active") is True,
            "process_bound": True,
            "survives_restart": False,
            "production_identity_verified": False,
            "approval_authority": False,
            "pin_required": False,
            "binding": binding,
        },
        "approval_requests": {
            "runtime_enabled": pending_requests_state.get("runtime_enabled") is True,
            "request_creation_enabled": pending_requests_state.get("request_creation_enabled") is True,
            "decision_runtime_enabled": pending_requests_state.get("decision_runtime_enabled") is True,
            "count": len(pending_requests),
            "pending_count": sum(1 for item in pending_requests if item["status"] == "pending_review"),
            "approval_results_enabled": False,
            "non_authorizing_terminal_results_enabled": pending_requests_state.get(
                "non_authorizing_terminal_results_enabled"
            ) is True,
            "terminal_non_authorizing_results": ["denied", "cancelled", "expired"],
            "positive_approval_enabled": False,
            "approval_tokens_enabled": False,
            "approval_bindings_enabled": False,
            "token_verification_enabled": False,
            "replay_records_enabled": False,
            "arc_dispatch_enabled": False,
            "items": pending_requests,
        },
        "workers": {
            "inventory_refreshed": inventory is not None,
            "count": len(workers),
            "items": workers,
            "automatic_refresh": False,
            "registered_worker_limit": 8,
        },
        "training": {
            "attempts": _safe_nonnegative_int(training.get("attempts")),
            "open_gaps": _safe_nonnegative_int(training.get("open_gaps")),
            "registration_attempts": _safe_nonnegative_int(
                registration.get("attempt_count")
            ),
            "registration_reviews": _safe_nonnegative_int(
                registration.get("review_count")
            ),
            "synthetic_data_only": True,
        },
        "evidence": {
            "recent_count": len(evidence),
            "items": evidence,
            "raw_payloads_included": False,
        },
        "blocked_capabilities": [
            "worker_dispatch",
            "external_send",
            "external_form_submission",
            "customer_record_update",
            "unrestricted_browser",
            "unrestricted_filesystem",
            "unrestricted_network",
            "production_remediation",
        ],
    }
