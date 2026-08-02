#!/usr/bin/env python3
"""Move a dependency pin in the lock and every site that repeats it.

The whole point is that a bump is one command. Editing a pin by hand means
remembering every site that duplicates it, which is exactly the mistake this
tooling exists to prevent.

    python scripts/bump-pin.py arc-bot-shell --to main
    python scripts/bump-pin.py lima-runtime --to 0718af2...
    python scripts/bump-pin.py --all-tracking --to main

A frozen pin is held behind main deliberately, so it is skipped unless it is
named explicitly together with --force.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys


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
        description="Move one dependency pin across the lock and all its sites."
    )
    parser.add_argument(
        "dependency",
        nargs="?",
        help="Dependency name as declared in stack.lock.json.",
    )
    parser.add_argument(
        "--all-tracking",
        action="store_true",
        help="Bump every tracking dependency instead of one named dependency.",
    )
    parser.add_argument(
        "--to",
        required=True,
        help="A full 40-character commit, or 'main' to resolve the remote head.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow moving a frozen pin. Update its reason in the same change.",
    )
    return parser


def _resolve(dependency: stack_pins.Dependency, target: str) -> str:
    if target != "main":
        if not stack_pins.COMMIT_PATTERN.match(target):
            raise SystemExit(
                "--to must be 'main' or a full lowercase 40-character commit"
            )
        return target
    result = subprocess.run(
        ["git", "ls-remote", dependency.clone_url, "refs/heads/main"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise SystemExit(f"could not read main from {dependency.clone_url}")
    return result.stdout.split()[0].strip()


def _rewrite_lock(root: Path, name: str, commit: str) -> None:
    path = root / stack_pins.LOCK_NAME
    with open(path, "r", encoding="utf-8", newline="") as handle:
        raw = json.loads(handle.read())
    raw["dependencies"][name]["commit"] = commit
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(raw, handle, indent=2)
        handle.write("\n")


def _bump(root: Path, dependency: stack_pins.Dependency, commit: str) -> list[str]:
    touched: list[str] = []
    for site in dependency.sites:
        if not (root / site.path).is_file():
            raise SystemExit(f"{dependency.name}: site {site.path} does not exist")
        text = stack_pins.read_site_text(root, site)
        found = stack_pins.site_matches(text, site)
        if len(found) != site.occurrences:
            raise SystemExit(
                f"{dependency.name}: {site.path} matched {len(found)} "
                f"occurrence(s), the lock declares {site.occurrences}; refusing "
                "to rewrite a site the lock no longer describes"
            )
        updated = stack_pins.rewrite_site(text, site, commit)
        if updated != text:
            stack_pins.write_site_text(root, site, updated)
            touched.append(site.path)
    _rewrite_lock(root, dependency.name, commit)
    return touched


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if bool(args.dependency) == bool(args.all_tracking):
        raise SystemExit("name one dependency or pass --all-tracking, not both")

    root = stack_pins.repository_root()
    lock = stack_pins.load_lock(root)
    if args.all_tracking:
        targets = [item for item in lock.dependencies if item.policy == "tracking"]
    else:
        targets = [lock.dependency(args.dependency)]

    changed = False
    for dependency in targets:
        if dependency.policy == "frozen" and not args.force:
            print(
                f"{dependency.name}: frozen at {dependency.commit[:7]}, skipped "
                f"({dependency.reason}). Pass --force to move it."
            )
            continue
        commit = _resolve(dependency, args.to)
        if commit == dependency.commit:
            print(f"{dependency.name}: already at {commit[:7]}, nothing to do")
            continue
        touched = _bump(root, dependency, commit)
        changed = True
        print(
            f"{dependency.name}: {dependency.commit[:7]} -> {commit[:7]} "
            f"across {len(touched) + 1} file(s)"
        )
        for path in (stack_pins.LOCK_NAME, *touched):
            print(f"  updated {path}")

    if changed:
        print("Now run: python scripts/check-stack-pins.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
