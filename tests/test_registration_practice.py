"""Contract tests for the synthetic registration practice engine."""

from __future__ import annotations

import pytest

from lima_office.runtime.registration_practice import (
    FORM_FIELDS,
    RegistrationPracticeError,
    catalog,
    run_scenario,
    run_suite,
)


def test_catalog_is_fixed_synthetic_and_non_executable() -> None:
    result = catalog()

    assert result["data_classification"] == "synthetic_fixture_only"
    assert len(result["scenarios"]) == 5
    assert result["form_fields"] == list(FORM_FIELDS)
    assert result["submission_allowed"] is False
    assert result["browser_automation_allowed"] is False
    assert result["external_side_effects"] is False
    for scenario in result["scenarios"]:
        email = scenario["profile"].get("email")
        phone = scenario["profile"].get("phone")
        if isinstance(email, str) and "@" in email:
            assert email.endswith(".test")
        if phone is not None:
            assert phone.startswith("555-01")


@pytest.mark.parametrize(
    ("scenario_id", "issue_fields"),
    [
        ("complete-contact", []),
        ("missing-phone", ["phone"]),
        ("invalid-email", ["email"]),
        ("invalid-postal-code", ["postal_code"]),
        ("consent-not-granted", ["consent_to_contact"]),
    ],
)
def test_scenario_maps_exactly_and_flags_expected_gaps(
    scenario_id: str, issue_fields: list[str]
) -> None:
    result = run_scenario(scenario_id)

    assert result["passed"] is True
    assert result["score"] == 100
    assert [issue["field"] for issue in result["issues"]] == issue_fields
    assert result["submission_allowed"] is False
    assert result["browser_automation_allowed"] is False
    assert result["external_side_effects"] is False
    for field in issue_fields:
        assert result["prepared_fields"][field] == ""
    for field in set(FORM_FIELDS) - set(issue_fields):
        assert result["prepared_fields"][field] == result["synthetic_profile"][field]


def test_full_suite_passes_every_synthetic_scenario() -> None:
    result = run_suite()

    assert result["status"] == "passed"
    assert result["scenario_count"] == 5
    assert result["passed_count"] == 5
    assert result["failed_count"] == 0
    assert result["average_score"] == 100
    assert result["submission_allowed"] is False
    assert result["external_side_effects"] is False


@pytest.mark.parametrize("scenario_id", [None, "", "unknown", 7])
def test_unknown_or_malformed_scenario_fails_closed(scenario_id: object) -> None:
    with pytest.raises(RegistrationPracticeError):
        run_scenario(scenario_id)
