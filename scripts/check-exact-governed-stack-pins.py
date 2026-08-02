#!/usr/bin/env python3
"""Fail closed unless the lab uses the reviewed Guardian and LIMA source pins.

The expected identities come from ``stack.lock.json`` rather than a private
copy, so this check and the installed requirements cannot drift apart.

Reading what is installed is delegated to ``stack_pins.installed_package`` so
this check and ``check-stack-pins.py --check-installed`` cannot disagree about
what the environment contains. This check is the stricter of the two: it also
requires the recorded version and the requested revision to match, and proves
the governed-stack APIs are importable and callable. It is what the lab job
runs; ``--check-installed`` is the portable one-liner that names the offending
interpreter.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


_HELPER = Path(__file__).resolve().parent / "stack_pins.py"
_spec = importlib.util.spec_from_file_location("stack_pins", _HELPER)
assert _spec is not None and _spec.loader is not None
stack_pins = importlib.util.module_from_spec(_spec)
# Registered before execution because dataclasses resolves annotations through
# sys.modules, and a module loaded purely from a path is not there yet.
sys.modules["stack_pins"] = stack_pins
_spec.loader.exec_module(stack_pins)


def main() -> int:
    lock = stack_pins.load_lock()
    installed = [
        dependency
        for dependency in lock.dependencies
        if dependency.package_name is not None
    ]
    if not installed:
        raise SystemExit("the lock declares no installed packages to verify")

    for dependency in installed:
        package = dependency.package_name
        found = stack_pins.installed_package(package)
        if found is None:
            raise SystemExit(
                f"{package} is not installed in {sys.executable}; the lab needs "
                "this repository's own environment"
            )
        if (
            found.version != dependency.package_version
            or found.commit != dependency.commit
            or found.requested_revision != dependency.commit
        ):
            raise SystemExit(
                f"{package} identity mismatch in {sys.executable}: "
                f"version={found.version!r}, commit={found.commit!r}, "
                f"requested_revision={found.requested_revision!r}; the lock "
                f"requires version={dependency.package_version!r} and commit "
                f"{dependency.commit}"
            )
        print(f"{package}=={found.version} commit={found.commit}")

    from guardian_core.policy import decide_tool_use
    from lima.runtime import run_governed_request

    if not callable(decide_tool_use) or not callable(run_governed_request):
        raise SystemExit("required governed-stack APIs are not callable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
