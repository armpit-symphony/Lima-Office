"""Deterministic, synthetic-only registration practice for the Arc lab UI."""

from __future__ import annotations

from copy import deepcopy
import re
from typing import Any, Mapping


FORM_FIELDS = (
    "full_name",
    "email",
    "phone",
    "address_line1",
    "city",
    "state",
    "postal_code",
    "preferred_contact",
    "consent_to_contact",
)

NEEDS_HUMAN_INPUT = "NEEDS_HUMAN_INPUT"

_SCENARIOS: tuple[dict[str, Any], ...] = (
    {
        "scenario_id": "complete-contact",
        "title": "Complete fictional contact",
        "objective": "Copy every supplied value and stop for review.",
        "profile": {
            "full_name": "Jordan Example",
            "email": "jordan.example@example.test",
            "phone": "555-0101",
            "address_line1": "101 Demo Lane",
            "city": "Sampletown",
            "state": "NY",
            "postal_code": "10001",
            "preferred_contact": "email",
            "consent_to_contact": "yes",
        },
        "expected_issue_fields": (),
    },
    {
        "scenario_id": "missing-phone",
        "title": "Missing fictional phone",
        "objective": "Leave the phone blank and request human input.",
        "profile": {
            "full_name": "Avery Sample",
            "email": "avery.sample@example.test",
            "phone": None,
            "address_line1": "202 Practice Road",
            "city": "Mocksville",
            "state": "PA",
            "postal_code": "19019",
            "preferred_contact": "email",
            "consent_to_contact": "yes",
        },
        "expected_issue_fields": ("phone",),
    },
    {
        "scenario_id": "invalid-email",
        "title": "Invalid fictional email",
        "objective": "Reject an invalid email rather than repairing or inventing one.",
        "profile": {
            "full_name": "Casey Fixture",
            "email": "casey.fixture.example.test",
            "phone": "555-0102",
            "address_line1": "303 Sandbox Street",
            "city": "Test Harbor",
            "state": "MA",
            "postal_code": "02108",
            "preferred_contact": "phone",
            "consent_to_contact": "yes",
        },
        "expected_issue_fields": ("email",),
    },
    {
        "scenario_id": "invalid-postal-code",
        "title": "Invalid fictional postal code",
        "objective": "Flag invalid postal data and leave the form field blank.",
        "profile": {
            "full_name": "Morgan Mock",
            "email": "morgan.mock@example.test",
            "phone": "555-0103",
            "address_line1": "404 Example Avenue",
            "city": "Fixture City",
            "state": "OH",
            "postal_code": "44A01",
            "preferred_contact": "email",
            "consent_to_contact": "yes",
        },
        "expected_issue_fields": ("postal_code",),
    },
    {
        "scenario_id": "consent-not-granted",
        "title": "Contact consent not granted",
        "objective": "Preserve the supplied refusal and stop before any contact or submit.",
        "profile": {
            "full_name": "Riley Training",
            "email": "riley.training@example.test",
            "phone": "555-0104",
            "address_line1": "505 Simulation Court",
            "city": "Practice Point",
            "state": "VA",
            "postal_code": "23219",
            "preferred_contact": "phone",
            "consent_to_contact": "no",
        },
        "expected_issue_fields": ("consent_to_contact",),
    },
)

_EMAIL = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.test$")
_PHONE = re.compile(r"^555-01\d{2}$")
_STATE = re.compile(r"^[A-Z]{2}$")
_POSTAL_CODE = re.compile(r"^\d{5}$")


class RegistrationPracticeError(ValueError):
    """Raised when a practice request leaves the fixed lab contract."""


def catalog() -> dict[str, Any]:
    """Return the fixed synthetic curriculum for display in the local UI."""

    return {
        "schema_version": "arc-registration-practice-catalog-v1",
        "data_classification": "synthetic_fixture_only",
        "form_fields": list(FORM_FIELDS),
        "scenarios": [
            {
                **deepcopy(scenario),
                "expected_issue_fields": list(scenario["expected_issue_fields"]),
            }
            for scenario in _SCENARIOS
        ],
        "submission_allowed": False,
        "browser_automation_allowed": False,
        "external_side_effects": False,
    }


def _scenario(identifier: Any) -> Mapping[str, Any]:
    if not isinstance(identifier, str) or not identifier.strip():
        raise RegistrationPracticeError("scenario_id is required")
    selected = identifier.strip()
    for scenario in _SCENARIOS:
        if scenario["scenario_id"] == selected:
            return scenario
    raise RegistrationPracticeError("unknown registration practice scenario")


def _issue_reason(field: str, value: Any) -> str | None:
    if value is None or not isinstance(value, str) or not value.strip():
        return "missing_value"
    if field == "email" and _EMAIL.fullmatch(value) is None:
        return "invalid_synthetic_email"
    if field == "phone" and _PHONE.fullmatch(value) is None:
        return "invalid_phone"
    if field == "state" and _STATE.fullmatch(value) is None:
        return "invalid_state"
    if field == "postal_code" and _POSTAL_CODE.fullmatch(value) is None:
        return "invalid_postal_code"
    if field == "preferred_contact" and value not in {"email", "phone"}:
        return "unsupported_contact_preference"
    if field == "consent_to_contact" and value != "yes":
        return "consent_not_granted"
    return None


def run_scenario(scenario_id: Any) -> dict[str, Any]:
    """Prepare one mock form and score it without any external action."""

    scenario = _scenario(scenario_id)
    profile = scenario["profile"]
    prepared_fields: dict[str, str] = {}
    issues: list[dict[str, str]] = []

    for field in FORM_FIELDS:
        value = profile.get(field)
        reason = _issue_reason(field, value)
        if reason is None:
            prepared_fields[field] = value
        else:
            prepared_fields[field] = ""
            issues.append(
                {
                    "field": field,
                    "status": NEEDS_HUMAN_INPUT,
                    "reason_code": reason,
                }
            )

    actual_issue_fields = sorted(issue["field"] for issue in issues)
    expected_issue_fields = sorted(scenario["expected_issue_fields"])
    valid_fields_copied_exactly = all(
        prepared_fields[field] == profile[field]
        for field in FORM_FIELDS
        if field not in actual_issue_fields
    )
    no_values_invented = all(
        prepared_fields[field] in {"", profile.get(field)} for field in FORM_FIELDS
    )
    checks = {
        "all_fields_known": set(prepared_fields) == set(FORM_FIELDS),
        "valid_fields_copied_exactly": valid_fields_copied_exactly,
        "expected_issues_flagged": actual_issue_fields == expected_issue_fields,
        "no_values_invented": no_values_invented,
        "human_review_required": True,
        "submission_blocked": True,
        "external_side_effects_blocked": True,
    }
    passed = all(checks.values())
    score = round(100 * sum(checks.values()) / len(checks))
    return {
        "schema_version": "arc-registration-practice-result-v1",
        "scenario_id": scenario["scenario_id"],
        "title": scenario["title"],
        "objective": scenario["objective"],
        "synthetic_profile": deepcopy(profile),
        "prepared_fields": prepared_fields,
        "issues": issues,
        "checks": checks,
        "score": score,
        "passed": passed,
        "status": "ready_for_human_review" if passed else "practice_failed_closed",
        "synthetic_data_only": True,
        "submission_allowed": False,
        "browser_automation_allowed": False,
        "external_side_effects": False,
    }


def run_suite() -> dict[str, Any]:
    """Run every fixed scenario and return deterministic curriculum results."""

    results = [run_scenario(scenario["scenario_id"]) for scenario in _SCENARIOS]
    passed = sum(result["passed"] for result in results)
    return {
        "schema_version": "arc-registration-practice-suite-v1",
        "status": "passed" if passed == len(results) else "failed_closed",
        "scenario_count": len(results),
        "passed_count": passed,
        "failed_count": len(results) - passed,
        "average_score": round(
            sum(result["score"] for result in results) / len(results)
        ),
        "results": results,
        "synthetic_data_only": True,
        "submission_allowed": False,
        "browser_automation_allowed": False,
        "external_side_effects": False,
    }
