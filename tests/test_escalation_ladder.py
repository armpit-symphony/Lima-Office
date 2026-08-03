"""Proofs that a configured escalation ladder can actually terminate.

Every rung below the last is automated, so the only thing guaranteeing an
escalation ever stops is that a human tier exists, sits last, and cannot
defer. The ladder is customer configuration authored through a UI, which makes
it untrusted input: these tests are mostly about what the loader refuses.
"""

from __future__ import annotations

import unittest

from lima_office.runtime.escalation import (
    UNBOUNDED_PERMIT_SCOPE,
    EscalationLadder,
    EscalationLadderError,
    EscalationTier,
    default_ladder,
    escalation_record,
    load_ladder,
)


def _tier(tier: int, role: str, kind: str, *permits: str) -> EscalationTier:
    return EscalationTier(
        tier=tier, role=role, kind=kind, may_permit=frozenset(permits)
    )


def _human(tier: int, role: str = "human operator") -> EscalationTier:
    return _tier(tier, role, "human", UNBOUNDED_PERMIT_SCOPE)


def _valid_payload() -> dict:
    return {
        "tiers": [
            {"role": "shift lead", "kind": "system_manager", "may_permit": ["routine"]},
            {
                "role": "general manager",
                "kind": "executive",
                "may_permit": ["routine", "elevated"],
            },
            {"role": "owner", "kind": "human", "may_permit": ["*"]},
        ]
    }


class TerminationTests(unittest.TestCase):
    """The property the whole design rests on."""

    def test_a_ladder_without_a_human_tier_is_refused(self):
        """Automated rungs alone can escalate forever."""

        with self.assertRaises(EscalationLadderError) as caught:
            EscalationLadder(
                tiers=(
                    _tier(1, "lead", "system_manager", "routine"),
                    _tier(2, "gm", "executive", "routine", "elevated"),
                )
            )
        self.assertIn("terminate", str(caught.exception))

    def test_the_human_tier_must_be_last(self):
        with self.assertRaises(EscalationLadderError):
            EscalationLadder(
                tiers=(
                    _tier(1, "lead", "system_manager", "routine"),
                    _human(2),
                    _tier(3, "gm", "executive", "routine", "elevated"),
                )
            )

    def test_only_one_terminal_tier_is_allowed(self):
        with self.assertRaises(EscalationLadderError):
            EscalationLadder(
                tiers=(
                    _tier(1, "lead", "system_manager", "routine"),
                    _tier(2, "gm", "executive", "routine", "elevated"),
                    _human(3, "owner"),
                    _human(4, "founder"),
                )
            )

    def test_the_terminal_tier_cannot_defer(self):
        ladder = default_ladder()
        self.assertFalse(ladder.terminal_tier.may_defer)
        self.assertTrue(ladder.tier(1).may_defer)

    def test_the_terminal_tier_cannot_escalate_further(self):
        ladder = default_ladder()
        with self.assertRaises(EscalationLadderError) as caught:
            ladder.next_tier(len(ladder.tiers))
        self.assertIn("decides", str(caught.exception))


class MovementIsUpwardOnlyTests(unittest.TestCase):
    """Sideways or downward movement would dissolve the guarantee."""

    def setUp(self) -> None:
        self.ladder = default_ladder()

    def test_next_tier_is_strictly_one_above(self):
        self.assertEqual(2, self.ladder.next_tier(1).tier)
        self.assertEqual(3, self.ladder.next_tier(2).tier)

    def test_a_tier_outside_the_ladder_is_refused(self):
        for current in (0, -1, 99):
            with self.subTest(current=current):
                with self.assertRaises(EscalationLadderError):
                    self.ladder.next_tier(current)

    def test_a_non_integer_tier_is_refused(self):
        for current in ("1", None, 1.5, True):
            with self.subTest(current=current):
                with self.assertRaises(EscalationLadderError):
                    self.ladder.next_tier(current)


class FloorTests(unittest.TestCase):
    """Every deployment has at least a system manager and an executive."""

    def test_a_ladder_missing_the_system_manager_is_refused(self):
        with self.assertRaises(EscalationLadderError) as caught:
            EscalationLadder(
                tiers=(_tier(1, "gm", "executive", "routine"), _human(2))
            )
        self.assertIn("system_manager", str(caught.exception))

    def test_a_ladder_missing_the_executive_is_refused(self):
        with self.assertRaises(EscalationLadderError) as caught:
            EscalationLadder(
                tiers=(_tier(1, "lead", "system_manager", "routine"), _human(2))
            )
        self.assertIn("executive", str(caught.exception))

    def test_the_default_ladder_is_exactly_the_floor(self):
        ladder = default_ladder()
        self.assertEqual(3, len(ladder.tiers))
        self.assertEqual(
            ["system_manager", "executive", "human"],
            [tier.kind for tier in ladder.tiers],
        )


class AuthorityMustIncreaseTests(unittest.TestCase):
    """A rung that cannot decide more denies for the same reason."""

    def test_equal_authority_between_rungs_is_refused(self):
        with self.assertRaises(EscalationLadderError) as caught:
            EscalationLadder(
                tiers=(
                    _tier(1, "lead", "system_manager", "routine"),
                    _tier(2, "gm", "executive", "routine"),
                    _human(3),
                )
            )
        self.assertIn("strictly more", str(caught.exception))

    def test_narrower_authority_above_is_refused(self):
        with self.assertRaises(EscalationLadderError):
            EscalationLadder(
                tiers=(
                    _tier(1, "lead", "system_manager", "routine", "elevated"),
                    _tier(2, "gm", "executive", "routine"),
                    _human(3),
                )
            )

    def test_overlapping_but_not_superset_authority_is_refused(self):
        """Different is not the same as greater."""

        with self.assertRaises(EscalationLadderError):
            EscalationLadder(
                tiers=(
                    _tier(1, "lead", "system_manager", "routine"),
                    _tier(2, "gm", "executive", "elevated"),
                    _human(3),
                )
            )

    def test_first_tier_permitting_finds_the_lowest_competent_rung(self):
        ladder = default_ladder()
        self.assertEqual(1, ladder.first_tier_permitting("routine_office_work").tier)
        self.assertEqual(2, ladder.first_tier_permitting("elevated_office_work").tier)

    def test_an_unrecognised_action_class_lands_on_the_human(self):
        ladder = default_ladder()
        self.assertTrue(ladder.first_tier_permitting("something_novel").is_terminal)


class PermitScopeTests(unittest.TestCase):
    """Only a person holds unbounded authority."""

    def test_an_automated_tier_may_not_be_unbounded(self):
        with self.assertRaises(EscalationLadderError) as caught:
            _tier(1, "lead", "system_manager", UNBOUNDED_PERMIT_SCOPE)
        self.assertIn("unbounded", str(caught.exception))

    def test_the_human_tier_must_be_unbounded(self):
        with self.assertRaises(EscalationLadderError):
            _tier(1, "owner", "human", "routine")

    def test_a_tier_with_no_declared_authority_is_refused(self):
        with self.assertRaises(EscalationLadderError):
            _tier(1, "lead", "system_manager")


class TierShapeTests(unittest.TestCase):
    """Ordinary structural validation."""

    def test_tiers_must_be_contiguous_and_ascending(self):
        with self.assertRaises(EscalationLadderError):
            EscalationLadder(
                tiers=(
                    _tier(1, "lead", "system_manager", "routine"),
                    _tier(3, "gm", "executive", "routine", "elevated"),
                    _human(4),
                )
            )

    def test_an_empty_ladder_is_refused(self):
        with self.assertRaises(EscalationLadderError):
            EscalationLadder(tiers=())

    def test_duplicate_role_labels_are_refused(self):
        with self.assertRaises(EscalationLadderError):
            EscalationLadder(
                tiers=(
                    _tier(1, "Manager", "system_manager", "routine"),
                    _tier(2, "manager", "executive", "routine", "elevated"),
                    _human(3),
                )
            )

    def test_an_unknown_kind_is_refused(self):
        with self.assertRaises(EscalationLadderError):
            _tier(1, "lead", "vice_president", "routine")

    def test_a_blank_role_label_is_refused(self):
        with self.assertRaises(EscalationLadderError):
            _tier(1, "   ", "system_manager", "routine")


class LoaderTests(unittest.TestCase):
    """Configuration from a UI is untrusted input."""

    def test_a_valid_configuration_loads(self):
        ladder = load_ladder(_valid_payload())
        self.assertEqual(3, len(ladder.tiers))
        self.assertEqual("owner", ladder.terminal_tier.role)

    def test_tier_numbers_are_assigned_from_order(self):
        ladder = load_ladder(_valid_payload())
        self.assertEqual([1, 2, 3], [tier.tier for tier in ladder.tiers])

    def test_a_non_object_configuration_is_refused(self):
        for payload in (None, [], "tiers", 7):
            with self.subTest(payload=payload):
                with self.assertRaises(EscalationLadderError):
                    load_ladder(payload)

    def test_a_configuration_without_tiers_is_refused(self):
        for payload in ({}, {"tiers": []}, {"tiers": "supervisor"}):
            with self.subTest(payload=payload):
                with self.assertRaises(EscalationLadderError):
                    load_ladder(payload)

    def test_a_configuration_missing_permit_scope_is_refused(self):
        payload = _valid_payload()
        del payload["tiers"][0]["may_permit"]
        with self.assertRaises(EscalationLadderError):
            load_ladder(payload)

    def test_an_unterminated_configuration_is_refused_at_load(self):
        """The failure that must not start a deployment."""

        payload = _valid_payload()
        payload["tiers"] = payload["tiers"][:2]
        with self.assertRaises(EscalationLadderError):
            load_ladder(payload)

    def test_a_customer_may_name_a_rung_supervisor_without_ambiguity(self):
        """The label collides with the control plane; the kind does not."""

        payload = _valid_payload()
        payload["tiers"][0]["role"] = "Supervisor"
        ladder = load_ladder(payload)

        self.assertEqual("Supervisor", ladder.tier(1).role)
        self.assertEqual("system_manager", ladder.tier(1).kind)


class EvidenceTests(unittest.TestCase):
    """Tier and role travel together, always."""

    def test_a_record_names_both_rung_and_role(self):
        record = escalation_record(
            default_ladder(), from_tier=1, reason_codes=["outbound_missing_approval"]
        )
        self.assertEqual(1, record["from"]["escalation_tier"])
        self.assertEqual("system manager", record["from"]["role"])
        self.assertEqual(2, record["to"]["escalation_tier"])
        self.assertFalse(record["terminal"])

    def test_a_record_marks_arrival_at_the_human_tier(self):
        record = escalation_record(
            default_ladder(), from_tier=2, reason_codes=["outbound_missing_approval"]
        )
        self.assertTrue(record["terminal"])
        self.assertFalse(record["to"]["may_defer"])

    def test_reason_codes_are_sorted_for_stable_evidence(self):
        record = escalation_record(
            default_ladder(), from_tier=1, reason_codes=["b_code", "a_code"]
        )
        self.assertEqual(["a_code", "b_code"], record["reason_codes"])

    def test_a_record_cannot_be_made_from_the_terminal_tier(self):
        with self.assertRaises(EscalationLadderError):
            escalation_record(default_ladder(), from_tier=3, reason_codes=[])


if __name__ == "__main__":
    unittest.main()
