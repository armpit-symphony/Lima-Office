# The task seam

A task manager puts jobs in a queue. Arc bot works them, returning to tasks
that needed more information before it could finish. Each attempt goes through
the real governed path and comes back either done or denied with reason codes.

This is where that answer is turned into a decision.

```
queued task
  -> governed request (real Supervisor, real Guardian, real Arc)
  -> performed, or denied with reason codes
  -> route_task_outcome
       completed  finished at this rung, nobody else involved
       retry      same rung tries again
       escalated  next rung up now owns it
       blocked    nothing further will be attempted automatically
```

`lima_office/runtime/task_outcome.py` is deliberately pure. It starts no
process, opens no socket and touches no queue — it takes an attempt and a
result and returns what should happen. The decision can therefore be tested
without a lab, and cannot differ between the lab and production.

## The routing

| Denial disposition | Outcome | Gap? |
|---|---|---|
| *(none — performed)* | `completed` | no |
| `correctable` | `retry` at the same rung, bounded | **yes** |
| `retry_with_fresh_decision` | `retry` at the same rung, bounded | no |
| `escalatable` | `escalated` to the next rung | **yes** |
| `forbidden` | `blocked` — never retried, never escalated | no |

Retries are capped at `DEFAULT_MAX_ATTEMPTS` (3). A denial that keeps arriving
is not resolved by arriving again, and retrying only ever means correcting a
malformed request or refreshing an aged decision — neither should need many
goes. When the budget runs out the task escalates rather than stopping, because
running out of attempts is itself a thing a rung above should see.

A rung that receives an escalated task starts with a **full** attempt budget.
It has not tried yet, and charging it for the previous rung's attempts would
let a task arrive already exhausted.

At the last rung the task is `blocked` rather than escalated — the terminal
rung cannot defer, so the task waits for the person. The SOP gap travels with
it: the thing to teach does not disappear because a human was needed.

## Two results that must not be read optimistically

**A result claiming both performed and denied** is treated as denied. Neither
half can be trusted, and reporting it as done would put work into the world
that the record says was refused.

**A result that did nothing and gave no reason** is `blocked`. There is nothing
to correct and nothing to teach, so it stops rather than looping.

## What running it found

The smoke is `scripts/arc-task-seam-smoke.py`, and running it against real
processes immediately found a hole.

Every Arc **execution** reason code — `document_not_found`,
`document_root_not_configured`, `document_not_utf8_text`,
`content_not_requested`, `execution_grant_absent` — was absent from
`REASON_CODE_REGISTRY`. Unclassified codes are `forbidden`, so a missing file
came back as *"no rung may permit this"*: terminal, no gap, nothing learned.

Correct as a default, wrong as an answer. Two are now classified:

| Code | Disposition | Why |
|---|---|---|
| `document_not_found` | `correctable` | Nothing refused it. Arc looked in the wrong place, and an SOP can teach it the right one. |
| `document_root_not_configured` | `escalatable` | Arc cannot configure itself out of this; a rung above has to. |

The rest stay `forbidden` deliberately. `execution_grant_absent` in particular
should **not** escalate: a missing grant usually means an opt-in gate is off,
and asking a higher rung to override an operator's opt-in is authority
shopping — the thing the disposition axis exists to prevent.

## Related

- [DENIAL_ROUTING.md](DENIAL_ROUTING.md) — the dispositions and the ladder
- [SOP_TRAINING.md](SOP_TRAINING.md) — what happens to the gaps this produces
