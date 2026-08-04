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
    DENIAL_DISPOSITIONS,
    denial_disposition_for_set,
)


# Where a gap came from. Both shapes are the same record because both feed the
# same training loop: one observed by the system, one written by a person.
GAP_SOURCES = frozenset({"escalation", "operator_authored"})

# Authored SOP has no denial behind it, so it has no denial disposition. The
# value is named here rather than left as a bare string, so a caller switching
# on disposition has a set to enumerate.
NOT_APPLICABLE_DISPOSITION = "not_applicable"
GAP_DISPOSITIONS = DENIAL_DISPOSITIONS | {NOT_APPLICABLE_DISPOSITION}

# Metadata carries references, never material. A gap says what was attempted
# and why it stopped; the document, prompt, payload and output stay where they
# already live under their own controls.
#
# Enforced rather than documented, because a free-form mapping is exactly where
# a body ends up when someone is debugging in a hurry.
_MATERIAL_KEY_FRAGMENTS = (
    "payload",
    "content",
    "body",
    "prompt",
    "output",
    "transcript",
    "message",
    "text",
    "excerpt",
    "snippet",
)

# Long enough for a ref, an id, a path or a short label. Not long enough to be
# somewhere a document ends up by accident.
MAX_METADATA_VALUE_LENGTH = 200

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


def validate_gap_metadata(metadata: Any) -> dict[str, Any]:
    """Return metadata that carries references only, or refuse it.

    The record's whole claim is that it holds what was attempted and why it
    stopped, never the material. A free-form mapping is where that claim goes
    to die, so the boundary is checked rather than asserted in a docstring.
    """

    if metadata is None:
        return {}
    if not isinstance(metadata, Mapping):
        raise SopGapError("gap metadata must be an object")

    checked: dict[str, Any] = {}
    for key, value in metadata.items():
        if not isinstance(key, str) or not key.strip():
            raise SopGapError("gap metadata keys must be non-empty strings")
        folded = key.casefold()
        for fragment in _MATERIAL_KEY_FRAGMENTS:
            if fragment in folded:
                raise SopGapError(
                    f"gap metadata key {key!r} looks like material; a gap "
                    "records references, not the document, prompt or output"
                )
        if isinstance(value, bool) or value is None:
            checked[key] = value
            continue
        if isinstance(value, (int, float)):
            checked[key] = value
            continue
        if isinstance(value, str):
            if len(value) > MAX_METADATA_VALUE_LENGTH:
                raise SopGapError(
                    f"gap metadata {key!r} is {len(value)} characters; values "
                    f"are capped at {MAX_METADATA_VALUE_LENGTH} so a body "
                    "cannot be stored here"
                )
            checked[key] = value
            continue
        raise SopGapError(
            f"gap metadata {key!r} must be a string, number, boolean or null; "
            "nested structures can hide material"
        )
    return checked


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
        if self.disposition not in GAP_DISPOSITIONS:
            raise SopGapError(
                f"unknown gap disposition {self.disposition!r}; expected one of "
                f"{sorted(GAP_DISPOSITIONS)}"
            )
        object.__setattr__(self, "metadata", validate_gap_metadata(self.metadata))
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

    def with_retirement(self, *, retired_by_role: str, demonstrated_by: str) -> "SopGap":
        """Close the loop: Arc now does this job without the failsafe.

        Only an instructed gap may retire. Retiring an open one would claim a
        job was learned when nothing was ever taught, and the autonomy rate
        would improve without anything having improved.

        ``demonstrated_by`` is the reference to the evidence that Arc did it
        alone, so a retirement can be checked rather than taken on trust.
        """

        if self.status != "instructed":
            raise SopGapError(
                f"only an instructed gap may retire; this one is {self.status!r} "
                "and nothing has been taught yet"
            )
        if not isinstance(retired_by_role, str) or not retired_by_role.strip():
            raise SopGapError("record who retired the gap")
        if not isinstance(demonstrated_by, str) or not demonstrated_by.strip():
            raise SopGapError(
                "a retirement needs the evidence reference showing Arc did it alone"
            )
        metadata = dict(self.metadata)
        metadata["retirement_evidence_ref"] = demonstrated_by.strip()
        return SopGap(
            gap_id=self.gap_id,
            task_ref=self.task_ref,
            capability=self.capability,
            reason_codes=self.reason_codes,
            disposition=self.disposition,
            source=self.source,
            status="retired",
            escalated_to_tier=self.escalated_to_tier,
            resolved_by_role=retired_by_role.strip(),
            instruction=self.instruction,
            metadata=metadata,
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
        # Passed through rather than coerced: dict() on a non-mapping raises
        # TypeError, which would escape instead of the SopGapError the caller
        # is prepared for.
        metadata=metadata,
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
        disposition=NOT_APPLICABLE_DISPOSITION,
        source="operator_authored",
        status="instructed",
        resolved_by_role=authored_by_role,
        instruction=instruction.strip(),
        metadata=metadata,
    )


def training_progress(
    *,
    completed_alone: int,
    stopped_short: int,
    gaps: Iterable[SopGap],
) -> dict[str, Any]:
    """How close Arc is to doing the job on its own.

    Two different quantities, kept separate on purpose:

    * ``stopped_short`` counts **occurrences** - every time Arc could not
      finish alone.
    * ``gaps`` are **distinct** things to teach. Ids are derived, so twenty
      identical failures collapse to one gap.

    An earlier signature took only ``gaps`` and inferred attempts from its
    length. That is right if the caller passes occurrences and quietly wrong if
    it passes a gap store - which is the natural thing to pass, given ids
    deduplicate. Twenty failures and eight successes would have reported 89%
    autonomy instead of 29%. The counts are now separate so neither reading is
    silent.

    ``autonomy_rate`` is the share of attempts Arc finished with nobody else
    involved. Training is working when it rises. An SOP written but never
    retiring anything shows up as instructed gaps that never fall: instruction
    written is not job learned.

    Counts only. Nothing here reads an instruction body.
    """

    for name, value in (
        ("completed_alone", completed_alone),
        ("stopped_short", stopped_short),
    ):
        if not isinstance(value, int) or isinstance(value, bool):
            raise SopGapError(f"{name} must be an integer")
        if value < 0:
            raise SopGapError(f"{name} cannot be negative")

    observed = list(gaps)
    distinct = {gap.gap_id for gap in observed}
    if stopped_short < len(distinct):
        raise SopGapError(
            f"stopped_short is {stopped_short} but there are {len(distinct)} "
            "distinct gaps; every gap came from at least one occurrence"
        )

    attempts = completed_alone + stopped_short
    return {
        "record_type": "sop_training_progress",
        "completed_alone": completed_alone,
        "stopped_short": stopped_short,
        "gap_count": len(distinct),
        "open_gaps": sum(1 for gap in observed if gap.status == "open"),
        "instructed_gaps": sum(1 for gap in observed if gap.status == "instructed"),
        "retired_gaps": sum(1 for gap in observed if gap.status == "retired"),
        "attempts": attempts,
        "autonomy_rate": (completed_alone / attempts) if attempts else None,
    }
