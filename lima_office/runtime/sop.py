"""SOP gaps: the things Arc could not do on its own, in a teachable form.

Arc bot is fed SOP and trained in its job until it can do that job accurately
on its own. Every time it stops short, that is a fact about what it has not
been taught yet - and the system already records it, as a denial with reason
codes. This module turns those records into the training signal, and holds the
same shape for SOP an operator authors directly in the UI.

The measure of whether training is working falls out of it: the ratio of tasks
Arc completed alone to tasks it could not. That number should fall over time,
and it comes from evidence already being captured rather than from new
instrumentation.

**Not every denial is an SOP gap.** A denial Arc may be taught past is one
where Arc was wrong or where a higher rung had to decide. A denial that exists
to stop something is not a gap in Arc's training, and writing an instruction
that gets past it would be teaching Arc to defeat a control. See
``is_teachable``.

Nothing here stores a task payload, document body, prompt or model output. A
gap records what was attempted and why it stopped, never the material - the
same boundary the diagnostics surfaces keep.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from typing import Any, Iterable, Mapping, Sequence

from lima_office.runtime.errors import PolicyDenyError
from lima_office.runtime.taxonomy import (
    denial_disposition_for_set,
)


# Where a gap came from. Both shapes are the same record because both feed the
# same training loop: one observed by the system, one written by a person.
GAP_SOURCES = frozenset({"escalation", "operator_authored"})

# A gap is open until someone writes the instruction that closes it, and
# retired once Arc demonstrably does the job without it.
GAP_STATUSES = frozenset({"open", "instructed", "retired"})

# Dispositions that represent something Arc can be taught.
#
# correctable - Arc built the request wrong; an SOP can teach it the right
#   shape, and the next attempt succeeds without anyone being asked.
# escalatable - Arc was right to stop and a higher rung decided; the SOP
#   records what that rung decided so the decision can be reused.
TEACHABLE_DISPOSITIONS = frozenset({"correctable", "escalatable"})

# Deliberately absent from the above:
#
# forbidden - not a training gap. The control worked. An instruction that got
#   Arc past it would be an instruction to defeat it.
# retry_with_fresh_decision - nothing was refused and nothing was misunderstood;
#   a decision aged out. There is nothing to teach.


class SopGapError(PolicyDenyError):
    """The gap record is unusable and must not be stored."""


def is_teachable(reason_codes: Iterable[str]) -> bool:
    """Whether this denial represents something Arc may be taught past.

    This is the safety boundary of the training loop. A forbidden denial must
    never become a gap awaiting an instruction, because the instruction that
    closed it would be an instruction to get past a control that was working.
    """

    codes = list(reason_codes)
    if not codes:
        return False
    return denial_disposition_for_set(codes) in TEACHABLE_DISPOSITIONS


@dataclass(frozen=True)
class SopGap:
    """One thing Arc could not do alone, and what it would need to learn."""

    gap_id: str
    task_ref: str
    capability: str
    reason_codes: tuple[str, ...]
    disposition: str
    source: str
    status: str = "open"
    escalated_to_tier: int | None = None
    resolved_by_role: str | None = None
    instruction: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("gap_id", "task_ref", "capability"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise SopGapError(f"{name} must be a non-empty string")
        if self.source not in GAP_SOURCES:
            raise SopGapError(
                f"unknown gap source {self.source!r}; expected one of "
                f"{sorted(GAP_SOURCES)}"
            )
        if self.status not in GAP_STATUSES:
            raise SopGapError(
                f"unknown gap status {self.status!r}; expected one of "
                f"{sorted(GAP_STATUSES)}"
            )
        if not isinstance(self.reason_codes, tuple):
            raise SopGapError("reason_codes must be a tuple")
        if self.source == "escalation" and not self.reason_codes:
            raise SopGapError(
                "a gap observed from a denial must record why it stopped"
            )
        if self.escalated_to_tier is not None:
            if (
                not isinstance(self.escalated_to_tier, int)
                or isinstance(self.escalated_to_tier, bool)
                or self.escalated_to_tier < 1
            ):
                raise SopGapError("escalated_to_tier must be a tier number")
        if self.status != "open" and not (self.instruction or "").strip():
            raise SopGapError(
                f"a gap marked {self.status!r} needs the instruction that closed it"
            )
        if self.reason_codes and not is_teachable(self.reason_codes):
            raise SopGapError(
                "this denial is not a training gap: "
                f"{sorted(self.reason_codes)} resolves to {self.disposition!r}, "
                "and an instruction that got past it would defeat a control"
            )

    def with_instruction(self, instruction: str, *, resolved_by_role: str) -> "SopGap":
        """Record the SOP that closes this gap.

        The instruction may come from an operator typing it in the UI or from a
        rung that decided the escalation. Either way it is the same field, so
        the training loop does not care which happened.
        """

        if not isinstance(instruction, str) or not instruction.strip():
            raise SopGapError("an instruction must be non-empty")
        if not isinstance(resolved_by_role, str) or not resolved_by_role.strip():
            raise SopGapError("record who supplied the instruction")
        return SopGap(
            gap_id=self.gap_id,
            task_ref=self.task_ref,
            capability=self.capability,
            reason_codes=self.reason_codes,
            disposition=self.disposition,
            source=self.source,
            status="instructed",
            escalated_to_tier=self.escalated_to_tier,
            resolved_by_role=resolved_by_role.strip(),
            instruction=instruction.strip(),
            metadata=dict(self.metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_type": "sop_gap",
            "gap_id": self.gap_id,
            "task_ref": self.task_ref,
            "capability": self.capability,
            "reason_codes": sorted(self.reason_codes),
            "disposition": self.disposition,
            "source": self.source,
            "status": self.status,
            "escalated_to_tier": self.escalated_to_tier,
            "resolved_by_role": self.resolved_by_role,
            "instruction": self.instruction,
            "metadata": dict(self.metadata),
        }


def gap_id_for(*, task_ref: str, capability: str, reason_codes: Iterable[str]) -> str:
    """A stable id for one kind of gap.

    Derived rather than random so the same shortfall hitting the same task and
    capability collapses to one gap instead of accumulating duplicates. Arc
    failing the same way twenty times is one thing to teach, not twenty.
    """

    codes = ",".join(sorted(str(code) for code in reason_codes))
    digest = hashlib.sha256(
        f"{task_ref}\x1f{capability}\x1f{codes}".encode("utf-8")
    ).hexdigest()[:16]
    return f"sop-gap:{digest}"


def gap_from_denial(
    *,
    task_ref: str,
    capability: str,
    reason_codes: Sequence[str],
    escalated_to_tier: int | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> SopGap | None:
    """Turn a denial into a training gap, or return None if it is not one.

    Returning None rather than raising is deliberate: most denials are not
    training gaps, and a caller walking an evidence stream should not have to
    pre-filter to avoid exceptions on the ordinary case.
    """

    codes = tuple(str(code) for code in reason_codes)
    if not is_teachable(codes):
        return None
    return SopGap(
        gap_id=gap_id_for(
            task_ref=task_ref, capability=capability, reason_codes=codes
        ),
        task_ref=task_ref,
        capability=capability,
        reason_codes=codes,
        disposition=denial_disposition_for_set(codes),
        source="escalation",
        escalated_to_tier=escalated_to_tier,
        metadata=dict(metadata or {}),
    )


def operator_authored_gap(
    *,
    task_ref: str,
    capability: str,
    instruction: str,
    authored_by_role: str,
    metadata: Mapping[str, Any] | None = None,
) -> SopGap:
    """SOP entered directly, rather than observed from a denial.

    The UI offers this so an operator can teach Arc a job before it fails at
    it, instead of only afterwards. It carries no reason codes because nothing
    was denied - which is also why the teachability check does not apply.
    """

    if not isinstance(instruction, str) or not instruction.strip():
        raise SopGapError("authored SOP needs an instruction")
    return SopGap(
        gap_id=gap_id_for(task_ref=task_ref, capability=capability, reason_codes=()),
        task_ref=task_ref,
        capability=capability,
        reason_codes=(),
        disposition="not_applicable",
        source="operator_authored",
        status="instructed",
        resolved_by_role=authored_by_role,
        instruction=instruction.strip(),
        metadata=dict(metadata or {}),
    )


def training_progress(
    *,
    completed_alone: int,
    gaps: Iterable[SopGap],
) -> dict[str, Any]:
    """How close Arc is to doing the job on its own.

    ``autonomy_rate`` is the share of attempts Arc finished without anyone
    else being involved. It is the number to watch: training is working when
    it rises, and an SOP that was written but never retired a gap shows up as
    instructed gaps that never fall.

    Counts only, deliberately. Nothing here reads an instruction body.
    """

    if not isinstance(completed_alone, int) or isinstance(completed_alone, bool):
        raise SopGapError("completed_alone must be an integer")
    if completed_alone < 0:
        raise SopGapError("completed_alone cannot be negative")

    observed = [gap for gap in gaps]
    open_gaps = sum(1 for gap in observed if gap.status == "open")
    instructed = sum(1 for gap in observed if gap.status == "instructed")
    retired = sum(1 for gap in observed if gap.status == "retired")
    attempts = completed_alone + len(observed)
    return {
        "record_type": "sop_training_progress",
        "completed_alone": completed_alone,
        "gap_count": len(observed),
        "open_gaps": open_gaps,
        "instructed_gaps": instructed,
        "retired_gaps": retired,
        "attempts": attempts,
        "autonomy_rate": (completed_alone / attempts) if attempts else None,
    }
