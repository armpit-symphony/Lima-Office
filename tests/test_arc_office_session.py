"""Proofs for the governed Arc office session launcher.

The launcher is convenience around the real processes, so the things worth
testing are the places convenience could quietly change behaviour: the gates
must stay off by default, readiness must still fail closed, the resource types
must be ones the contract actually admits, and a denial must be reported with
its real cause rather than a downstream symptom.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
_LAUNCHER = ROOT / "scripts" / "arc-office-session.py"
_spec = importlib.util.spec_from_file_location("arc_office_session", _LAUNCHER)
assert _spec is not None and _spec.loader is not None
session_mod = importlib.util.module_from_spec(_spec)
sys.modules["arc_office_session"] = session_mod
_spec.loader.exec_module(session_mod)


def _guardian_resource_types() -> list[str]:
    schema = json.loads(
        (ROOT / "contracts" / "v1" / "guardian.decision.schema.json").read_text(
            encoding="utf-8"
        )
    )
    found: list[str] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            properties = node.get("properties")
            if isinstance(properties, dict):
                resource_type = properties.get("resource_type")
                if isinstance(resource_type, dict) and "enum" in resource_type:
                    found.extend(resource_type["enum"])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(schema)
    return found


class ResourceTypeTests(unittest.TestCase):
    """The contract enumerates resource_type; the launcher must respect it."""

    def test_resource_types_are_contract_members(self):
        allowed = _guardian_resource_types()
        self.assertIn(session_mod.DOCUMENT_RESOURCE_TYPE, allowed)
        self.assertIn(session_mod.WORKER_RESOURCE_TYPE, allowed)

    def test_a_document_is_a_file_not_a_document(self):
        """'document' is not a contract member and is denied before Guardian."""

        self.assertEqual("file", session_mod.DOCUMENT_RESOURCE_TYPE)
        self.assertNotIn("document", _guardian_resource_types())


class GateDefaultTests(unittest.TestCase):
    """Convenience must not turn a gate on."""

    def _args(self, *extra: str):
        return session_mod._parser().parse_args(
            ["--arc-source", str(ROOT), *extra]
        )

    def test_both_opt_ins_default_off(self):
        args = self._args()
        self.assertFalse(args.execution_opt_in)
        self.assertFalse(args.execute_granted_capability)

    def test_content_and_document_root_default_off(self):
        args = self._args()
        self.assertFalse(args.emit_document_content)
        self.assertIsNone(args.document_root)

    def test_each_opt_in_is_independent(self):
        supervisor_only = self._args("--execution-opt-in")
        self.assertTrue(supervisor_only.execution_opt_in)
        self.assertFalse(supervisor_only.execute_granted_capability)

        arc_only = self._args("--execute-granted-capability")
        self.assertFalse(arc_only.execution_opt_in)
        self.assertTrue(arc_only.execute_granted_capability)


class ReadinessTests(unittest.TestCase):
    """Readiness parsing must still fail closed."""

    class _FakeProcess:
        def __init__(self, line: str) -> None:
            import io

            self.stdout = io.StringIO(line)
            self.stderr = io.StringIO("")

        def poll(self):
            return None

        def terminate(self):
            pass

        def wait(self, timeout=None):
            return 0

        def kill(self):
            pass

    def _ready(self, payload: dict) -> dict:
        process = self._FakeProcess(json.dumps(payload) + "\n")
        return session_mod._readiness(process, "component")

    def test_accepts_a_ready_non_executing_component(self):
        ready = self._ready(
            {"status": "ready", "executable": False, "port": 51234}
        )
        self.assertEqual(51234, ready["port"])

    def test_rejects_a_component_claiming_it_can_execute(self):
        with self.assertRaises(session_mod.SessionError):
            self._ready({"status": "ready", "executable": True, "port": 51234})

    def test_rejects_a_component_that_is_not_ready(self):
        with self.assertRaises(session_mod.SessionError):
            self._ready(
                {"status": "starting", "executable": False, "port": 51234}
            )

    def test_rejects_an_invalid_port(self):
        for port in (0, -1, "51234", None):
            with self.subTest(port=port):
                with self.assertRaises(session_mod.SessionError):
                    self._ready(
                        {"status": "ready", "executable": False, "port": port}
                    )

    def test_rejects_non_json_readiness(self):
        with self.assertRaises(session_mod.SessionError):
            session_mod._readiness(self._FakeProcess("not json\n"), "component")


class SummaryTests(unittest.TestCase):
    """A denial must name its real cause, not a downstream symptom."""

    def test_upstream_denial_is_reported_with_its_reason_codes(self):
        output = json.dumps(
            {
                "status": "denied",
                "reason_codes": ["recon_missing_guardian_decision"],
                "execution": {
                    "performed": False,
                    "reason_code": "execution_grant_absent",
                },
            }
        )
        summary = session_mod._summarize(output)

        # Without the status line this reads as an opt-in problem, and the
        # operator goes looking at the wrong gate.
        self.assertIn("denied", summary)
        self.assertIn("recon_missing_guardian_decision", summary)

    def test_successful_read_reports_bytes_and_capability(self):
        output = json.dumps(
            {
                "status": "acknowledged",
                "execution_grant": {"grant_id": "grant:1"},
                "execution": {
                    "performed": True,
                    "byte_count": 61,
                    "capability": "document_read",
                    "side_effects_performed": False,
                },
            }
        )
        summary = session_mod._summarize(output)

        self.assertIn("issued", summary)
        self.assertIn("61", summary)
        self.assertIn("document_read", summary)

    def test_content_block_is_appended_after_the_summary(self):
        output = (
            json.dumps(
                {
                    "status": "acknowledged",
                    "execution": {"performed": True, "byte_count": 5},
                }
            )
            + "\n--- BEGIN DOCUMENT CONTENT 'r.txt' (5 bytes) ---\nhello\n"
            "--- END DOCUMENT CONTENT ---\n"
        )
        summary = session_mod._summarize(output)

        self.assertIn("hello", summary)
        self.assertNotIn("BEGIN DOCUMENT CONTENT", summary)
        self.assertLess(summary.index("performed"), summary.index("hello"))

    def test_unparseable_output_is_passed_through(self):
        self.assertEqual("boom", session_mod._summarize("boom\n"))

    def test_side_effects_are_always_restated(self):
        output = json.dumps(
            {"status": "acknowledged", "execution": {"performed": False}}
        )
        self.assertIn("side effects", session_mod._summarize(output))


class KeyHandlingTests(unittest.TestCase):
    """Channel keys must not be printed, logged, or persisted."""

    def test_session_keys_are_distinct_and_not_exposed_in_info(self):
        import argparse

        args = argparse.Namespace(
            tenant_id="t", worker_id="w", document_root=None,
            execution_opt_in=False, execute_granted_capability=False,
            emit_document_content=False,
        )
        session = session_mod.ArcOfficeSession(args, Path("."))
        session.worker_port = 1
        session.supervisor_port = 2

        rendered = session_mod._info(session)
        self.assertNotIn(session._operator_key.hex(), rendered)
        self.assertNotIn(session._worker_key.hex(), rendered)
        self.assertNotEqual(session._operator_key, session._worker_key)

    def test_keys_are_full_length(self):
        import argparse

        session = session_mod.ArcOfficeSession(argparse.Namespace(), Path("."))
        self.assertEqual(32, len(session._operator_key))
        self.assertEqual(32, len(session._worker_key))


if __name__ == "__main__":
    unittest.main()
