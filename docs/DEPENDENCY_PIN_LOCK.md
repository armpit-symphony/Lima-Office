# Dependency pin lock

Every live dependency pin in LIMA Office is declared once in
[`stack.lock.json`](../stack.lock.json). Nothing else is the source of truth.

## Why this exists

Five separate incidents in this stack came from the same shape: one pin
duplicated across several files, and only some copies moved. The most recent
cost a full CI cycle mid-review, because the Arc commit pinned by the workflow
predated the operator CLI flags the new proof depended on.

The lock does not make pins correct. It makes a pin a single fact with one
place to change it, and makes disagreement a build failure instead of a
discovery.

## What is and is not a pin

A **live pin** decides what a build, test, or install actually uses. Those are
the only things in the lock.

Commit hashes in `docs/audits/`, `docs/proof_packets/`, `docs/BASELINE.md`,
and `tests/fixtures/` are **historical evidence**: a record of what was true
when something was attested. Roughly seventy such commits exist in this
repository. They must never be rewritten to match a current pin, and no tool
here reads or touches them. `check-stack-pins.py` only ever visits paths the
lock names explicitly, and a test asserts no evidence path is registered as a
site.

## The three checks

They catch different failures and run in different places.

| | Consistency | Currency | Installation |
|---|---|---|---|
| Question | Do all copies of a pin agree? | Is the pin still the right one? | Is the interpreter running it? |
| Needs network | No | Yes | No |
| Where | Every pull request, blocking | Scheduled weekday job | Lab job, before tests |

Currency deliberately does not block pull requests. Whether Arc merged
something this morning has nothing to do with whether the change under review
is correct, and a dependency's merge should never turn this repository red.

A pin can pass consistency and fail currency at the same time — that is
exactly the state that caused the last incident.

A pin can also pass both and still be wrong where it counts. Every file can
agree with the lock while the interpreter imports a different commit entirely,
because Arc-Bot-shell freezes `lima-runtime` at a commit this repository has
tracked past. `scripts/check-exact-governed-stack-pins.py` is the installation
check the lab job runs; `check-stack-pins.py --check-installed` is the portable
form that names the offending interpreter. Both resolve what is installed
through the same helper, so they cannot disagree. Each repository needs its own
environment: [ENVIRONMENT.md](ENVIRONMENT.md).

## Policies

- `tracking` — expected to equal the dependency's `main`. Currency reports it
  when it falls behind.
- `frozen` — deliberately held behind `main`. Requires a written reason, is
  reported but never failed by the currency job, and `bump-pin.py` refuses to
  move it without `--force`.

Arc pins LIMA at its RC1 frozen-API commit rather than LIMA `main`; that is a
`frozen` pin in Arc's own lock, not drift.

## Moving a pin

```bash
python scripts/bump-pin.py arc-bot-shell --to main
python scripts/bump-pin.py lima-runtime --to <full-40-character-commit>
python scripts/bump-pin.py --all-tracking --to main
python scripts/check-stack-pins.py
```

The bumper rewrites only the captured commit characters and preserves each
file's existing line endings, so moving a pin produces a one-line diff per
site rather than a whitespace-churned file.

## Adding a pin site

Add an entry under the dependency's `sites` with the file path, a regex
capturing a group named `commit`, and the expected occurrence count. The
pattern must anchor on something that identifies the dependency — a repository
name or a label — because several sites hold more than one dependency's pin.

Any commit-shaped string that appears in an operational path
(`requirements*.txt`, `.github/workflows/`, `scripts/`) and is not registered
is a build failure, so a new duplicate cannot be introduced quietly.
