"""The escalation ladder: customer-shaped, system-constrained.

A denial that may not be answered where it arose climbs a ladder of
authorities. In the LIMA office ecosystem every rung below the last is
automated - Arc bot, the supervisor role, manager, GM - and **Human is the
only rung that cannot defer**. Human is therefore the sole guarantee that an
escalation terminates, and that guarantee has to be structural rather than
conventional.

The ladder's shape is customer configuration, authored through an IDE or UI:
how many tiers, what they are called, who fills them. Its invariants are not.
A ladder that violates them is refused at load, the way
``GovernedDecision.__post_init__`` refuses an execution flag, rather than being
accepted and degraded.

Which denials may climb the ladder at all is a separate, system-owned
question. See ``taxonomy.may_escalate`` and docs/DENIAL_ROUTING.md.

Role labels are customer text; ``kind`` is what the system reasons about. That
split matters here specifically: "supervisor" is already a LIMA Office
component - the Supervisor control plane that issues grants - and a customer
may also name a rung "Supervisor". They are different things, and no log line
should have to be disambiguated by context.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from lima_office.runtime.errors import PolicyDenyError


# What the system understands a rung to be, independent of what it is called.
TIER_KINDS = frozenset(
    {
        # An automated authority with a bounded permit scope.
        "automated",
        # The minimum operational authority every deployment must have.
        "system_manager",
        # The minimum senior authority every deployment must have.
        "executive",
        # A person. Terminal: cannot defer, so escalation stops here.
        "human",
    }
)

# Kinds every ladder must contain, whatever the customer calls them.
REQUIRED_TIER_KINDS = frozenset({"system_manager", "executive", "human"})

# The only kind permitted to terminate, and it must.
TERMINAL_TIER_KIND = "human"

# A permit scope meaning "no bound". Reserved for the terminal rung: a person
# is not constrained by a declared action-class list.
UNBOUNDED_PERMIT_SCOPE = "*"


class EscalationLadderError(PolicyDenyError):
    """The configured ladder is unusable and must not be loaded."""


@dataclass(frozen=True)
class EscalationTier:
    """One rung. ``role`` is the customer's label; ``kind`` is the contract."""

    tier: int
    role: str
    kind: str
    may_permit: frozenset[str]

    def __post_init__(self) -> None:
        if not isinstance(self.tier, int) or isinstance(self.tier, bool):
            raise EscalationLadderError("tier must be an integer")
        if self.tier < 1:
            raise EscalationLadderError(f"tier must be 1 or greater, got {self.tier}")
        if not isinstance(self.role, str) or not self.role.strip():
            raise EscalationLadderError(f"tier {self.tier} needs a non-empty role label")
        if self.kind not in TIER_KINDS:
            raise EscalationLadderError(
                f"tier {self.tier} has unknown kind {self.kind!r}; "
                f"expected one of {sorted(TIER_KINDS)}"
            )
        if not isinstance(self.may_permit, frozenset) or not self.may_permit:
            raise EscalationLadderError(
                f"tier {self.tier} must declare what it may permit"
            )
        if self.is_terminal and self.may_permit != frozenset({UNBOUNDED_PERMIT_SCOPE}):
            raise EscalationLadderError(
                "the terminal tier's permit scope is unbounded; declare "
                f"{UNBOUNDED_PERMIT_SCOPE!r}"
            )
        if not self.is_terminal and UNBOUNDED_PERMIT_SCOPE in self.may_permit:
            raise EscalationLadderError(
                f"tier {self.tier} is automated and may not hold an unbounded "
                "permit scope"
            )

    @property
    def is_terminal(self) -> bool:
        return self.kind == TERMINAL_TIER_KIND

    @property
    def may_defer(self) -> bool:
        """Only a person cannot pass the decision upward."""

        return not self.is_terminal

    def permits(self, action_class: str) -> bool:
        if UNBOUNDED_PERMIT_SCOPE in self.may_permit:
            return True
        return action_class in self.may_permit

    def to_dict(self) -> dict[str, Any]:
        """Evidence shape. Tier and role travel together, always."""

        return {
            "escalation_tier": self.tier,
            "role": self.role,
            "kind": self.kind,
            "may_defer": self.may_defer,
            "may_permit": sorted(self.may_permit),
        }


@dataclass(frozen=True)
class EscalationLadder:
    """An ordered ladder that is refused unless it can actually terminate."""

    tiers: tuple[EscalationTier, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.tiers:
            raise EscalationLadderError("a ladder needs at least one tier")

        expected = list(range(1, len(self.tiers) + 1))
        actual = [tier.tier for tier in self.tiers]
        if actual != expected:
            raise EscalationLadderError(
                f"tiers must be contiguous and ascending from 1, got {actual}"
            )

        roles = [tier.role.strip().casefold() for tier in self.tiers]
        if len(set(roles)) != len(roles):
            raise EscalationLadderError("two tiers share a role label")

        terminal = [tier for tier in self.tiers if tier.is_terminal]
        if not terminal:
            raise EscalationLadderError(
                "a ladder must end in a human tier; without one an escalation "
                "between automated authorities never terminates"
            )
        if len(terminal) > 1:
            raise EscalationLadderError("a ladder may have only one terminal tier")
        if not self.tiers[-1].is_terminal:
            raise EscalationLadderError(
                f"the human tier must be last, found it at tier "
                f"{terminal[0].tier} of {len(self.tiers)}"
            )

        present = {tier.kind for tier in self.tiers}
        missing = REQUIRED_TIER_KINDS - present
        if missing:
            raise EscalationLadderError(
                "every deployment needs at least a system manager, an "
                f"executive, and a human tier; missing {sorted(missing)}"
            )

        # Each rung must be able to decide something the one below could not.
        # Otherwise it denies for the same reason and the ladder buys nothing
        # but hops before a person sees it anyway.
        for lower, upper in zip(self.tiers, self.tiers[1:]):
            if upper.is_terminal:
                continue
            if not upper.may_permit > lower.may_permit:
                raise EscalationLadderError(
                    f"tier {upper.tier} ({upper.role}) must permit strictly more "
                    f"than tier {lower.tier} ({lower.role}); as configured it "
                    "would deny for the same reason"
                )

    @property
    def terminal_tier(self) -> EscalationTier:
        return self.tiers[-1]

    def tier(self, number: int) -> EscalationTier:
        for candidate in self.tiers:
            if candidate.tier == number:
                return candidate
        raise EscalationLadderError(
            f"no tier {number}; ladder has 1..{len(self.tiers)}"
        )

    def next_tier(self, current: int) -> EscalationTier:
        """The rung above ``current``. Movement is upward only.

        Refusing to move sideways or downward is what makes the terminal tier
        a termination guarantee rather than a hope.
        """

        if not isinstance(current, int) or isinstance(current, bool):
            raise EscalationLadderError("current tier must be an integer")
        if current < 1 or current > len(self.tiers):
            raise EscalationLadderError(
                f"current tier {current} is outside the ladder (1..{len(self.tiers)})"
            )
        if current == len(self.tiers):
            raise EscalationLadderError(
                "the terminal tier cannot escalate further; it decides"
            )
        return self.tiers[current]

    def first_tier_permitting(self, action_class: str) -> EscalationTier:
        """The lowest rung with authority for this action class."""

        for candidate in self.tiers:
            if candidate.permits(action_class):
                return candidate
        return self.terminal_tier

    def to_dict(self) -> dict[str, Any]:
        return {
            "tier_count": len(self.tiers),
            "terminal_role": self.terminal_tier.role,
            "tiers": [tier.to_dict() for tier in self.tiers],
        }


def load_ladder(payload: Any) -> EscalationLadder:
    """Build a ladder from customer configuration, or refuse it.

    Configuration arrives from an IDE or UI and is therefore untrusted input
    like any other. Nothing here repairs a malformed ladder: a deployment with
    an unusable escalation path must fail to start, not start with a ladder
    that cannot terminate.
    """

    if not isinstance(payload, Mapping):
        raise EscalationLadderError("ladder configuration must be an object")
    raw_tiers = payload.get("tiers")
    if not isinstance(raw_tiers, (list, tuple)) or not raw_tiers:
        raise EscalationLadderError("ladder configuration needs a non-empty 'tiers'")

    tiers: list[EscalationTier] = []
    for index, raw in enumerate(raw_tiers, start=1):
        if not isinstance(raw, Mapping):
            raise EscalationLadderError(f"tier {index} must be an object")
        role = raw.get("role")
        kind = raw.get("kind")
        may_permit = raw.get("may_permit")
        if not isinstance(may_permit, (list, tuple, set, frozenset)):
            raise EscalationLadderError(
                f"tier {index} must declare 'may_permit' as a list"
            )
        if not all(isinstance(entry, str) and entry for entry in may_permit):
            raise EscalationLadderError(
                f"tier {index} has a non-string entry in 'may_permit'"
            )
        declared = raw.get("tier", index)
        tiers.append(
            EscalationTier(
                tier=declared if isinstance(declared, int) else index,
                role=role if isinstance(role, str) else "",
                kind=kind if isinstance(kind, str) else "",
                may_permit=frozenset(may_permit),
            )
        )
    return EscalationLadder(tiers=tuple(tiers))


def default_ladder() -> EscalationLadder:
    """The smallest ladder this system will run: the floor, and nothing more.

    Present so a deployment that has not authored a ladder still has a valid
    one rather than none, and so the floor is executable rather than prose.
    """

    return EscalationLadder(
        tiers=(
            EscalationTier(
                tier=1,
                role="system manager",
                kind="system_manager",
                may_permit=frozenset({"routine_office_work"}),
            ),
            EscalationTier(
                tier=2,
                role="executive manager",
                kind="executive",
                may_permit=frozenset({"routine_office_work", "elevated_office_work"}),
            ),
            EscalationTier(
                tier=3,
                role="human operator",
                kind="human",
                may_permit=frozenset({UNBOUNDED_PERMIT_SCOPE}),
            ),
        )
    )


def escalation_record(
    ladder: EscalationLadder,
    *,
    from_tier: int,
    reason_codes: Iterable[str],
) -> dict[str, Any]:
    """Describe one upward move, for evidence.

    Records the rung and the role together so that no reader has to work out
    whether "supervisor" meant the control plane or a person.
    """

    origin = ladder.tier(from_tier)
    destination = ladder.next_tier(from_tier)
    return {
        "record_type": "escalation",
        "from": origin.to_dict(),
        "to": destination.to_dict(),
        "reason_codes": sorted(str(code) for code in reason_codes),
        "terminal": destination.is_terminal,
    }
