#!/usr/bin/env python3
"""Fail closed unless every live dependency pin agrees with the lock.

Two independent failure modes bit this repository repeatedly, and they need
different checks:

* Consistency - one dependency, several sites, one of them left behind. This
  check is offline and deterministic, so it runs on every pull request.
* Currency - a pin that is internally consistent but lags a merge the repo
  needs. That needs the dependency's main, so it lives behind
  ``--check-currency`` and runs on a schedule instead of blocking review. An
  unrelated merge in a dependency must never turn this repository's pull
  request CI red.

The unregistered scan covers operational paths only. Commit hashes in audits,
proof packets, and fixtures are evidence of what was true at the time; this
tool must never rewrite them or demand they move.
"""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile


_HELPER = Path(__file__).resolve().parent / "stack_pins.py"
_spec = importlib.util.spec_from_file_location("stack_pins", _HELPER)
assert _spec is not None and _spec.loader is not None
stack_pins = importlib.util.module_from_spec(_spec)
# Registered before execution because dataclasses resolves annotations through
# sys.modules, and a module loaded purely from a path is not there yet.
sys.modules["stack_pins"] = stack_pins
_spec.loader.exec_module(stack_pins)


OPERATIONAL_GLOBS = (
    "requirements*.txt",
    ".github/workflows/*.yml",
    ".github/workflows/*.yaml",
    "scripts/*.py",
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Prove every live dependency pin matches stack.lock.json. "
            "This command changes nothing."
        )
    )
    parser.add_argument(
        "--check-currency",
        action="store_true",
        help=(
            "Also contact each dependency repository and report pins that are "
            "not their main. Requires network access."
        ),
    )
    return parser


def _operational_files(root: Path) -> list[Path]:
    found: set[Path] = set()
    for pattern in OPERATIONAL_GLOBS:
        found.update(path for path in root.glob(pattern) if path.is_file())
    return sorted(found)


def _read(path: Path) -> str:
    with open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def _unregistered(lock: stack_pins.Lock, root: Path) -> list[str]:
    """Report commit-shaped strings in operational files the lock ignores."""

    spans = stack_pins.registered_spans(lock, root)
    failures: list[str] = []
    for path in _operational_files(root):
        relative = path.relative_to(root).as_posix()
        known = spans.get(relative, [])
        for match in stack_pins.COMMIT_SHAPED.finditer(_read(path)):
            span = match.span()
            if any(start <= span[0] and span[1] <= end for start, end in known):
                continue
            failures.append(
                f"{relative}: commit {match.group()} is not registered in "
                f"{stack_pins.LOCK_NAME}; add a site for it or move it out of "
                "the operational paths"
            )
    return failures


def _remote_main(url: str) -> str | None:
    result = subprocess.run(
        ["git", "ls-remote", url, "refs/heads/main"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None
    return result.stdout.split()[0].strip()


def _is_ancestor_of_main(url: str, commit: str) -> bool | None:
    """Return whether the pin is reachable from the dependency's main."""

    with tempfile.TemporaryDirectory(prefix="lima-office-pin-check-") as raw:
        work = Path(raw)
        commands = (
            ["git", "init", "--quiet", str(work)],
            ["git", "-C", str(work), "remote", "add", "origin", url],
            [
                "git", "-C", str(work), "fetch", "--quiet",
                "--filter=tree:0", "origin", "main",
            ],
        )
        for command in commands:
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode != 0:
                return None
        result = subprocess.run(
            ["git", "-C", str(work), "merge-base", "--is-ancestor", commit,
             "FETCH_HEAD"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0


def _currency(lock: stack_pins.Lock) -> tuple[list[str], list[str]]:
    """Return (failures, notes) after comparing each pin with its main."""

    failures: list[str] = []
    notes: list[str] = []
    for dependency in lock.dependencies:
        head = _remote_main(dependency.clone_url)
        if head is None:
            failures.append(
                f"{dependency.name}: could not read main from "
                f"{dependency.clone_url}"
            )
            continue
        if head == dependency.commit:
            notes.append(f"{dependency.name}: current with main ({head[:7]})")
            continue
        ancestor = _is_ancestor_of_main(dependency.clone_url, dependency.commit)
        if ancestor is False:
            failures.append(
                f"{dependency.name}: pinned commit {dependency.commit[:7]} is "
                "not reachable from main; it may have been rewritten or retired"
            )
            continue
        if ancestor is None:
            failures.append(
                f"{dependency.name}: could not verify {dependency.commit[:7]} "
                "against main"
            )
            continue
        if dependency.policy == "frozen":
            notes.append(
                f"{dependency.name}: frozen at {dependency.commit[:7]}, main is "
                f"{head[:7]} - {dependency.reason}"
            )
            continue
        failures.append(
            f"{dependency.name}: tracking pin {dependency.commit[:7]} is behind "
            f"main {head[:7]}; run "
            f"python scripts/bump-pin.py {dependency.name} --to main"
        )
    return failures, notes


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        root = stack_pins.repository_root()
        lock = stack_pins.load_lock(root)
    except stack_pins.LockError as exc:
        print("LIMA Office dependency pin lock")
        print(f"- lock error: {exc}")
        print("Result: FAIL")
        return 1

    site_count = sum(len(dependency.sites) for dependency in lock.dependencies)
    failures = stack_pins.check_sites(lock, root)
    failures.extend(_unregistered(lock, root))
    notes: list[str] = []
    if args.check_currency:
        currency_failures, notes = _currency(lock)
        failures.extend(currency_failures)

    print("LIMA Office dependency pin lock")
    print(f"- lock version: {lock.version}")
    print(f"- dependencies pinned: {len(lock.dependencies)}")
    print(f"- sites verified: {site_count}")
    print(f"- operational files scanned: {len(_operational_files(root))}")
    print(f"- currency checked: {'yes' if args.check_currency else 'no'}")
    for dependency in lock.dependencies:
        print(
            f"  {dependency.name} {dependency.commit[:7]} "
            f"({dependency.policy}, {len(dependency.sites)} site(s))"
        )
    for note in notes:
        print(f"- {note}")
    for failure in failures:
        print(f"- FAIL {failure}")
    print(f"- failures: {len(failures)}")
    print("Result:", "FAIL" if failures else "PASS")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
