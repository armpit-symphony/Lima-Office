"""Contract tests for the lab.4 localhost registration test range."""

from __future__ import annotations

import pytest

from lima_office.runtime.registration_workflow import (
    FORM_FIELDS,
    RegistrationWorkflowError,
    catalog,
    run_scenario,
    run_suite,
)


def test_catalog_has_25_synthetic_records_and_three_local_layouts() -> None:
    result = catalog()

    assert result["data_classification"] == "synthetic_fixture_only"
    assert len(result["scenarios"]) == 25
    assert len(result["templates"]) == 3
    assert result["mock_target"] == "localhost_test_range"
    assert result["human_review_required"] is True
    assert result["external_submission_allowed"] is False
    assert result["browser_automation_allowed"] is False
    assert result["external_side_effects"] is False
    assert {item["template_id"] for item in result["scenarios"]} == {
        template["template_id"] for template in result["templates"]
    }
    for scenario in result["scenarios"]:
        email = scenario["profile"].get("email")
        phone = scenario["profile"].get("phone")
        if isinstance(email, str) and "@" in email:
            assert email.endswith(".test")
        if phone is not None:
            assert phone.startswith("555-01")


def test_every_template_has_exactly_the_bounded_fields() -> None:
    for template in catalog()["templates"]:
        fields = [item["field"] for item in template["fields"]]
        assert len(fields) == len(set(fields))
        assert set(fields) == set(FORM_FIELDS)


def test_complete_record_is_eligible_only_for_human_mock_review() -> None:
    scenario = next(
        item for item in catalog()["scenarios"] if not item["expected_issue_fields"]
    )
    result = run_scenario(scenario["scenario_id"])

    assert result["passed"] is True
    assert result["score"] == 100
    assert result["issues"] == []
    assert result["review_eligible"] is True
    assert result["mock_submission_performed"] is False
    assert result["external_submission_allowed"] is False
    assert result["external_side_effects"] is False


def test_incomplete_record_stays_blank_and_is_not_review_eligible() -> None:
    scenario = next(
        item for item in catalog()["scenarios"] if item["expected_issue_fields"]
    )
    result = run_scenario(scenario["scenario_id"])
    issue_fields = [item["field"] for item in result["issues"]]

    assert issue_fields == scenario["expected_issue_fields"]
    assert result["review_eligible"] is False
    for field in issue_fields:
        assert result["prepared_fields"][field] == ""


def test_full_lab4_suite_passes_all_25_records() -> None:
    result = run_suite()

    assert result["status"] == "passed"
    assert result["scenario_count"] == 25
    assert result["template_count"] == 3
    assert result["passed_count"] == 25
    assert result["failed_count"] == 0
    assert result["average_score"] == 100
    assert result["external_submission_allowed"] is False
    assert result["external_side_effects"] is False


@pytest.mark.parametrize("scenario_id", [None, "", "unknown", 7])
def test_unknown_or_malformed_scenario_fails_closed(scenario_id: object) -> None:
    with pytest.raises(RegistrationWorkflowError):
        run_scenario(scenario_id)
