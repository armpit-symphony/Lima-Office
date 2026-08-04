"""What happens to a queued task after the governed path answers.

This is the seam. A task manager puts jobs in a queue; Arc bot works them, and
returns to tasks that needed more information before it can finish them. Each
attempt goes through the real governed path, and comes back either done or
denied with reason codes. This module decides what that means:

* finish the task,
* correct the request and try again,
* hand it to the next rung,
* or stop.

It is deliberately pure. Nothing here starts a process, opens a socket or
touches a queue - it takes an attempt and a result and returns what should
happen, so the decision can be tested without a lab and cannot differ between
the lab and production.

The three pieces it joins were built separately and meet here for the first
time: the denial disposition decides the class of failure, the escalation
ladder decides who sees it next, and the SOP gap records what Arc would need
to learn to not need anyone next time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from lima_office.runtime.errors import PolicyDenyError
from lima_office.runtime.escalation import EscalationLadder, escalation_record
from lima_office.runtime.sop import SopGap, gap_from_denial
from lima_office.runtime.taxonomy import denial_disposition_for_set


# completed - Arc finished it at this rung, with nobody else involved.
# retry     - the same rung tries again; the request or the decision was at
#             fault, not the authority.
# escalated - the next rung up now owns it.
# blocked   - nothing further will be attempted automatically.
TASK_OUTCOME_STATUSES = frozenset({"completed", "retry", "escalated", "blocked"})

# A denial that keeps arriving is not resolved by arriving again. The cap is
# small on purpose: retrying is only ever correcting a malformed request or
# refreshing an aged decision, and neither should need many goes.
DEFAULT_MAX_ATTEMPTS = 3


class TaskOutcomeError(PolicyDenyError):
    """The attempt or result is not something an outcome can be derived from."""


@dataclass(frozen=True)
class TaskAttempt:
    """One pass at a task, at one rung of the ladder."""

    task_ref: str
    capability: str
    attempt: int = 1
    tier: int = 1

    def __post_init__(self) -> None:
        for name in ("task_ref", "capability"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise TaskOutcomeError(f"{name} must be a non-empty string")
        for name in ("attempt", "tier"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise TaskOutcomeError(f"{name} must be 1 or greater")

    def next_try(self) -> "TaskAttempt":
        return TaskAttempt(
            task_ref=self.task_ref,
            capability=self.capability,
            attempt=self.attempt + 1,
            tier=self.tier,
        )

    def at_tier(self, tier: int) -> "TaskAttempt":
        """The same work, handed upward. The attempt count restarts.

        A new rung has not tried yet, and charging it for the previous rung's
        attempts would let a task arrive already out of retries.
        """

        return TaskAttempt(
            task_ref=self.task_ref,
            capability=self.capability,
            attempt=1,
            tier=tier,
        )


@dataclass(frozen=True)
class TaskOutcome:
    """What should happen to the task next, and what to record about it."""

    task_ref: str
    status: str
    reason_codes: tuple[str, ...] = ()
    disposition: str | None = None
    gap: SopGap | None = None
    escalation: Mapping[str, Any] | None = None
    next_attempt: TaskAttempt | None = None
    note: str = ""

    def __post_init__(self) -> None:
        if self.status not in TASK_OUTCOME_STATUSES:
            raise TaskOutcomeError(
                f"unknown outcome status {self.status!r}; expected one of "
                f"{sorted(TASK_OUTCOME_STATUSES)}"
            )

    @property
    def is_terminal(self) -> bool:
        return self.status in {"completed", "blocked"}

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_type": "task_outcome",
            "task_ref": self.task_ref,
            "status": self.status,
            "reason_codes": sorted(self.reason_codes),
            "disposition": self.disposition,
            "sop_gap": self.gap.to_dict() if self.gap is not None else None,
            "escalation": dict(self.escalation) if self.escalation else None,
            "next_attempt": (
                {
                    "attempt": self.next_attempt.attempt,
                    "tier": self.next_attempt.tier,
                }
                if self.next_attempt is not None
                else None
            ),
            "note": self.note,
        }


def route_task_outcome(
    attempt: TaskAttempt,
    *,
    performed: bool,
    reason_codes: Sequence[str] = (),
    ladder: EscalationLadder,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    metadata: Mapping[str, Any] | None = None,
) -> TaskOutcome:
    """Decide what happens to a task after one governed attempt.

    ``performed`` is the governed path's own answer about whether the work
    happened. It is taken at face value only when no reason codes arrived with
    it: a result claiming both is contradictory, and the safe reading of a
    contradiction is the denial.
    """

    if not isinstance(attempt, TaskAttempt):
        raise TaskOutcomeError("attempt must be a TaskAttempt")
    if not isinstance(ladder, EscalationLadder):
        raise TaskOutcomeError("routing an outcome needs the escalation ladder")
    if not isinstance(max_attempts, int) or isinstance(max_attempts, bool):
        raise TaskOutcomeError("max_attempts must be an integer")
    if max_attempts < 1:
        raise TaskOutcomeError("max_attempts must be 1 or greater")

    codes = tuple(str(code) for code in reason_codes)

    if performed and not codes:
        return TaskOutcome(
            task_ref=attempt.task_ref,
            status="completed",
            note=f"finished at tier {attempt.tier} without escalation",
        )

    if performed and codes:
        # Neither half can be trusted, so the denial wins. Reporting this as
        # done would put work into the world that the record says was refused.
        return TaskOutcome(
            task_ref=attempt.task_ref,
            status="blocked",
            reason_codes=codes,
            disposition=denial_disposition_for_set(codes),
            note=(
                "result claimed the work was performed and denied it at the "
                "same time; treated as denied"
            ),
        )

    if not codes:
        # Nothing happened and nothing said why. There is nothing to correct
        # and nothing to teach, so it stops rather than looping.
        return TaskOutcome(
            task_ref=attempt.task_ref,
            status="blocked",
            note="the attempt did not complete and gave no reason",
        )

    disposition = denial_disposition_for_set(codes)
    gap = gap_from_denial(
        task_ref=attempt.task_ref,
        capability=attempt.capability,
        reason_codes=codes,
        escalated_to_tier=None,
        metadata=metadata,
    )

    if disposition == "forbidden":
        # Terminal by construction: no rung may permit it, so handing it
        # upward would only be asking a more powerful authority the same
        # question. gap_from_denial already returned None for these.
        return TaskOutcome(
            task_ref=attempt.task_ref,
            status="blocked",
            reason_codes=codes,
            disposition=disposition,
            note="no rung may permit this; not escalated and not retried",
        )

    if disposition in {"correctable", "retry_with_fresh_decision"}:
        if attempt.attempt < max_attempts:
            return TaskOutcome(
                task_ref=attempt.task_ref,
                status="retry",
                reason_codes=codes,
                disposition=disposition,
                gap=gap,
                next_attempt=attempt.next_try(),
                note=(
                    f"attempt {attempt.attempt} of {max_attempts} at tier "
                    f"{attempt.tier}"
                ),
            )
        return _escalate(
            attempt,
            codes=codes,
            disposition=disposition,
            gap=gap,
            ladder=ladder,
            note=f"unresolved after {max_attempts} attempts at tier {attempt.tier}",
        )

    return _escalate(
        attempt,
        codes=codes,
        disposition=disposition,
        gap=gap,
        ladder=ladder,
        note="this rung may not permit it",
    )


def _escalate(
    attempt: TaskAttempt,
    *,
    codes: tuple[str, ...],
    disposition: str,
    gap: SopGap | None,
    ladder: EscalationLadder,
    note: str,
) -> TaskOutcome:
    """Hand the task to the next rung, or stop if there is none above."""

    if not ladder.may_defer(attempt.tier):
        # The last rung decides. It cannot pass the task on, so the task waits
        # for the person rather than moving anywhere.
        return TaskOutcome(
            task_ref=attempt.task_ref,
            status="blocked",
            reason_codes=codes,
            disposition=disposition,
            gap=gap,
            note=(
                f"{note}; awaiting {ladder.terminal_tier.role}, which cannot "
                "defer further"
            ),
        )

    record = escalation_record(ladder, from_tier=attempt.tier, reason_codes=codes)
    destination = ladder.next_tier(attempt.tier)
    escalated_gap = gap
    if gap is not None:
        escalated_gap = SopGap(
            gap_id=gap.gap_id,
            task_ref=gap.task_ref,
            capability=gap.capability,
            reason_codes=gap.reason_codes,
            disposition=gap.disposition,
            source=gap.source,
            status=gap.status,
            escalated_to_tier=destination.tier,
            resolved_by_role=gap.resolved_by_role,
            instruction=gap.instruction,
            metadata=gap.metadata,
        )
    return TaskOutcome(
        task_ref=attempt.task_ref,
        status="escalated",
        reason_codes=codes,
        disposition=disposition,
        gap=escalated_gap,
        escalation=record,
        next_attempt=attempt.at_tier(destination.tier),
        note=f"{note}; handed to {destination.role}",
    )


def run_to_rest(
    attempt: TaskAttempt,
    *,
    answers: Iterable[tuple[bool, Sequence[str]]],
    ladder: EscalationLadder,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
) -> list[TaskOutcome]:
    """Route a whole sequence of attempts until the task stops moving.

    ``answers`` supplies what the governed path returned for each successive
    attempt. Present so the walk from first attempt to rest can be exercised
    as one thing, rather than only a step at a time.

    Stops when an outcome is terminal or the answers run out; it never invents
    an attempt it was not given a result for.
    """

    outcomes: list[TaskOutcome] = []
    current = attempt
    for performed, codes in answers:
        outcome = route_task_outcome(
            current,
            performed=performed,
            reason_codes=codes,
            ladder=ladder,
            max_attempts=max_attempts,
        )
        outcomes.append(outcome)
        if outcome.is_terminal or outcome.next_attempt is None:
            break
        current = outcome.next_attempt
    return outcomes
