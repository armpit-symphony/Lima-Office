"""Proofs that the interpreter runs the locked commit, not just the files.

Every pin site can agree with the lock while the running interpreter imports
something else entirely. That is not hypothetical in this stack: Arc-Bot-shell
freezes lima-runtime at a commit this repository has tracked past, so one
shared interpreter silently gives one of the two the wrong runtime, and the
loser's tests pass anyway.

Two checks read the environment here. They must not become two answers, so
these tests also hold the lab check to reading through the shared helper.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_stack_pin_lock import (
    COMMIT_A,
    COMMIT_B,
    ROOT,
    _fixture_lock,
    _write_fixture,
    stack_pins,
)


EXACT_CHECKER = ROOT / "scripts" / "check-exact-governed-stack-pins.py"


def _vcs(commit: str, requested: str | None = None) -> dict:
    return {
        "url": "https://github.com/armpit-symphony/LIMA-AI-OS.git",
        "vcs_info": {
            "vcs": "git",
            "commit_id": commit,
            "requested_revision": commit if requested is None else requested,
        },
    }


def _write_dist(
    site: Path,
    name: str = "demo-pkg",
    version: str = "0.1.0rc1",
    direct_url: dict | None = None,
) -> None:
    """Write a distribution importlib.metadata will discover on sys.path."""

    dist_info = site / f"{name.replace('-', '_')}-{version}.dist-info"
    dist_info.mkdir(parents=True, exist_ok=True)
    (dist_info / "METADATA").write_text(
        f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n",
        encoding="utf-8",
    )
    if direct_url is not None:
        (dist_info / "direct_url.json").write_text(
            json.dumps(direct_url), encoding="utf-8"
        )
    importlib.invalidate_caches()


class InstalledPackageTests(unittest.TestCase):
    """Reading what pip recorded at install time."""

    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory(prefix="office-installed-")
        self.addCleanup(directory.cleanup)
        self.site = Path(directory.name)
        sys.path.insert(0, str(self.site))
        self.addCleanup(sys.path.remove, str(self.site))
        importlib.invalidate_caches()

    def test_a_vcs_install_reports_the_commit_pip_resolved(self) -> None:
        _write_dist(self.site, direct_url=_vcs(COMMIT_A))
        found = stack_pins.installed_package("demo-pkg")
        self.assertIsNotNone(found)
        self.assertEqual(COMMIT_A, found.commit)
        self.assertEqual("0.1.0rc1", found.version)

    def test_a_package_that_is_absent_reports_nothing(self) -> None:
        self.assertIsNone(stack_pins.installed_package("demo-pkg-never-installed"))

    def test_a_moving_ref_is_distinguishable_from_a_pinned_commit(self) -> None:
        """An install asking for @main can resolve right and still be unpinned."""

        _write_dist(self.site, direct_url=_vcs(COMMIT_A, requested="main"))
        found = stack_pins.installed_package("demo-pkg")
        self.assertEqual(COMMIT_A, found.commit)
        self.assertEqual("main", found.requested_revision)

    def test_a_local_checkout_is_not_treated_as_a_verified_commit(self) -> None:
        """An editable install can contain anything; it must not pass as a pin."""

        _write_dist(
            self.site,
            direct_url={
                "url": "file:///C:/work/LIMA-AI-OS",
                "dir_info": {"editable": True},
            },
        )
        found = stack_pins.installed_package("demo-pkg")
        self.assertIsNone(found.commit)
        self.assertIn("local checkout", found.described_origin)

    def test_a_registry_install_has_no_commit_to_verify(self) -> None:
        _write_dist(self.site)
        self.assertIsNone(stack_pins.installed_package("demo-pkg").commit)

    def test_unreadable_provenance_is_reported_rather_than_raised(self) -> None:
        _write_dist(self.site, direct_url=_vcs(COMMIT_A))
        dist_info = self.site / "demo_pkg-0.1.0rc1.dist-info"
        (dist_info / "direct_url.json").write_text("{not json", encoding="utf-8")
        self.assertIsNone(stack_pins.installed_package("demo-pkg").commit)

    def test_a_commit_that_is_not_a_full_lowercase_hash_is_refused(self) -> None:
        """The shape rule the lock enforces, applied to what pip recorded."""

        _write_dist(self.site, direct_url=_vcs("ABCDEF1234"))
        self.assertIsNone(stack_pins.installed_package("demo-pkg").commit)


class InstalledCheckerTests(unittest.TestCase):
    """--check-installed, end to end through the real script."""

    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory(prefix="office-checker-")
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.site = self.root / "site-packages"
        self.site.mkdir()

    def _repo(self, commit: str = COMMIT_A) -> None:
        lock = _fixture_lock(commit=commit)
        lock["dependencies"]["demo-dep"]["package"] = {
            "name": "demo-pkg",
            "version": "0.1.0rc1",
        }
        _write_fixture(self.root, lock, commit=commit)
        (self.root / "scripts").mkdir(exist_ok=True)
        for name in ("stack_pins.py", "check-stack-pins.py"):
            (self.root / "scripts" / name).write_bytes(
                (ROOT / "scripts" / name).read_bytes()
            )

    def _run(self, *flags: str) -> subprocess.CompletedProcess:
        import os

        env = dict(os.environ)
        env["PYTHONPATH"] = str(self.site)
        return subprocess.run(
            [
                sys.executable,
                str(self.root / "scripts" / "check-stack-pins.py"),
                *flags,
            ],
            capture_output=True,
            text=True,
            cwd=str(self.root),
            env=env,
        )

    def test_the_wrong_interpreter_fails_and_names_both_commits(self) -> None:
        """The failure this exists to catch, reported so the cause is obvious."""

        self._repo(commit=COMMIT_A)
        _write_dist(self.site, direct_url=_vcs(COMMIT_B))

        result = self._run("--check-installed")

        self.assertEqual(1, result.returncode, result.stdout)
        self.assertIn("Result: FAIL", result.stdout)
        self.assertIn(COMMIT_A[:7], result.stdout)
        self.assertIn(COMMIT_B[:7], result.stdout)
        # Without the interpreter path the operator cannot tell which
        # environment is at fault, which is the whole question when two
        # repositories disagree.
        self.assertIn(sys.executable, result.stdout)

    def test_the_matching_interpreter_passes(self) -> None:
        self._repo(commit=COMMIT_A)
        _write_dist(self.site, direct_url=_vcs(COMMIT_A))

        result = self._run("--check-installed")

        self.assertEqual(0, result.returncode, result.stdout)
        self.assertIn("Result: PASS", result.stdout)

    def test_a_missing_package_fails_rather_than_passing_quietly(self) -> None:
        self._repo(commit=COMMIT_A)

        result = self._run("--check-installed")

        self.assertEqual(1, result.returncode, result.stdout)
        self.assertIn("is not installed", result.stdout)

    def test_the_default_run_still_ignores_the_environment(self) -> None:
        """Consistency must stay offline and environment-independent."""

        self._repo(commit=COMMIT_A)
        _write_dist(self.site, direct_url=_vcs(COMMIT_B))

        result = self._run()

        self.assertEqual(0, result.returncode, result.stdout)
        self.assertIn("installation checked: no", result.stdout)


class ExactGovernedStackPinTests(unittest.TestCase):
    """The lab check and the portable one must not become two answers."""

    def setUp(self) -> None:
        self.source = EXACT_CHECKER.read_text(encoding="utf-8")

    def test_it_reads_the_environment_through_the_shared_helper(self) -> None:
        """Two parsers would be two chances to disagree about one fact."""

        self.assertIn("stack_pins.installed_package", self.source)
        self.assertNotIn("direct_url.json", self.source)

    def test_it_still_verifies_more_than_the_commit(self) -> None:
        """It is the stricter check; losing that would be a silent downgrade."""

        self.assertIn("requested_revision", self.source)
        self.assertIn("package_version", self.source)

    def test_this_repository_declares_its_installed_packages(self) -> None:
        """Dropping a package block would silently make both checks no-ops."""

        named = {
            dependency.name
            for dependency in stack_pins.load_lock(ROOT).dependencies
            if dependency.package_name is not None
        }
        self.assertIn("lima-runtime", named)
        self.assertIn("guardian-suite", named)


if __name__ == "__main__":
    unittest.main()
