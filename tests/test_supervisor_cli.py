"""Foreground Supervisor launcher tests."""

from __future__ import annotations

from io import StringIO
import unittest

from lima_office.supervisor.cli import (
    _parser,
    _read_key_line,
    _worker_bindings,
)


class SupervisorCliTests(unittest.TestCase):
    def test_keys_are_read_from_distinct_stdin_lines(self) -> None:
        stream = StringIO("11" * 32 + "\n" + "22" * 32 + "\n")
        self.assertEqual(
            _read_key_line(stream, "operator"),
            bytes.fromhex("11" * 32),
        )
        self.assertEqual(
            _read_key_line(stream, "worker"),
            bytes.fromhex("22" * 32),
        )

    def test_missing_invalid_or_short_key_fails_closed(self) -> None:
        for value in ("", "not-hex", "11" * 31):
            with self.subTest(value=value), self.assertRaises(SystemExit):
                _read_key_line(StringIO(value + "\n"), "operator")

    def test_launcher_requires_explicit_operator_worker_and_store_bindings(
        self,
    ) -> None:
        parser = _parser()
        with self.assertRaises(SystemExit):
            parser.parse_args([])
        args = parser.parse_args(
            [
                "--tenant-id",
                "tenant-lab-001",
                "--customer-context-id",
                "customer-context-main",
                "--operator-id",
                "operator-lab-001",
                "--operator-key-id",
                "operator-key-001",
                "--worker-id",
                "arc-worker-001",
                "--worker-key-id",
                "worker-key-001",
                "--worker-url",
                "http://127.0.0.1:8123",
                "--evidence-db",
                "supervisor.db",
                "--operator-key-stdin",
                "--worker-key-stdin",
            ]
        )
        self.assertEqual(args.host, "127.0.0.1")
        self.assertEqual(args.port, 0)
        self.assertTrue(args.operator_key_stdin)
        self.assertTrue(args.worker_key_stdin)
        self.assertEqual(
            [binding.worker_id for binding in _worker_bindings(args)],
            ["arc-worker-001"],
        )

    def test_launcher_accepts_two_and_eight_explicit_worker_bindings(
        self,
    ) -> None:
        parser = _parser()
        common = [
            "--tenant-id",
            "tenant-lab-001",
            "--customer-context-id",
            "customer-context-main",
            "--operator-id",
            "operator-lab-001",
            "--operator-key-id",
            "operator-key-001",
            "--evidence-db",
            "supervisor.db",
            "--operator-key-stdin",
            "--worker-key-stdin",
        ]
        for count in (2, 8):
            worker_args = []
            for index in range(1, count + 1):
                worker_args.extend(
                    [
                        "--worker-binding",
                        f"arc-worker-{index:03d}",
                        f"worker-key-{index:03d}",
                        f"http://127.0.0.1:{8100 + index}",
                    ]
                )
            with self.subTest(count=count):
                bindings = _worker_bindings(
                    parser.parse_args(common + worker_args)
                )
                self.assertEqual(len(bindings), count)
                self.assertEqual(
                    len({binding.worker_id for binding in bindings}),
                    count,
                )

    def test_worker_binding_ambiguity_duplicates_and_limits_fail_closed(
        self,
    ) -> None:
        parser = _parser()
        common = [
            "--tenant-id",
            "tenant-lab-001",
            "--customer-context-id",
            "customer-context-main",
            "--operator-id",
            "operator-lab-001",
            "--operator-key-id",
            "operator-key-001",
            "--evidence-db",
            "supervisor.db",
            "--operator-key-stdin",
            "--worker-key-stdin",
        ]
        invalid = [
            common,
            common
            + [
                "--worker-id",
                "arc-worker-001",
                "--worker-key-id",
                "worker-key-001",
                "--worker-url",
                "http://127.0.0.1:8101",
                "--worker-binding",
                "arc-worker-002",
                "worker-key-002",
                "http://127.0.0.1:8102",
            ],
            common
            + [
                "--worker-binding",
                "arc-worker-001",
                "worker-key-001",
                "http://127.0.0.1:8101",
                "--worker-binding",
                "arc-worker-001",
                "worker-key-002",
                "http://127.0.0.1:8102",
            ],
        ]
        nine = list(common)
        for index in range(1, 10):
            nine.extend(
                [
                    "--worker-binding",
                    f"arc-worker-{index:03d}",
                    f"worker-key-{index:03d}",
                    f"http://127.0.0.1:{8100 + index}",
                ]
            )
        invalid.append(nine)
        for index, argv in enumerate(invalid):
            with self.subTest(case=index), self.assertRaises(SystemExit):
                _worker_bindings(parser.parse_args(argv))


if __name__ == "__main__":
    unittest.main()
