"""Lab 4 localhost-only registration workflow and deterministic test range."""

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

_TEMPLATES: tuple[dict[str, Any], ...] = (
    {
        "template_id": "community-program",
        "title": "Community program registration",
        "description": "Contact-first layout for a fictional community program.",
        "fields": (
            ("full_name", "Participant name", "text"),
            ("email", "Email address", "email"),
            ("phone", "Phone number", "tel"),
            ("preferred_contact", "Preferred contact", "select"),
            ("address_line1", "Street address", "text"),
            ("city", "City", "text"),
            ("state", "State", "text"),
            ("postal_code", "ZIP code", "text"),
            ("consent_to_contact", "Contact consent", "select"),
        ),
    },
    {
        "template_id": "service-intake",
        "title": "Service intake registration",
        "description": "Address-first layout for a fictional service intake.",
        "fields": (
            ("full_name", "Client name", "text"),
            ("address_line1", "Service address", "text"),
            ("city", "Municipality", "text"),
            ("state", "State abbreviation", "text"),
            ("postal_code", "Postal code", "text"),
            ("phone", "Primary phone", "tel"),
            ("email", "Primary email", "email"),
            ("preferred_contact", "Contact method", "select"),
            ("consent_to_contact", "Permission to contact", "select"),
        ),
    },
    {
        "template_id": "event-enrollment",
        "title": "Event enrollment registration",
        "description": "Consent-forward layout for a fictional local event.",
        "fields": (
            ("consent_to_contact", "May organizers contact you?", "select"),
            ("full_name", "Attendee name", "text"),
            ("preferred_contact", "Contact preference", "select"),
            ("phone", "Mobile phone", "tel"),
            ("email", "Email", "email"),
            ("address_line1", "Mailing address", "text"),
            ("postal_code", "ZIP", "text"),
            ("city", "City", "text"),
            ("state", "State", "text"),
        ),
    },
)

_VARIANTS = (
    ("complete", "Complete fictional record", None),
    ("missing-phone", "Missing fictional phone", "phone"),
    ("invalid-email", "Invalid fictional email", "email"),
    ("invalid-postal", "Invalid fictional postal code", "postal_code"),
    ("no-consent", "Contact consent not granted", "consent_to_contact"),
)

_EMAIL = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.test$")
_PHONE = re.compile(r"^555-01\d{2}$")
_STATE = re.compile(r"^[A-Z]{2}$")
_POSTAL_CODE = re.compile(r"^\d{5}$")


class RegistrationWorkflowError(ValueError):
    """Raised when a request leaves the fixed localhost lab contract."""


def _render_template(template: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "template_id": template["template_id"],
        "title": template["title"],
        "description": template["description"],
        "fields": [
            {"field": field, "label": label, "input_type": input_type}
            for field, label, input_type in template["fields"]
        ],
    }


def _profile(index: int, issue_field: str | None) -> dict[str, str | None]:
    profile: dict[str, str | None] = {
        "full_name": f"Practice Person {index:02d}",
        "email": f"practice{index:02d}@example.test",
        "phone": f"555-01{index:02d}",
        "address_line1": f"{100 + index} Fixture Lane",
        "city": "Sample City",
        "state": "NY",
        "postal_code": f"{10000 + index}",
        "preferred_contact": "email" if index % 2 else "phone",
        "consent_to_contact": "yes",
    }
    if issue_field == "phone":
        profile["phone"] = None
    elif issue_field == "email":
        profile["email"] = f"practice{index:02d}.example.test"
    elif issue_field == "postal_code":
        profile["postal_code"] = "10A00"
    elif issue_field == "consent_to_contact":
        profile["consent_to_contact"] = "no"
    return profile


def _build_scenarios() -> tuple[dict[str, Any], ...]:
    scenarios: list[dict[str, Any]] = []
    for index in range(1, 26):
        template = _TEMPLATES[(index - 1) % len(_TEMPLATES)]
        variant_id, variant_title, issue_field = _VARIANTS[(index - 1) % 5]
        scenarios.append(
            {
                "scenario_id": f"{template['template_id']}-{variant_id}-{index:02d}",
                "title": f"{index:02d} · {variant_title}",
                "objective": (
                    "Map only supplied values into the selected localhost form "
                    "layout and stop for explicit human review."
                ),
                "template_id": template["template_id"],
                "profile": _profile(index, issue_field),
                "expected_issue_fields": (() if issue_field is None else (issue_field,)),
            }
        )
    return tuple(scenarios)


_SCENARIOS = _build_scenarios()


def catalog() -> dict[str, Any]:
    """Return the fixed synthetic records and form templates for the UI."""

    return {
        "schema_version": "arc-registration-workflow-catalog-v2",
        "data_classification": "synthetic_fixture_only",
        "form_fields": list(FORM_FIELDS),
        "templates": [_render_template(template) for template in _TEMPLATES],
        "scenarios": [
            {
                **deepcopy(scenario),
                "expected_issue_fields": list(scenario["expected_issue_fields"]),
            }
            for scenario in _SCENARIOS
        ],
        "human_review_required": True,
        "mock_target": "localhost_test_range",
        "mock_submission_available": True,
        "submission_allowed": False,
        "external_submission_allowed": False,
        "browser_automation_allowed": False,
        "external_side_effects": False,
    }


def _scenario(identifier: Any) -> Mapping[str, Any]:
    if not isinstance(identifier, str) or not identifier.strip():
        raise RegistrationWorkflowError("scenario_id is required")
    selected = identifier.strip()
    for scenario in _SCENARIOS:
        if scenario["scenario_id"] == selected:
            return scenario
    raise RegistrationWorkflowError("unknown registration workflow scenario")


def _template(identifier: str) -> Mapping[str, Any]:
    for template in _TEMPLATES:
        if template["template_id"] == identifier:
            return template
    raise RegistrationWorkflowError("unknown registration form template")


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
    """Prepare one local mock form and stop before human review."""

    scenario = _scenario(scenario_id)
    template = _template(str(scenario["template_id"]))
    rendered_template = _render_template(template)
    profile = scenario["profile"]
    prepared_fields: dict[str, str] = {}
    issues: list[dict[str, str]] = []

    for field in FORM_FIELDS:
        value = profile.get(field)
        reason = _issue_reason(field, value)
        if reason is None:
            prepared_fields[field] = str(value)
        else:
            prepared_fields[field] = ""
            issues.append(
                {"field": field, "status": NEEDS_HUMAN_INPUT, "reason_code": reason}
            )

    actual_issue_fields = sorted(issue["field"] for issue in issues)
    expected_issue_fields = sorted(scenario["expected_issue_fields"])
    valid_fields_copied_exactly = all(
        prepared_fields[field] == profile[field]
        for field in FORM_FIELDS
        if field not in actual_issue_fields
    )
    template_field_order = [field["field"] for field in rendered_template["fields"]]
    checks = {
        "all_fields_known": set(prepared_fields) == set(FORM_FIELDS),
        "template_fields_exact": set(template_field_order) == set(FORM_FIELDS),
        "valid_fields_copied_exactly": valid_fields_copied_exactly,
        "expected_issues_flagged": actual_issue_fields == expected_issue_fields,
        "no_values_invented": all(
            prepared_fields[field] in {"", profile.get(field)} for field in FORM_FIELDS
        ),
        "human_review_required": True,
        "external_submission_blocked": True,
        "external_side_effects_blocked": True,
    }
    passed = all(checks.values())
    review_eligible = passed and not issues
    return {
        "schema_version": "arc-registration-workflow-result-v2",
        "scenario_id": scenario["scenario_id"],
        "title": scenario["title"],
        "objective": scenario["objective"],
        "form_template": rendered_template,
        "synthetic_profile": deepcopy(profile),
        "prepared_fields": prepared_fields,
        "issues": issues,
        "checks": checks,
        "score": round(100 * sum(checks.values()) / len(checks)),
        "passed": passed,
        "status": "ready_for_human_review" if passed else "practice_failed_closed",
        "review_eligible": review_eligible,
        "mock_target": "localhost_test_range",
        "mock_submission_performed": False,
        "synthetic_data_only": True,
        "submission_allowed": False,
        "external_submission_allowed": False,
        "browser_automation_allowed": False,
        "external_side_effects": False,
    }


def run_suite() -> dict[str, Any]:
    """Run all 25 fixed records across the three local form layouts."""

    results = [run_scenario(scenario["scenario_id"]) for scenario in _SCENARIOS]
    passed = sum(result["passed"] for result in results)
    return {
        "schema_version": "arc-registration-workflow-suite-v2",
        "status": "passed" if passed == len(results) else "failed_closed",
        "scenario_count": len(results),
        "template_count": len(_TEMPLATES),
        "passed_count": passed,
        "failed_count": len(results) - passed,
        "average_score": round(sum(result["score"] for result in results) / len(results)),
        "results": results,
        "synthetic_data_only": True,
        "submission_allowed": False,
        "external_submission_allowed": False,
        "browser_automation_allowed": False,
        "external_side_effects": False,
    }
