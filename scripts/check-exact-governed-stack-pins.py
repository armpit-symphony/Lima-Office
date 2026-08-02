#!/usr/bin/env python3
"""Fail closed unless the lab uses the reviewed Guardian and LIMA source pins.

The expected identities come from ``stack.lock.json`` rather than a private
copy, so this check and the installed requirements cannot drift apart.
"""

from __future__ import annotations

import importlib.util
import json
from importlib import metadata
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


def _direct_url(distribution: metadata.Distribution) -> dict[str, object]:
    content = distribution.read_text("direct_url.json")
    if content is None:
        raise SystemExit(f"{distribution.metadata['Name']} has no direct_url.json")
    return json.loads(content)


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
        distribution = metadata.distribution(package)
        version = distribution.version
        direct_url = _direct_url(distribution)
        vcs_info = direct_url.get("vcs_info")
        commit = vcs_info.get("commit_id") if isinstance(vcs_info, dict) else None
        requested = (
            vcs_info.get("requested_revision") if isinstance(vcs_info, dict) else None
        )
        if (
            version != dependency.package_version
            or commit != dependency.commit
            or requested != dependency.commit
        ):
            raise SystemExit(
                f"{package} identity mismatch: version={version!r}, "
                f"commit={commit!r}, requested_revision={requested!r}"
            )
        print(f"{package}=={version} commit={commit}")

    from guardian_core.policy import decide_tool_use
    from lima.runtime import run_governed_request

    if not callable(decide_tool_use) or not callable(run_governed_request):
        raise SystemExit("required governed-stack APIs are not callable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
