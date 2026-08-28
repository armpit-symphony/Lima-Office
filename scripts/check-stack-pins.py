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
* Installation - every file agrees, and the interpreter is importing something
  else entirely. Each repository needs an isolated environment that proves the
  installed package came from its exact lock commit.
  That check needs an environment rather than a repository, so it lives behind
  ``--check-installed`` and belongs in front of a test run.

This file is byte-identical in both repositories on purpose. Keep it that way:
nothing here may describe one of them as "this" repository.

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
    parser.add_argument(
        "--check-installed",
        action="store_true",
        help=(
            "Also prove the running interpreter has each pinned package "
            "installed at the locked commit. Offline. Run this before tests."
        ),
    )
    return parser


def _operational_files(root: Path, lock: stack_pins.Lock) -> list[Path]:
    found: set[Path] = set()
    for pattern in lock.operational_paths:
        found.update(path for path in root.glob(pattern) if path.is_file())
    return sorted(found)


def _read(path: Path) -> str:
    with open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def _unregistered(lock: stack_pins.Lock, root: Path) -> list[str]:
    """Report commit-shaped strings in operational files the lock ignores."""

    spans = stack_pins.registered_spans(lock, root)
    failures: list[str] = []
    for path in _operational_files(root, lock):
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

    # Git 2.55 can leave an automatic maintenance process touching .git for a
    # few milliseconds after fetch exits. Disable that work and tolerate only
    # cleanup errors in this disposable reachability clone; the command results
    # still fail closed below.
    with tempfile.TemporaryDirectory(
        prefix="stack-pin-check-", ignore_cleanup_errors=True
    ) as raw:
        work = Path(raw)
        commands = (
            ["git", "-c", "maintenance.auto=false", "init", "--quiet", str(work)],
            ["git", "-C", str(work), "remote", "add", "origin", url],
            [
                "git", "-c", "maintenance.auto=false", "-C", str(work),
                "fetch", "--quiet",
                "--filter=tree:0", "origin", "main",
            ],
        )
        for command in commands:
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode != 0:
                return None
        result = subprocess.run(
            [
                "git", "-c", "maintenance.auto=false", "-C", str(work),
                "merge-base", "--is-ancestor", commit, "FETCH_HEAD",
            ],
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


def _installed(lock: stack_pins.Lock) -> tuple[list[str], list[str]]:
    """Return (failures, notes) after comparing the environment with the lock.

    Only dependencies the lock describes as packages are checked. The rest are
    rollback targets and superseded baselines: real pins that appear in files
    but are never installed, so an interpreter that lacks them is correct.
    """

    failures: list[str] = []
    notes: list[str] = []
    for dependency in lock.dependencies:
        if dependency.package_name is None:
            notes.append(
                f"{dependency.name}: not a package, nothing to install"
            )
            continue
        found = stack_pins.installed_package(dependency.package_name)
        if found is None:
            failures.append(
                f"{dependency.name}: {dependency.package_name} is not installed "
                f"in {sys.executable}; create this repository's own environment "
                "and install it there"
            )
            continue
        if found.commit is None:
            failures.append(
                f"{dependency.name}: {dependency.package_name} is installed from "
                f"{found.described_origin}, so its commit cannot be verified "
                f"against the lock's {dependency.commit[:7]}"
            )
            continue
        if found.commit != dependency.commit:
            failures.append(
                f"{dependency.name}: {sys.executable} imports "
                f"{found.commit[:7]}, the lock pins {dependency.commit[:7]}; "
                "this interpreter belongs to another repository or is stale"
            )
            continue
        notes.append(
            f"{dependency.name}: installed {found.commit[:7]} matches the lock"
        )
    return failures, notes


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        root = stack_pins.repository_root()
        lock = stack_pins.load_lock(root)
    except stack_pins.LockError as exc:
        print("Dependency pin lock")
        print(f"- lock error: {exc}")
        print("Result: FAIL")
        return 1

    site_count = sum(len(dependency.sites) for dependency in lock.dependencies)
    failures = stack_pins.check_sites(lock, root)
    failures.extend(_unregistered(lock, root))
    notes: list[str] = []
    if args.check_installed:
        installed_failures, installed_notes = _installed(lock)
        failures.extend(installed_failures)
        notes.extend(installed_notes)
    if args.check_currency:
        currency_failures, currency_notes = _currency(lock)
        failures.extend(currency_failures)
        notes.extend(currency_notes)

    print("Dependency pin lock")
    print(f"- lock version: {lock.version}")
    print(f"- dependencies pinned: {len(lock.dependencies)}")
    print(f"- sites verified: {site_count}")
    print(f"- operational files scanned: {len(_operational_files(root, lock))}")
    print(f"- currency checked: {'yes' if args.check_currency else 'no'}")
    print(f"- installation checked: {'yes' if args.check_installed else 'no'}")
    if args.check_installed:
        print(f"- interpreter: {sys.executable}")
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
