"""Guardian policy tests for the localhost-only mock form target."""

from lima_office.guardian.policy import GuardianPolicy


def _context(**overrides):
    context = {
        "tenant_id": "tenant-lab-001",
        "customer_context_id": "customer-context-main",
        "execution_mode": "mock_only",
        "external_effect": "none",
        "evidence_required": True,
        "evidence_artifact_ids": ["harness-event:before-review"],
        "synthetic_data_only": True,
        "operator_review_decision": "approved",
        "unresolved_issue_count": 0,
        "mock_target": "localhost_test_range",
    }
    context.update(overrides)
    return context


def test_complete_human_approved_local_mock_is_allowed_with_evidence() -> None:
    decision = GuardianPolicy().decide("mock_form_submission", _context())

    assert decision["decision"] == "allow_with_evidence"
    assert decision["approval_required"] is False


def test_mock_form_policy_fails_closed_on_every_boundary() -> None:
    cases = (
        {"synthetic_data_only": False},
        {"operator_review_decision": "rejected"},
        {"unresolved_issue_count": 1},
        {"mock_target": "https://example.test"},
        {"external_effect": "write"},
        {"evidence_artifact_ids": []},
    )
    for overrides in cases:
        decision = GuardianPolicy().decide(
            "mock_form_submission", _context(**overrides)
        )
        assert decision["decision"] == "deny"
