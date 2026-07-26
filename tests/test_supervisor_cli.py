"""Foreground Supervisor launcher tests."""

from __future__ import annotations

from io import StringIO

import pytest

from lima_office.supervisor.cli import _parser, _read_key_line


def test_keys_are_read_from_distinct_stdin_lines() -> None:
    stream = StringIO("11" * 32 + "\n" + "22" * 32 + "\n")
    assert _read_key_line(stream, "operator") == bytes.fromhex("11" * 32)
    assert _read_key_line(stream, "worker") == bytes.fromhex("22" * 32)


@pytest.mark.parametrize("value", ["", "not-hex", "11" * 31])
def test_missing_invalid_or_short_key_fails_closed(value: str) -> None:
    with pytest.raises(SystemExit):
        _read_key_line(StringIO(value + "\n"), "operator")


def test_launcher_requires_explicit_operator_worker_and_store_bindings() -> None:
    parser = _parser()
    with pytest.raises(SystemExit):
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
    assert args.host == "127.0.0.1"
    assert args.port == 0
    assert args.operator_key_stdin is True
    assert args.worker_key_stdin is True
