"""Proofs for the dependency pin lock and the tooling that moves it.

The lock exists because five separate incidents came from one pin being
duplicated across several files and only some copies being updated. These
tests hold both halves of that: the real repository must be consistent right
now, and each way of breaking it must actually be caught.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
_HELPER = ROOT / "scripts" / "stack_pins.py"
_spec = importlib.util.spec_from_file_location("stack_pins", _HELPER)
assert _spec is not None and _spec.loader is not None
stack_pins = importlib.util.module_from_spec(_spec)
sys.modules["stack_pins"] = stack_pins
_spec.loader.exec_module(stack_pins)

CHECKER = ROOT / "scripts" / "check-stack-pins.py"
BUMPER = ROOT / "scripts" / "bump-pin.py"

COMMIT_A = "1111111111111111111111111111111111111111"
COMMIT_B = "2222222222222222222222222222222222222222"


def _fixture_lock(commit: str = COMMIT_A, policy: str = "tracking") -> dict:
    return {
        "lock_version": "1.0.0",
        "dependencies": {
            "demo-dep": {
                "repo": "armpit-symphony/Demo",
                "commit": commit,
                "policy": policy,
                "reason": "held for a documented reason" if policy == "frozen" else "",
                "package": {"name": "demo-dep", "version": "1.0.0"},
                "sites": [
                    {
                        "path": "requirements-demo.txt",
                        "pattern": "Demo\\.git@(?P<commit>[0-9a-f]{40})",
                        "occurrences": 1,
                    },
                    {
                        "path": "docs/DEMO.md",
                        "pattern": "Demo dep:\\s*`(?P<commit>[0-9a-f]{40})`",
                        "occurrences": 1,
                    },
                ],
            }
        },
    }


def _write_fixture(root: Path, lock: dict, commit: str = COMMIT_A) -> None:
    (root / "docs").mkdir(parents=True, exist_ok=True)
    with open(root / "stack.lock.json", "w", encoding="utf-8", newline="\n") as handle:
        json.dump(lock, handle, indent=2)
        handle.write("\n")
    # Deliberately CRLF: the real requirements-lab.txt uses CRLF, and a bumper
    # that normalises line endings would rewrite the whole file.
    with open(
        root / "requirements-demo.txt", "w", encoding="utf-8", newline=""
    ) as handle:
        handle.write(
            "-r requirements-dev.txt\r\n"
            f"demo-dep @ git+https://github.com/armpit-symphony/Demo.git@{commit}\r\n"
        )
    with open(root / "docs" / "DEMO.md", "w", encoding="utf-8", newline="") as handle:
        handle.write(f"# Demo\n\n- Demo dep:\n  `{commit}`\n")


class RealRepositoryPinTests(unittest.TestCase):
    """The pins in this repository must agree with the lock right now."""

    def test_lock_parses_and_declares_the_governed_stack(self):
        lock = stack_pins.load_lock(ROOT)
        names = {dependency.name for dependency in lock.dependencies}
        self.assertEqual({"guardian-suite", "lima-runtime", "arc-bot-shell"}, names)

    def test_every_site_agrees_with_the_lock(self):
        lock = stack_pins.load_lock(ROOT)
        self.assertEqual([], stack_pins.check_sites(lock, ROOT))

    def test_installed_packages_declare_a_version(self):
        lock = stack_pins.load_lock(ROOT)
        for name in ("guardian-suite", "lima-runtime"):
            dependency = lock.dependency(name)
            self.assertIsNotNone(dependency.package_name)
            self.assertTrue(dependency.package_version)

    def test_checker_passes_on_the_real_repository(self):
        result = subprocess.run(
            [sys.executable, str(CHECKER)],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("Result: PASS", result.stdout)

    def test_currency_checker_defuses_disposable_git_cleanup_race(self):
        """Scheduled currency checks must not fail after Git already succeeded."""

        source = CHECKER.read_text(encoding="utf-8")
        self.assertIn("maintenance.auto=false", source)
        self.assertIn("ignore_cleanup_errors=True", source)

    def test_no_operational_file_holds_an_unregistered_pin(self):
        """A new pin site must be registered, not silently duplicated."""

        result = subprocess.run(
            [sys.executable, str(CHECKER)],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
        )
        self.assertNotIn("is not registered", result.stdout)

    def test_evidence_records_are_not_tracked_as_pins(self):
        """Audit and proof-packet commits are history and must stay untouched."""

        lock = stack_pins.load_lock(ROOT)
        tracked = {site.path for dep in lock.dependencies for site in dep.sites}
        for path in tracked:
            self.assertFalse(
                path.startswith("docs/audits/")
                or path.startswith("docs/proof_packets/")
                or path.startswith("tests/fixtures/"),
                f"{path} is historical evidence and must not be a live pin site",
            )


class LockValidationTests(unittest.TestCase):
    def _load(self, mutate) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            lock = _fixture_lock()
            mutate(lock)
            _write_fixture(root, lock)
            stack_pins.load_lock(root)

    def test_frozen_pin_requires_a_reason(self):
        def mutate(lock):
            lock["dependencies"]["demo-dep"]["policy"] = "frozen"
            lock["dependencies"]["demo-dep"]["reason"] = "   "

        with self.assertRaises(stack_pins.LockError) as caught:
            self._load(mutate)
        self.assertIn("why it is held behind main", str(caught.exception))

    def test_unknown_policy_is_rejected(self):
        def mutate(lock):
            lock["dependencies"]["demo-dep"]["policy"] = "whatever"

        with self.assertRaises(stack_pins.LockError):
            self._load(mutate)

    def test_short_or_uppercase_commit_is_rejected(self):
        for bad in ("1111111", "a" * 40 + "b", ("ab" * 20).upper()):
            with self.subTest(commit=bad):
                with self.assertRaises(stack_pins.LockError):
                    self._load(
                        lambda lock, bad=bad: lock["dependencies"]["demo-dep"].update(
                            commit=bad
                        )
                    )

    def test_pattern_without_a_commit_group_is_rejected(self):
        def mutate(lock):
            lock["dependencies"]["demo-dep"]["sites"][0]["pattern"] = "[0-9a-f]{40}"

        with self.assertRaises(stack_pins.LockError) as caught:
            self._load(mutate)
        self.assertIn("named 'commit'", str(caught.exception))

    def test_dependency_without_sites_is_rejected(self):
        def mutate(lock):
            lock["dependencies"]["demo-dep"]["sites"] = []

        with self.assertRaises(stack_pins.LockError):
            self._load(mutate)

    def test_operational_paths_default_when_absent(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _write_fixture(root, _fixture_lock())
            self.assertEqual(
                stack_pins.DEFAULT_OPERATIONAL_PATHS,
                stack_pins.load_lock(root).operational_paths,
            )

    def test_operational_paths_can_be_declared(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            lock = _fixture_lock()
            lock["operational_paths"] = ["requirements*.txt"]
            _write_fixture(root, lock)
            self.assertEqual(
                ("requirements*.txt",),
                stack_pins.load_lock(root).operational_paths,
            )


class DriftDetectionTests(unittest.TestCase):
    """Each way a pin can drift must be caught, not merely be possible."""

    def test_a_site_left_behind_is_reported(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _write_fixture(root, _fixture_lock())
            # Move only the requirements file, exactly the mistake made before.
            text = (root / "requirements-demo.txt").read_bytes()
            (root / "requirements-demo.txt").write_bytes(
                text.replace(COMMIT_A.encode(), COMMIT_B.encode())
            )
            lock = stack_pins.load_lock(root)
            failures = stack_pins.check_sites(lock, root)
            self.assertEqual(1, len(failures))
            self.assertIn("requirements-demo.txt", failures[0])
            self.assertIn(COMMIT_B, failures[0])

    def test_a_missing_site_is_reported(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _write_fixture(root, _fixture_lock())
            (root / "docs" / "DEMO.md").unlink()
            lock = stack_pins.load_lock(root)
            failures = stack_pins.check_sites(lock, root)
            self.assertEqual(1, len(failures))
            self.assertIn("does not exist", failures[0])

    def test_an_extra_occurrence_is_reported(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _write_fixture(root, _fixture_lock())
            with open(
                root / "requirements-demo.txt", "a", encoding="utf-8", newline=""
            ) as handle:
                handle.write(
                    f"other @ git+https://github.com/armpit-symphony/Demo.git@{COMMIT_A}\r\n"
                )
            lock = stack_pins.load_lock(root)
            failures = stack_pins.check_sites(lock, root)
            self.assertEqual(1, len(failures))
            self.assertIn("matched 2 occurrence", failures[0])


class RewriteTests(unittest.TestCase):
    def test_rewrite_replaces_only_the_captured_commit(self):
        site = stack_pins.Site(
            path="x",
            pattern="Demo\\.git@(?P<commit>[0-9a-f]{40})",
            occurrences=1,
        )
        text = f"prefix Demo.git@{COMMIT_A} suffix {COMMIT_A}"
        updated = stack_pins.rewrite_site(text, site, COMMIT_B)
        self.assertEqual(f"prefix Demo.git@{COMMIT_B} suffix {COMMIT_A}", updated)

    def test_bump_moves_the_lock_and_every_site(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _write_fixture(root, _fixture_lock())
            (root / "scripts").mkdir()
            for name in ("stack_pins.py", "bump-pin.py"):
                (root / "scripts" / name).write_bytes(
                    (ROOT / "scripts" / name).read_bytes()
                )
            result = subprocess.run(
                [
                    sys.executable,
                    str(root / "scripts" / "bump-pin.py"),
                    "demo-dep",
                    "--to",
                    COMMIT_B,
                ],
                capture_output=True,
                text=True,
                cwd=str(root),
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

            lock = stack_pins.load_lock(root)
            self.assertEqual(COMMIT_B, lock.dependency("demo-dep").commit)
            self.assertEqual([], stack_pins.check_sites(lock, root))

    def test_bump_preserves_crlf_line_endings(self):
        """A pin move must not rewrite every line ending in the file."""

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _write_fixture(root, _fixture_lock())
            (root / "scripts").mkdir()
            for name in ("stack_pins.py", "bump-pin.py"):
                (root / "scripts" / name).write_bytes(
                    (ROOT / "scripts" / name).read_bytes()
                )
            before = (root / "requirements-demo.txt").read_bytes()
            self.assertIn(b"\r\n", before)

            subprocess.run(
                [
                    sys.executable,
                    str(root / "scripts" / "bump-pin.py"),
                    "demo-dep",
                    "--to",
                    COMMIT_B,
                ],
                capture_output=True,
                text=True,
                cwd=str(root),
                check=True,
            )
            after = (root / "requirements-demo.txt").read_bytes()
            self.assertEqual(
                before.replace(COMMIT_A.encode(), COMMIT_B.encode()), after
            )
            self.assertEqual(before.count(b"\r\n"), after.count(b"\r\n"))

    def test_bump_refuses_a_frozen_pin_without_force(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _write_fixture(root, _fixture_lock(policy="frozen"))
            (root / "scripts").mkdir()
            for name in ("stack_pins.py", "bump-pin.py"):
                (root / "scripts" / name).write_bytes(
                    (ROOT / "scripts" / name).read_bytes()
                )
            result = subprocess.run(
                [
                    sys.executable,
                    str(root / "scripts" / "bump-pin.py"),
                    "demo-dep",
                    "--to",
                    COMMIT_B,
                ],
                capture_output=True,
                text=True,
                cwd=str(root),
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("skipped", result.stdout)
            self.assertEqual(COMMIT_A, stack_pins.load_lock(root).dependency(
                "demo-dep"
            ).commit)


if __name__ == "__main__":
    unittest.main()
