"""Proofs for what a shell may do about a denial.

The escalation ladder in the LIMA office ecosystem is automated: Arc bot, the
supervisor role, manager and GM are all machines, and only Human terminates.
That makes the disposition axis a safety boundary rather than a convenience.
Escalating a policy denial to a higher automated authority is authority
shopping - the same failure as auto-retry, with a different decider.

These tests hold the two properties that keep it safe: unclassified denials
stop, and the most restrictive reason in a set governs the whole denial.
"""

from __future__ import annotations

import unittest

from lima_office.runtime.taxonomy import (
    ALIAS_TO_CANONICAL,
    DEFAULT_DENIAL_DISPOSITION,
    DENIAL_DISPOSITIONS,
    DENIAL_DISPOSITION_OVERRIDES,
    DENIAL_DISPOSITION_PRECEDENCE,
    REASON_CODE_REGISTRY,
    denial_disposition,
    denial_disposition_for_set,
    may_escalate,
)


class RegistryIntegrityTests(unittest.TestCase):
    """The classification table must describe codes that exist."""

    def test_every_override_names_a_real_reason_code(self):
        """A typo here would silently classify nothing and read as deliberate."""

        unknown = sorted(
            code
            for code in DENIAL_DISPOSITION_OVERRIDES
            if code not in REASON_CODE_REGISTRY
        )
        self.assertEqual([], unknown)

    def test_every_override_value_is_a_known_disposition(self):
        invalid = {
            code: value
            for code, value in DENIAL_DISPOSITION_OVERRIDES.items()
            if value not in DENIAL_DISPOSITIONS
        }
        self.assertEqual({}, invalid)

    def test_precedence_covers_every_disposition(self):
        """A disposition missing from precedence would fall through to default."""

        self.assertEqual(DENIAL_DISPOSITIONS, set(DENIAL_DISPOSITION_PRECEDENCE))

    def test_forbidden_is_the_most_restrictive_and_comes_first(self):
        self.assertEqual("forbidden", DENIAL_DISPOSITION_PRECEDENCE[0])


class DefaultIsForbiddenTests(unittest.TestCase):
    """The property that makes a missed classification safe."""

    def test_the_default_is_forbidden(self):
        self.assertEqual("forbidden", DEFAULT_DENIAL_DISPOSITION)

    def test_an_unclassified_registry_code_is_forbidden(self):
        unclassified = next(
            code
            for code in REASON_CODE_REGISTRY
            if code not in DENIAL_DISPOSITION_OVERRIDES
        )
        self.assertEqual("forbidden", denial_disposition(unclassified))

    def test_an_unknown_code_is_forbidden_rather_than_raising(self):
        """A shell that cannot classify a denial must stop, not guess."""

        self.assertEqual("forbidden", denial_disposition("no_such_reason_code_at_all"))

    def test_empty_and_malformed_inputs_are_forbidden(self):
        for value in ("", None, 0, [], (), set(), "not_a_code", 17):
            with self.subTest(value=value):
                self.assertEqual("forbidden", denial_disposition_for_set(value))

    def test_a_bare_string_is_not_treated_as_a_set_of_characters(self):
        """Passing one code where a set is expected must not silently pass."""

        self.assertEqual(
            "forbidden",
            denial_disposition_for_set("request_resource_type_not_permitted"),
        )


class ClassificationTests(unittest.TestCase):
    """The four classes, on the codes that motivated them."""

    def test_an_inadmissible_request_is_correctable(self):
        self.assertEqual(
            "correctable",
            denial_disposition("request_resource_type_not_permitted"),
        )

    def test_an_aged_decision_is_retried_with_a_fresh_one(self):
        for code in ("decision_expired", "decision_stale"):
            with self.subTest(code=code):
                self.assertEqual("retry_with_fresh_decision", denial_disposition(code))

    def test_a_missing_approval_is_what_the_ladder_is_for(self):
        self.assertEqual("escalatable", denial_disposition("outbound_missing_approval"))

    def test_adversarial_input_is_terminal(self):
        """Escalating these hands an attacker a higher-authority target."""

        for code in (
            "prompt_injection_suspected",
            "tainted_input",
            "connector_prompt_injection_blocked",
            "model_route_tainted_input_denied",
        ):
            with self.subTest(code=code):
                self.assertEqual("forbidden", denial_disposition(code))
                self.assertFalse(may_escalate([code]))

    def test_integrity_failures_are_terminal(self):
        """No other authority may bless a decision that does not match."""

        for code in ("guardian_decision_mismatch", "decision_scope_hash_mismatch"):
            with self.subTest(code=code):
                self.assertFalse(may_escalate([code]))

    def test_codes_indistinguishable_in_the_registry_now_differ(self):
        """The reason this axis exists at all, derived rather than asserted.

        If some pair of classified codes shares category, severity and
        fail_closed_required yet needs opposite handling, then the existing
        fields cannot drive denial routing and a separate axis is required.
        """

        def fingerprint(code: str) -> tuple:
            meta = REASON_CODE_REGISTRY[code]
            return (
                meta["category"],
                meta["severity"],
                meta["fail_closed_required"],
            )

        classified = sorted(
            code for code in DENIAL_DISPOSITION_OVERRIDES if code in REASON_CODE_REGISTRY
        )
        collisions = [
            (left, right)
            for index, left in enumerate(classified)
            for right in classified[index + 1 :]
            if fingerprint(left) == fingerprint(right)
            and denial_disposition(left) != denial_disposition(right)
        ]

        self.assertTrue(
            collisions,
            "no indistinguishable pair found; the disposition axis may be redundant",
        )
        # e.g. tainted_input and decision_expired: both guardian/blocked/True,
        # one terminal and one merely stale.
        left, right = collisions[0]
        self.assertEqual(fingerprint(left), fingerprint(right))


class MostRestrictiveWinsTests(unittest.TestCase):
    """A denial rarely carries one reason."""

    def test_forbidden_beats_every_other_disposition(self):
        for other in (
            "request_resource_type_not_permitted",
            "decision_expired",
            "outbound_missing_approval",
        ):
            with self.subTest(other=other):
                self.assertEqual(
                    "forbidden",
                    denial_disposition_for_set(["prompt_injection_suspected", other]),
                )

    def test_correcting_a_field_does_not_dissolve_a_forbidden_reason(self):
        """The failure mode this ordering prevents."""

        codes = ["request_resource_type_not_permitted", "tainted_input"]
        self.assertEqual("forbidden", denial_disposition_for_set(codes))
        self.assertFalse(may_escalate(codes))

    def test_escalation_beats_retry_and_correction(self):
        self.assertEqual(
            "escalatable",
            denial_disposition_for_set(
                ["outbound_missing_approval", "decision_expired"]
            ),
        )

    def test_a_single_escalatable_reason_may_climb(self):
        self.assertTrue(may_escalate(["outbound_missing_approval"]))

    def test_order_of_reason_codes_does_not_change_the_outcome(self):
        forward = ["outbound_missing_approval", "prompt_injection_suspected"]
        self.assertEqual(
            denial_disposition_for_set(forward),
            denial_disposition_for_set(list(reversed(forward))),
        )


class AliasTests(unittest.TestCase):
    """An alias must not become a way around a classification."""

    def test_an_alias_resolves_to_its_canonical_disposition(self):
        aliased = {
            alias: canonical
            for alias, canonical in ALIAS_TO_CANONICAL.items()
            if canonical in DENIAL_DISPOSITION_OVERRIDES
        }
        if not aliased:
            self.skipTest("no alias currently points at a classified code")
        for alias, canonical in aliased.items():
            with self.subTest(alias=alias):
                self.assertEqual(
                    denial_disposition(canonical), denial_disposition(alias)
                )


if __name__ == "__main__":
    unittest.main()
