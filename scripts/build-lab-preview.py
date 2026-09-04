#!/usr/bin/env python3
"""Build the coordinated Arc + LIMA Office Windows lab-preview artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]
RELEASE_SOURCE = ROOT / "release" / "lab-preview"
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
VERSION_RE = re.compile(r"^[0-9A-Za-z][0-9A-Za-z.-]{0,63}$")
PAYLOAD_FILES = (
    "README.md",
    "install-lab-preview.ps1",
    "start-lab-preview.ps1",
    "smoke-lab-preview.ps1",
    "setup-local-model.ps1",
)


class PreviewBuildError(RuntimeError):
    """The requested artifact cannot be proven reproducible."""


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise PreviewBuildError(result.stderr.strip() or "git command failed")
    return result.stdout.strip()


def _require_clean_tracked_tree() -> None:
    if _git("status", "--porcelain", "--untracked-files=no"):
        raise PreviewBuildError(
            "tracked LIMA Office files are modified; commit them before building"
        )


def _load_lock() -> dict:
    payload = json.loads((ROOT / "stack.lock.json").read_text(encoding="utf-8"))
    dependencies = payload.get("dependencies")
    if not isinstance(dependencies, dict):
        raise PreviewBuildError("stack.lock.json has no dependency map")
    return dependencies


def build_manifest(version: str, office_commit: str) -> dict:
    if not VERSION_RE.fullmatch(version):
        raise PreviewBuildError("version must be a simple 1-64 character label")
    if not COMMIT_RE.fullmatch(office_commit):
        raise PreviewBuildError("Office commit must be a full lowercase hash")

    dependencies = _load_lock()
    required = {
        "arc-bot-shell": "arc_worker",
        "lima-runtime": "lima_runtime",
        "guardian-suite": "guardian",
    }
    components = {
        "lima_office": {
            "repo": "armpit-symphony/Lima-Office",
            "commit": office_commit,
        }
    }
    for lock_name, manifest_name in required.items():
        dependency = dependencies.get(lock_name)
        if not isinstance(dependency, dict):
            raise PreviewBuildError(f"missing dependency {lock_name}")
        commit = dependency.get("commit")
        repo = dependency.get("repo")
        if not isinstance(commit, str) or not COMMIT_RE.fullmatch(commit):
            raise PreviewBuildError(f"{lock_name} has an invalid commit")
        if not isinstance(repo, str) or not repo:
            raise PreviewBuildError(f"{lock_name} has an invalid repository")
        components[manifest_name] = {"repo": repo, "commit": commit}

    return {
        "schema_version": "lima-office-arc-lab-preview-manifest-v1",
        "version": version,
        "release_channel": "local_lab_preview_candidate",
        "production_ready": False,
        "customer_pilot_allowed": False,
        "operator_authentication": False,
        "topology": {
            "supervisor_servers": 1,
            "arc_worker_min": 1,
            "arc_worker_max": 8,
            "tenant_mode": "single_tenant",
            "network_scope": "localhost_only",
        },
        "local_model": {
            "provider": "ollama",
            "default_model": "qwen2.5:7b",
            "license": "Apache-2.0",
            "network_scope": "loopback_only",
            "separate_opt_ins_required": True,
            "automatic_sop_save": False,
            "bundled_model_weights": False,
        },
        "registration_practice": {
            "scenario_count": 25,
            "template_count": 3,
            "data_classification": "synthetic_fixture_only",
            "deterministic_scoring": True,
            "human_review_required": True,
            "mock_target": "localhost_test_range",
            "mock_submission_available": True,
            "external_submission_allowed": False,
            "submission_allowed": False,
            "browser_automation_allowed": False,
            "external_side_effects": False,
        },
        "allowed_capabilities": [
            "document_list", "document_read", "local_model_preview",
            "registration_practice", "registration_mock_review",
        ],
        "blocked_capabilities": [
            "cloud_models",
            "browser_automation",
            "connectors",
            "external_sends",
            "file_mutation",
            "software_remediation",
            "production_server_changes",
            "robotics",
            "lan_exposure",
            "hidden_background_actions",
        ],
        "components": components,
    }


def _zip_write(archive: zipfile.ZipFile, name: str, content: bytes) -> None:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, content)


def build_artifact(
    version: str,
    output_dir: Path,
    *,
    office_commit: str | None = None,
    require_clean: bool = True,
) -> tuple[Path, Path, dict]:
    if require_clean:
        _require_clean_tracked_tree()
    commit = office_commit or _git("rev-parse", "HEAD")
    manifest = build_manifest(version, commit)

    missing = [name for name in PAYLOAD_FILES if not (RELEASE_SOURCE / name).is_file()]
    if missing:
        raise PreviewBuildError(f"missing release payload files: {missing}")

    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"lima-office-arc-lab-preview-{version}.zip"
    artifact = output_dir / filename
    checksum = output_dir / f"{filename}.sha256"

    with tempfile.TemporaryDirectory(prefix="lima-office-preview-build-"):
        with zipfile.ZipFile(artifact, "w") as archive:
            _zip_write(
                archive,
                "manifest.json",
                (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode(),
            )
            for name in PAYLOAD_FILES:
                _zip_write(archive, name, (RELEASE_SOURCE / name).read_bytes())

    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    checksum.write_text(f"{digest}  {filename}\n", encoding="ascii")
    return artifact, checksum, manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="0.1.0-lab.4")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    try:
        artifact, checksum, manifest = build_artifact(
            args.version, args.output_dir.resolve()
        )
    except (OSError, ValueError, PreviewBuildError) as exc:
        print(f"Lab preview build failed: {exc}")
        return 1
    print(
        json.dumps(
            {
                "artifact": str(artifact),
                "checksum": str(checksum),
                "version": manifest["version"],
                "production_ready": manifest["production_ready"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
