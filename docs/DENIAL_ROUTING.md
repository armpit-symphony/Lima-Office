# What a shell may do about a denial

A denied request is not one thing. Some denials mean the shell got the request
wrong. Some mean an authority refused. Treating them alike produces either a
system that grinds against its own gates, or one that escalates an attack.

This document defines the four dispositions, and the boundary between what a
customer configures and what the system owns.

## The escalation ladder is automated

In the LIMA office ecosystem, Arc bot, the supervisor role, manager and GM are
all automated. **Human is the terminal rung and the only one that cannot
defer**, which makes it the sole guarantee that an escalation ever stops.

That changes the safety analysis. When the rungs are machines, escalating a
policy denial to a higher automated authority is **authority shopping** —
structurally the same failure as automatically retrying, with a different
decider. If Guardian refuses and an automated manager can approve, the ladder
has become a route around Guardian, and "LIMA decides, shells execute" no
longer holds.

The first instinct — have the shell re-check that it has all the information
and try again — is right for exactly one class of denial and unsafe for the
rest.

## The four dispositions

| Disposition | Meaning | Behaviour |
|---|---|---|
| `forbidden` | No tier may permit it | Terminal. Never retried, never escalated. |
| `escalatable` | This authority may not permit it; a higher tier might | Enters the ladder |
| `correctable` | The request itself was inadmissible | Correct it, resubmit at the same tier |
| `retry_with_fresh_decision` | Nothing was refused; the decision aged out | Fresh decision, bounded and counted, same tier |

`retry_with_fresh_decision` is deliberately its own class rather than folded
into either neighbour. `decision_expired` is not a refusal and not a malformed
request, and recording it as either misreports what happened. Truthful evidence
is the point of the system.

## Unclassified means forbidden

`DEFAULT_DENIAL_DISPOSITION` is `forbidden`, and classifications live in
`DENIAL_DISPOSITION_OVERRIDES` rather than on each registry entry. A code
nobody has classified therefore stops.

The cost of a missing classification is a denial that halts and needs a human.
The cost of the opposite default would be a denial that loops against a gate,
or climbs the ladder carrying an injection attempt. Only one of those is
recoverable.

## Why a separate axis was necessary

The registry already carries `category`, `severity` and `fail_closed_required`.
None of them, alone or together, can drive this routing.

| Reason code | category | severity | fail_closed | Disposition |
|---|---|---|---|---|
| `connector_prompt_injection_blocked` | guardian | blocked | True | `forbidden` |
| `outbound_missing_approval` | guardian | blocked | True | `escalatable` |
| `decision_expired` | guardian | blocked | True | `retry_with_fresh_decision` |

Identical on every existing field, and they require opposite handling: one must
terminate, one must climb the ladder, one only needs a fresher decision.
`tests/test_denial_disposition.py` derives such a pair from the registry rather
than hard-coding it, so if the fields ever do become sufficient, the test says
so instead of quietly passing.

## Adversarial input terminates

`prompt_injection_suspected`, `tainted_input`,
`connector_prompt_injection_blocked` and `model_route_tainted_input_denied` are
`forbidden`, not `escalatable`.

Escalating an injection attempt walks it up to progressively higher automated
authority. Every rung is another target, and each has more power than the last.
The ladder would be an attack path.

Integrity failures — `guardian_decision_mismatch`, `decision_scope_hash_mismatch`,
`decision_revoked` — terminate for a related reason: no other authority may be
asked to bless a decision that does not match the request it was issued for.

## The most restrictive reason governs

A denial rarely carries a single reason code. `denial_disposition_for_set`
returns the most restrictive disposition present, ordered by
`DENIAL_DISPOSITION_PRECEDENCE`.

Correcting a malformed field does not dissolve a `forbidden` reason that
arrived alongside it. A denial with no stated reason at all is also
`forbidden` — an inexplicable denial is the last thing to retry.

## The configuration boundary

The ladder is customer-configurable: corporate structure and preferences,
authored through an IDE or UI. Its shape is data, not code.

| | Owns |
|---|---|
| **Customer** | Tier count, names, order, who fills each rung, routing preferences |
| **System** | Which denials may enter the ladder at all, and the structural invariants |

`may_escalate()` is the system-owned half. A customer must never be able to
configure a `forbidden` denial as escalatable, or the org-structure editor
becomes a supported way to widen an attack path.

Every deployment has at least a system manager and an Executive manager/GM,
plus the Human terminator, so ladder validation enforces a minimum ladder and
not merely a well-formed one.

## The ladder contract

`lima_office/runtime/escalation.py`. A ladder is refused at load rather than
accepted and degraded — a deployment whose escalation path cannot terminate
must fail to start.

Configuration arrives from an IDE or UI and is untrusted input like any other.
Nothing in the loader repairs a malformed ladder.

### Invariants

| Invariant | Why |
|---|---|
| Ends in a `human` tier | Every other rung is automated and may defer. Human is the only termination guarantee. |
| Exactly one terminal tier, and it is last | Two terminators, or one in the middle, means escalation can route past the person. |
| Tiers contiguous and ascending from 1 | Movement is upward only; gaps make "the rung above" ambiguous. |
| `next_tier` refuses sideways or downward moves | Monotonic movement is what makes termination structural rather than hoped for. |
| Contains `system_manager` and `executive` kinds | The floor every deployment has. |
| Each rung permits strictly more than the one below | A rung with equal authority denies for the same reason; the ladder would buy hops, not decisions. |
| Only the terminal tier may hold `*` | Unbounded authority belongs to a person, not an automated role. |
| Role labels unique, case-insensitively | Two rungs called "Manager" cannot be told apart in evidence. |

The strict-superset rule is the one that prevents escalation theatre. Without
it a customer can configure four rungs that all refuse identically, and the
only thing they have bought is three hops before a person sees the request
anyway.

### Labels and kinds

`role` is the customer's text. `kind` is what the system reasons about.

A customer may name a rung "Supervisor" — and LIMA Office already has a
Supervisor control plane that issues grants. Those are different things. The
split keeps the customer's vocabulary while leaving contracts and evidence
unambiguous, and `escalation_record()` always emits the rung and the role
together:

```json
{
  "record_type": "escalation",
  "from": {"escalation_tier": 1, "role": "Supervisor", "kind": "system_manager"},
  "to":   {"escalation_tier": 2, "role": "general manager", "kind": "executive"},
  "reason_codes": ["outbound_missing_approval"],
  "terminal": false
}
```

## Naming

"Supervisor" is both a customer-chosen role label and a LIMA Office component
— the Supervisor control plane that issues grants. They are different things.
Evidence and contracts record the rung and the role together
(`escalation_tier: 1, role: "supervisor"`) so that no log line has to be
disambiguated by context.

Two diagnostics in this stack have already blamed the wrong component:
`recon_missing_guardian_decision` blamed the Guardian authority for an
inadmissible request, and Arc's health report blamed LIMA for a retired
adapter. Both cost real time, and both were one word pointing somewhere wrong.
