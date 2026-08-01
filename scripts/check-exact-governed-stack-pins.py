#!/usr/bin/env python3
"""Fail closed unless the lab uses the reviewed Guardian and LIMA source pins."""

from __future__ import annotations

import json
from importlib import metadata


EXPECTED = {
    "guardian-suite": {
        "version": "1.0.0",
        "commit": "69e843218c521b913edcec404dea6b7be8c64f06",
    },
    "lima-runtime": {
        "version": "0.1.0rc1",
        "commit": "40d6f1379284931ee46f05650e9201d6f98975d6",
    },
}


def _direct_url(distribution: metadata.Distribution) -> dict[str, object]:
    content = distribution.read_text("direct_url.json")
    if content is None:
        raise SystemExit(f"{distribution.metadata['Name']} has no direct_url.json")
    return json.loads(content)


def main() -> int:
    for package, expected in EXPECTED.items():
        distribution = metadata.distribution(package)
        version = distribution.version
        direct_url = _direct_url(distribution)
        vcs_info = direct_url.get("vcs_info")
        commit = vcs_info.get("commit_id") if isinstance(vcs_info, dict) else None
        requested = vcs_info.get("requested_revision") if isinstance(vcs_info, dict) else None
        if (
            version != expected["version"]
            or commit != expected["commit"]
            or requested != expected["commit"]
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
