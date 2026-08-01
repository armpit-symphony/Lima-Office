"""Foreground Supervisor launcher tests."""

from __future__ import annotations

from io import StringIO
import unittest

from lima_office.supervisor.cli import _parser, _read_key_line


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


if __name__ == "__main__":
    unittest.main()
