"""Proofs for turning denials into training signal without teaching around controls.

Arc bot is fed SOP and trained until it can do its job accurately alone. Every
time it stops short, that is a fact about what it has not been taught. The
danger in treating denials as training data is obvious once stated: some
denials exist to stop something, and an instruction that closed one of those
would be an instruction to defeat it.

Most of these tests are about that line.
"""

from __future__ import annotations

import unittest

from lima_office.runtime.sop import (
    TEACHABLE_DISPOSITIONS,
    SopGap,
    SopGapError,
    gap_from_denial,
    gap_id_for,
    is_teachable,
    operator_authored_gap,
    training_progress,
)


CORRECTABLE = "request_resource_type_not_permitted"
ESCALATABLE = "outbound_missing_approval"
FORBIDDEN = "prompt_injection_suspected"
STALE = "decision_expired"


class TeachabilityTests(unittest.TestCase):
    """The safety boundary of the whole loop."""

    def test_a_correctable_denial_is_teachable(self):
        """Arc built the request wrong; an SOP teaches it the right shape."""

        self.assertTrue(is_teachable([CORRECTABLE]))

    def test_an_escalatable_denial_is_teachable(self):
        """A higher rung decided; the SOP records the decision for reuse."""

        self.assertTrue(is_teachable([ESCALATABLE]))

    def test_a_forbidden_denial_is_never_teachable(self):
        """The control worked. There is nothing here to learn."""

        self.assertFalse(is_teachable([FORBIDDEN]))

    def test_a_stale_decision_is_not_a_training_gap(self):
        """Nothing was refused and nothing misunderstood; it just aged out."""

        self.assertFalse(is_teachable([STALE]))

    def test_a_forbidden_reason_alongside_a_teachable_one_is_not_teachable(self):
        """The most restrictive reason governs, as it does everywhere else."""

        self.assertFalse(is_teachable([CORRECTABLE, FORBIDDEN]))

    def test_a_denial_with_no_reason_is_not_teachable(self):
        self.assertFalse(is_teachable([]))

    def test_an_unknown_reason_code_is_not_teachable(self):
        """Unclassified codes are forbidden, so they cannot become gaps."""

        self.assertFalse(is_teachable(["some_code_nobody_classified"]))

    def test_the_teachable_set_excludes_forbidden(self):
        self.assertNotIn("forbidden", TEACHABLE_DISPOSITIONS)
        self.assertNotIn("retry_with_fresh_decision", TEACHABLE_DISPOSITIONS)


class GapFromDenialTests(unittest.TestCase):
    """Walking an evidence stream must not raise on the ordinary case."""

    def test_a_teachable_denial_becomes_a_gap(self):
        gap = gap_from_denial(
            task_ref="task:1", capability="document_read", reason_codes=[CORRECTABLE]
        )
        self.assertIsNotNone(gap)
        self.assertEqual("open", gap.status)
        self.assertEqual("correctable", gap.disposition)
        self.assertEqual("escalation", gap.source)

    def test_a_forbidden_denial_yields_no_gap_rather_than_raising(self):
        gap = gap_from_denial(
            task_ref="task:1", capability="document_read", reason_codes=[FORBIDDEN]
        )
        self.assertIsNone(gap)

    def test_a_stale_decision_yields_no_gap(self):
        self.assertIsNone(
            gap_from_denial(
                task_ref="task:1", capability="document_read", reason_codes=[STALE]
            )
        )

    def test_an_escalated_gap_records_the_rung_that_saw_it(self):
        gap = gap_from_denial(
            task_ref="task:1",
            capability="document_read",
            reason_codes=[ESCALATABLE],
            escalated_to_tier=2,
        )
        self.assertEqual(2, gap.escalated_to_tier)


class ConstructionRefusalTests(unittest.TestCase):
    """A gap that would teach around a control must not exist at all."""

    def _gap(self, **overrides):
        payload = dict(
            gap_id="sop-gap:test",
            task_ref="task:1",
            capability="document_read",
            reason_codes=(CORRECTABLE,),
            disposition="correctable",
            source="escalation",
        )
        payload.update(overrides)
        return SopGap(**payload)

    def test_a_gap_cannot_be_built_from_a_forbidden_denial(self):
        """Bypassing gap_from_denial must not bypass the boundary."""

        with self.assertRaises(SopGapError) as caught:
            self._gap(reason_codes=(FORBIDDEN,), disposition="forbidden")
        self.assertIn("defeat a control", str(caught.exception))

    def test_an_observed_gap_must_record_why_it_stopped(self):
        with self.assertRaises(SopGapError):
            self._gap(reason_codes=())

    def test_an_instructed_gap_needs_its_instruction(self):
        with self.assertRaises(SopGapError):
            self._gap(status="instructed")

    def test_a_retired_gap_needs_its_instruction(self):
        with self.assertRaises(SopGapError):
            self._gap(status="retired")

    def test_unknown_sources_and_statuses_are_refused(self):
        with self.assertRaises(SopGapError):
            self._gap(source="guessed")
        with self.assertRaises(SopGapError):
            self._gap(status="maybe")

    def test_a_blank_identifier_is_refused(self):
        for field in ("gap_id", "task_ref", "capability"):
            with self.subTest(field=field):
                with self.assertRaises(SopGapError):
                    self._gap(**{field: "   "})

    def test_an_invalid_tier_is_refused(self):
        for tier in (0, -1, True, "2"):
            with self.subTest(tier=tier):
                with self.assertRaises(SopGapError):
                    self._gap(escalated_to_tier=tier)


class InstructionTests(unittest.TestCase):
    """Closing a gap is the same action however the instruction arrived."""

    def setUp(self) -> None:
        self.gap = gap_from_denial(
            task_ref="task:1", capability="document_read", reason_codes=[ESCALATABLE]
        )

    def test_an_instruction_moves_a_gap_to_instructed(self):
        taught = self.gap.with_instruction(
            "Attach the signed approval before requesting an outbound send.",
            resolved_by_role="GM",
        )
        self.assertEqual("instructed", taught.status)
        self.assertEqual("GM", taught.resolved_by_role)

    def test_the_original_gap_is_unchanged(self):
        self.gap.with_instruction("do the thing", resolved_by_role="GM")
        self.assertEqual("open", self.gap.status)
        self.assertIsNone(self.gap.instruction)

    def test_an_empty_instruction_is_refused(self):
        for instruction in ("", "   ", None):
            with self.subTest(instruction=instruction):
                with self.assertRaises(SopGapError):
                    self.gap.with_instruction(instruction, resolved_by_role="GM")

    def test_who_supplied_the_instruction_is_required(self):
        with self.assertRaises(SopGapError):
            self.gap.with_instruction("do the thing", resolved_by_role="  ")


class OperatorAuthoredTests(unittest.TestCase):
    """The UI input option: teach Arc before it fails, not only after."""

    def test_authored_sop_is_instructed_from_the_start(self):
        gap = operator_authored_gap(
            task_ref="task:1",
            capability="document_read",
            instruction="Quarterly reports live in the archive folder.",
            authored_by_role="system manager",
        )
        self.assertEqual("instructed", gap.status)
        self.assertEqual("operator_authored", gap.source)

    def test_authored_sop_carries_no_reason_codes(self):
        """Nothing was denied, so there is nothing to classify."""

        gap = operator_authored_gap(
            task_ref="task:1",
            capability="document_read",
            instruction="Check the archive folder first.",
            authored_by_role="system manager",
        )
        self.assertEqual((), gap.reason_codes)

    def test_authored_sop_needs_an_instruction(self):
        for instruction in ("", "   "):
            with self.subTest(instruction=instruction):
                with self.assertRaises(SopGapError):
                    operator_authored_gap(
                        task_ref="task:1",
                        capability="document_read",
                        instruction=instruction,
                        authored_by_role="system manager",
                    )

    def test_both_sources_produce_the_same_record_shape(self):
        """One training loop, whichever way the SOP arrived."""

        observed = gap_from_denial(
            task_ref="task:1", capability="document_read", reason_codes=[CORRECTABLE]
        ).to_dict()
        authored = operator_authored_gap(
            task_ref="task:2",
            capability="document_read",
            instruction="Check the archive folder first.",
            authored_by_role="system manager",
        ).to_dict()
        self.assertEqual(set(observed), set(authored))


class GapIdentityTests(unittest.TestCase):
    """The same shortfall twenty times is one thing to teach."""

    def test_the_same_shortfall_collapses_to_one_id(self):
        first = gap_id_for(
            task_ref="task:1", capability="document_read", reason_codes=[CORRECTABLE]
        )
        second = gap_id_for(
            task_ref="task:1", capability="document_read", reason_codes=[CORRECTABLE]
        )
        self.assertEqual(first, second)

    def test_reason_code_order_does_not_change_the_id(self):
        forward = gap_id_for(
            task_ref="task:1",
            capability="document_read",
            reason_codes=[CORRECTABLE, ESCALATABLE],
        )
        reverse = gap_id_for(
            task_ref="task:1",
            capability="document_read",
            reason_codes=[ESCALATABLE, CORRECTABLE],
        )
        self.assertEqual(forward, reverse)

    def test_different_capabilities_are_different_gaps(self):
        self.assertNotEqual(
            gap_id_for(task_ref="t", capability="a", reason_codes=[CORRECTABLE]),
            gap_id_for(task_ref="t", capability="b", reason_codes=[CORRECTABLE]),
        )


class EvidenceHygieneTests(unittest.TestCase):
    """A gap records what was attempted and why, never the material."""

    def test_the_record_has_no_field_for_task_payload_or_document_body(self):
        gap = gap_from_denial(
            task_ref="task:1", capability="document_read", reason_codes=[CORRECTABLE]
        )
        rendered = gap.to_dict()
        for forbidden_field in ("payload", "content", "body", "prompt", "output"):
            self.assertNotIn(forbidden_field, rendered)


class TrainingProgressTests(unittest.TestCase):
    """The number that says whether training is working."""

    def _gap(self, status: str) -> SopGap:
        gap = gap_from_denial(
            task_ref=f"task:{status}",
            capability="document_read",
            reason_codes=[CORRECTABLE],
        )
        if status == "open":
            return gap
        return gap.with_instruction("teach it", resolved_by_role="GM")

    def test_autonomy_rate_is_the_share_finished_alone(self):
        progress = training_progress(
            completed_alone=8, gaps=[self._gap("open"), self._gap("instructed")]
        )
        self.assertEqual(10, progress["attempts"])
        self.assertAlmostEqual(0.8, progress["autonomy_rate"])

    def test_a_perfect_run_is_full_autonomy(self):
        progress = training_progress(completed_alone=5, gaps=[])
        self.assertEqual(1.0, progress["autonomy_rate"])

    def test_no_attempts_yields_no_rate_rather_than_zero(self):
        """Nothing attempted is not the same as nothing achieved."""

        self.assertIsNone(training_progress(completed_alone=0, gaps=[])["autonomy_rate"])

    def test_gaps_are_counted_by_status(self):
        progress = training_progress(
            completed_alone=0,
            gaps=[self._gap("open"), self._gap("open"), self._gap("instructed")],
        )
        self.assertEqual(2, progress["open_gaps"])
        self.assertEqual(1, progress["instructed_gaps"])

    def test_negative_completions_are_refused(self):
        with self.assertRaises(SopGapError):
            training_progress(completed_alone=-1, gaps=[])

    def test_progress_reports_counts_only(self):
        """Nothing here reads an instruction body."""

        progress = training_progress(completed_alone=1, gaps=[self._gap("instructed")])
        self.assertNotIn("instruction", str(progress))


if __name__ == "__main__":
    unittest.main()
