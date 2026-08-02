# This repository needs an interpreter of its own

Lima-Office pins `lima-runtime` to `0718af2` and tracks it forward.

Arc-Bot-shell pins the same package to `40d6f13` and freezes it there: that is
its v0.10 trust baseline, and Arc refuses to start against any other commit.

Both are correct. Neither can move to satisfy the other. A single shared
interpreter can therefore only ever serve one of the two repositories, and the
failure is silent — the loser's tests import the wrong runtime and pass.

## Setup

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-lab.txt    # Windows
.venv/bin/python -m pip install -r requirements-lab.txt        # macOS and Linux
```

`requirements-dev.txt` is enough for contract and doc validation. The lab
dependencies — Guardian and LIMA — are what the governed tests and the session
launcher need.

`.venv/` is ignored by git. Do not install this repository into a system or
user-level interpreter, and do not reuse Arc's environment.

## Proving the environment is the right one

Two checks read the environment. They cannot disagree: both resolve what is
installed through `stack_pins.installed_package`, and both compare against
`stack.lock.json`.

```bash
.venv/Scripts/python scripts/check-exact-governed-stack-pins.py
```

The stricter one, and what the `exact-governed-arc-stack` CI job runs. Requires
the recorded version and the requested revision to match as well as the commit,
then proves the governed-stack APIs import and are callable.

```
guardian-suite==1.0.0 commit=69e843218c521b913edcec404dea6b7be8c64f06
lima-runtime==0.1.0rc1 commit=0718af23570ed631ed4af4c7d9d8b0db82075648
```

```bash
.venv/Scripts/python scripts/check-stack-pins.py --check-installed
```

The portable one. Checks the commit only, but names the interpreter at fault,
which is the useful thing when two repositories disagree:

```
- FAIL lima-runtime: ...\Arc-Bot-shell\.venv\Scripts\python.exe imports
  40d6f13, the lock pins 0718af2; this interpreter belongs to another
  repository or is stale
```

It is not in CI here, because the exact-stack check already covers the lab job
and consistency has to stay environment-independent so it can block a pull
request regardless of how CI installed anything.

## Why a version number is not enough

Both pins build `lima-runtime 0.1.0rc1`. The version string cannot tell them
apart, which is why both checks read the resolved commit instead.

`requested_revision` matters for the same reason. An install that asked for
`@main` can resolve to exactly the right commit today and still be unpinned;
the exact-stack check requires the request itself to name the commit.

Editable installs are reported as unverifiable rather than accepted — a local
checkout can contain any working tree at all.

## When a check fails after a pin moves

A bumped pin does not update an environment that already exists. Reinstall:

```bash
.venv/Scripts/python -m pip install -r requirements-lab.txt --force-reinstall --no-deps
```

## What these checks are not

They do not replace the consistency check. Files agreeing with the lock and the
interpreter agreeing with the lock are separate questions, and both have gone
wrong in this stack independently. See
[DEPENDENCY_PIN_LOCK.md](DEPENDENCY_PIN_LOCK.md).
