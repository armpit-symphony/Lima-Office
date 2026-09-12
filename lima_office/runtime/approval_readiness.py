"""Non-authorizing approval-profile projection for the attended lab."""

from __future__ import annotations

from typing import Any


PROFILE_A_ID = "attended_os_session_lab_only"
SEPARATION_PROFILE = "single_owner_low_risk_exception"


def profile_a_lab_state() -> dict[str, Any]:
    """Describe the selected lab profile without granting approval authority."""

    return {
        "profile_id": PROFILE_A_ID,
        "display_name": "Profile A - attended OS session",
        "status": "active_lab_only",
        "environment": "phase0_lab",
        "separation_profile": SEPARATION_PROFILE,
        "synthetic_data_only": True,
        "attended_session_required": True,
        "survives_restart": False,
        "named_owner_identity_configured": False,
        "mfa_configured": False,
        "customer_or_production_use_allowed": False,
        "positive_approval_enabled": False,
        "approval_result_issuance_enabled": False,
        "approval_token_issuance_enabled": False,
        "approval_binding_enabled": False,
        "token_verification_enabled": False,
        "replay_consumption_enabled": False,
        "worker_assignment_enabled": False,
        "arc_dispatch_enabled": False,
        "external_effects_enabled": False,
        "upgrade_required_before_customer_use": True,
    }
