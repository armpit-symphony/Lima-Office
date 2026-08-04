# Training Arc toward doing the job alone

Arc bot is fed SOP and trained in its job until it can do that job accurately
on its own. The rungs above it — at minimum a system manager and a GM — are
the failsafes that catch what it cannot yet handle, before anything reaches a
person.

That makes every shortfall a fact about what Arc has not been taught. The
system already records those facts as denials with reason codes, so the
training signal needs no new instrumentation — only a shape that can be fed
back.

## Not every denial is a training gap

This is the line the whole loop depends on.

| Disposition | A training gap? | Why |
|---|---|---|
| `correctable` | **Yes** | Arc built the request wrong. An SOP teaches it the right shape and the next attempt needs no one. |
| `escalatable` | **Yes** | Arc was right to stop and a higher rung decided. The SOP records that decision so it can be reused. |
| `forbidden` | **No** | The control worked. An instruction that got Arc past it would be an instruction to defeat it. |
| `retry_with_fresh_decision` | **No** | Nothing was refused and nothing misunderstood. A decision aged out. There is nothing to teach. |

`is_teachable()` enforces it, and `SopGap.__post_init__` enforces it again, so
constructing a gap directly cannot route around `gap_from_denial()`. Teaching
Arc past a prompt-injection denial is not a feature to be careful with — it is
a record the system refuses to hold.

The most restrictive reason governs, as everywhere else: a `correctable`
reason arriving alongside a `forbidden` one is not teachable.

## Two ways an SOP arrives, one record

| Source | When | Status on creation |
|---|---|---|
| `escalation` | Observed from a denial Arc hit | `open` — awaiting an instruction |
| `operator_authored` | Typed into the UI | `instructed` — the instruction is the point |

Authored SOP exists so an operator can teach Arc a job **before** it fails at
one, rather than only afterwards. It carries no reason codes because nothing
was denied.

Both produce the same record shape, so the training loop does not care which
happened. `test_both_sources_produce_the_same_record_shape` holds that.

## A gap's life

```
open ──with_instruction()──▶ instructed ──▶ retired
```

- **open** — Arc stopped, nobody has written the SOP yet
- **instructed** — someone supplied the instruction; a rung that decided the
  escalation, or an operator in the UI. Both land in the same field.
- **retired** — Arc demonstrably does the job without it

A gap marked beyond `open` without an instruction is refused, so the status
cannot claim progress that did not happen.

## Identity: one shortfall, not twenty records

`gap_id_for()` derives the id from task, capability and reason codes rather
than generating one. Arc failing the same way twenty times is **one thing to
teach**, and it collapses to one gap instead of accumulating duplicates that
make the backlog look worse than it is.

## The number to watch

```python
training_progress(completed_alone=8, gaps=[...])
# {"attempts": 10, "autonomy_rate": 0.8, "open_gaps": 1, ...}
```

`autonomy_rate` is the share of attempts Arc finished with nobody else
involved. Training is working when it rises.

It also exposes the failure that is easy to miss: SOPs written but never
retiring anything show up as `instructed_gaps` that never fall. Instruction
written is not the same as job learned.

No attempts yields `None` rather than `0.0` — nothing attempted is not the
same as nothing achieved.

## What a gap never contains

A gap records **what was attempted and why it stopped**, never the material:
no task payload, document body, prompt, or model output. Same boundary the
diagnostics surfaces keep, and `training_progress` reports counts only —
nothing in it reads an instruction body.

## Related

- [DENIAL_ROUTING.md](DENIAL_ROUTING.md) — the dispositions this builds on, and
  the escalation ladder the rungs sit in
