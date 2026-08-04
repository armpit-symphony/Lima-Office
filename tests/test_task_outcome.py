"""Proofs for what happens to a queued task after the governed path answers.

This is where the three pieces meet: the disposition decides the class of
failure, the ladder decides who sees it next, and the SOP gap records what Arc
would need to learn to not need anyone next time.

The cases worth being sure about are the ones where a wrong answer is
expensive: a forbidden denial must not climb, a contradictory result must not
be read as success, and a task must not run out of retries on arrival at a
rung that has not tried yet.
"""

from __future__ import annotations

import unittest

from lima_office.runtime.escalation import (
    UNBOUNDED_PERMIT_SCOPE,
    EscalationLadder,
    EscalationTier,
    default_ladder,
)
from lima_office.runtime.task_outcome import (
    DEFAULT_MAX_ATTEMPTS,
    TaskAttempt,
    TaskOutcome,
    TaskOutcomeError,
    route_task_outcome,
    run_to_rest,
)


CORRECTABLE = "request_resource_type_not_permitted"
ESCALATABLE = "outbound_missing_approval"
FORBIDDEN = "prompt_injection_suspected"
STALE = "decision_expired"


def _attempt(**overrides) -> TaskAttempt:
    payload = dict(task_ref="task:1", capability="document_read")
    payload.update(overrides)
    return TaskAttempt(**payload)


def _route(attempt=None, *, performed=False, codes=(), ladder=None, **kwargs):
    return route_task_outcome(
        attempt or _attempt(),
        performed=performed,
        reason_codes=codes,
        ladder=ladder or default_ladder(),
        **kwargs,
    )


class CompletionTests(unittest.TestCase):
    """The ordinary case: Arc did the job alone."""

    def test_a_performed_attempt_with_no_reasons_completes(self):
        outcome = _route(performed=True)
        self.assertEqual("completed", outcome.status)
        self.assertTrue(outcome.is_terminal)
        self.assertIsNone(outcome.gap)

    def test_completion_produces_no_escalation(self):
        self.assertIsNone(_route(performed=True).escalation)


class ContradictionTests(unittest.TestCase):
    """A result that claims both must not be read as the happy one."""

    def test_performed_and_denied_at_once_is_treated_as_denied(self):
        outcome = _route(performed=True, codes=[ESCALATABLE])
        self.assertEqual("blocked", outcome.status)
        self.assertIn("treated as denied", outcome.note)

    def test_a_contradiction_does_not_escalate(self):
        """Neither half of the result can be trusted enough to act on."""

        self.assertIsNone(_route(performed=True, codes=[ESCALATABLE]).escalation)

    def test_nothing_happened_and_nothing_said_why_stops(self):
        outcome = _route(performed=False, codes=[])
        self.assertEqual("blocked", outcome.status)
        self.assertIsNone(outcome.next_attempt)


class ForbiddenNeverClimbsTests(unittest.TestCase):
    """The property the disposition axis exists to guarantee."""

    def test_a_forbidden_denial_blocks(self):
        outcome = _route(codes=[FORBIDDEN])
        self.assertEqual("blocked", outcome.status)
        self.assertEqual("forbidden", outcome.disposition)

    def test_a_forbidden_denial_produces_no_escalation_record(self):
        self.assertIsNone(_route(codes=[FORBIDDEN]).escalation)

    def test_a_forbidden_denial_produces_no_sop_gap(self):
        """There is nothing to teach; the control worked."""

        self.assertIsNone(_route(codes=[FORBIDDEN]).gap)

    def test_a_forbidden_denial_is_not_retried(self):
        self.assertIsNone(_route(codes=[FORBIDDEN]).next_attempt)

    def test_forbidden_alongside_correctable_still_blocks(self):
        """The most restrictive reason governs here too."""

        outcome = _route(codes=[CORRECTABLE, FORBIDDEN])
        self.assertEqual("blocked", outcome.status)
        self.assertIsNone(outcome.escalation)


class RetryTests(unittest.TestCase):
    """Correcting a request or refreshing a decision stays at the same rung."""

    def test_a_correctable_denial_retries_at_the_same_tier(self):
        outcome = _route(codes=[CORRECTABLE])
        self.assertEqual("retry", outcome.status)
        self.assertEqual(2, outcome.next_attempt.attempt)
        self.assertEqual(1, outcome.next_attempt.tier)

    def test_a_stale_decision_retries(self):
        outcome = _route(codes=[STALE])
        self.assertEqual("retry", outcome.status)

    def test_a_stale_decision_produces_no_gap(self):
        """Nothing was refused and nothing misunderstood."""

        self.assertIsNone(_route(codes=[STALE]).gap)

    def test_a_correctable_denial_produces_a_gap(self):
        """Arc built the request wrong; that is teachable."""

        gap = _route(codes=[CORRECTABLE]).gap
        self.assertIsNotNone(gap)
        self.assertEqual("open", gap.status)

    def test_retries_are_bounded_then_escalate(self):
        outcome = _route(_attempt(attempt=DEFAULT_MAX_ATTEMPTS), codes=[CORRECTABLE])
        self.assertEqual("escalated", outcome.status)
        self.assertIn("unresolved after", outcome.note)

    def test_a_single_attempt_budget_escalates_immediately(self):
        outcome = _route(codes=[CORRECTABLE], max_attempts=1)
        self.assertEqual("escalated", outcome.status)

    def test_an_invalid_attempt_budget_is_refused(self):
        for max_attempts in (0, -1, True, "3"):
            with self.subTest(max_attempts=max_attempts):
                with self.assertRaises(TaskOutcomeError):
                    _route(codes=[CORRECTABLE], max_attempts=max_attempts)


class EscalationTests(unittest.TestCase):
    """Handing the task upward, and what travels with it."""

    def test_an_escalatable_denial_goes_to_the_next_rung(self):
        outcome = _route(codes=[ESCALATABLE])
        self.assertEqual("escalated", outcome.status)
        self.assertEqual(2, outcome.next_attempt.tier)

    def test_the_escalation_record_names_both_rungs(self):
        record = _route(codes=[ESCALATABLE]).escalation
        self.assertEqual("system manager", record["from"]["role"])
        self.assertEqual("executive manager", record["to"]["role"])

    def test_the_gap_records_which_rung_received_it(self):
        gap = _route(codes=[ESCALATABLE]).gap
        self.assertEqual(2, gap.escalated_to_tier)

    def test_a_new_rung_starts_with_a_full_attempt_budget(self):
        """Charging it for the previous rung's tries would arrive exhausted."""

        outcome = _route(_attempt(attempt=DEFAULT_MAX_ATTEMPTS), codes=[ESCALATABLE])
        self.assertEqual(1, outcome.next_attempt.attempt)

    def test_at_the_last_rung_the_task_waits_rather_than_moving(self):
        ladder = default_ladder()
        outcome = _route(
            _attempt(tier=len(ladder.tiers)), codes=[ESCALATABLE], ladder=ladder
        )
        self.assertEqual("blocked", outcome.status)
        self.assertIn("cannot defer", outcome.note)

    def test_the_final_block_still_carries_the_gap(self):
        """The thing to teach does not disappear because a person is needed."""

        ladder = default_ladder()
        outcome = _route(
            _attempt(tier=len(ladder.tiers)), codes=[ESCALATABLE], ladder=ladder
        )
        self.assertIsNotNone(outcome.gap)


class LadderIntegrationTests(unittest.TestCase):
    """The seam must respect whatever ladder the customer configured."""

    def _flat_ladder(self) -> EscalationLadder:
        """Equal authority between rungs - the shape the strict rule forbade."""

        return EscalationLadder(
            tiers=(
                EscalationTier(
                    tier=1, role="system manager", kind="system_manager",
                    may_permit=frozenset({"sop_work"}),
                ),
                EscalationTier(
                    tier=2, role="GM", kind="executive",
                    may_permit=frozenset({"sop_work"}),
                ),
                EscalationTier(
                    tier=3, role="owner", kind="human",
                    may_permit=frozenset({UNBOUNDED_PERMIT_SCOPE}),
                ),
            )
        )

    def test_escalation_follows_the_configured_roles(self):
        outcome = _route(codes=[ESCALATABLE], ladder=self._flat_ladder())
        self.assertEqual("GM", outcome.escalation["to"]["role"])

    def test_a_longer_ladder_takes_more_hops_to_reach_a_person(self):
        ladder = self._flat_ladder()
        first = _route(codes=[ESCALATABLE], ladder=ladder)
        second = _route(first.next_attempt, codes=[ESCALATABLE], ladder=ladder)
        self.assertEqual("escalated", second.status)
        self.assertTrue(second.escalation["terminal"])

    def test_routing_without_a_ladder_is_refused(self):
        with self.assertRaises(TaskOutcomeError):
            route_task_outcome(
                _attempt(), performed=False, reason_codes=[ESCALATABLE], ladder=None
            )


class AttemptTests(unittest.TestCase):
    """Ordinary validation of the attempt record."""

    def test_a_blank_identifier_is_refused(self):
        for field in ("task_ref", "capability"):
            with self.subTest(field=field):
                with self.assertRaises(TaskOutcomeError):
                    _attempt(**{field: "  "})

    def test_a_non_positive_attempt_or_tier_is_refused(self):
        for field in ("attempt", "tier"):
            for value in (0, -1, True):
                with self.subTest(field=field, value=value):
                    with self.assertRaises(TaskOutcomeError):
                        _attempt(**{field: value})

    def test_an_unknown_outcome_status_is_refused(self):
        with self.assertRaises(TaskOutcomeError):
            TaskOutcome(task_ref="task:1", status="probably_fine")


class WalkToRestTests(unittest.TestCase):
    """The whole journey, not only one step of it."""

    def test_a_task_corrected_on_the_second_try_completes(self):
        outcomes = run_to_rest(
            _attempt(),
            answers=[(False, [CORRECTABLE]), (True, [])],
            ladder=default_ladder(),
        )
        self.assertEqual(["retry", "completed"], [o.status for o in outcomes])

    def test_a_persistent_correctable_failure_climbs_then_waits(self):
        """Three tries, escalate, three more, escalate, then a person."""

        outcomes = run_to_rest(
            _attempt(),
            answers=[(False, [CORRECTABLE])] * 9,
            ladder=default_ladder(),
        )
        self.assertEqual("blocked", outcomes[-1].status)
        self.assertIn("cannot defer", outcomes[-1].note)
        self.assertEqual(3, sum(1 for o in outcomes if o.status == "escalated") + 1)

    def test_a_forbidden_denial_ends_the_walk_at_once(self):
        outcomes = run_to_rest(
            _attempt(),
            answers=[(False, [FORBIDDEN]), (True, [])],
            ladder=default_ladder(),
        )
        self.assertEqual(1, len(outcomes))
        self.assertEqual("blocked", outcomes[0].status)

    def test_the_walk_never_invents_an_attempt_it_has_no_answer_for(self):
        outcomes = run_to_rest(
            _attempt(), answers=[(False, [CORRECTABLE])], ladder=default_ladder()
        )
        self.assertEqual(1, len(outcomes))


class EvidenceTests(unittest.TestCase):
    """The outcome is a record, and has to render."""

    def test_an_escalated_outcome_renders_every_part(self):
        rendered = _route(codes=[ESCALATABLE]).to_dict()
        self.assertEqual("task_outcome", rendered["record_type"])
        self.assertEqual("escalated", rendered["status"])
        self.assertIsNotNone(rendered["sop_gap"])
        self.assertIsNotNone(rendered["escalation"])
        self.assertEqual(2, rendered["next_attempt"]["tier"])

    def test_a_completed_outcome_renders_without_a_gap(self):
        rendered = _route(performed=True).to_dict()
        self.assertIsNone(rendered["sop_gap"])
        self.assertIsNone(rendered["escalation"])

    def test_reason_codes_are_sorted_for_stable_evidence(self):
        rendered = _route(codes=["b_code", "a_code"]).to_dict()
        self.assertEqual(["a_code", "b_code"], rendered["reason_codes"])


if __name__ == "__main__":
    unittest.main()
