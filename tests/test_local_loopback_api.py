"""Loopback API v1 authz and the Profile B ceremony spike."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import importlib.util
import json
from http.client import HTTPConnection
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from lima_office.guardian import GuardianPolicy
from lima_office.runtime.local_loopback_api import (
    ROUTES,
    LocalApiError,
    LocalLoopbackApi,
    LoopbackBindError,
    assert_loopback_bind,
    client_is_loopback,
    host_header_is_loopback,
)
from lima_office.runtime.operator_session import BIND_CONFIRMATION, AttendedOperatorSessionService
from lima_office.runtime.profile_b_session import (
    BEGIN_CONFIRMATION,
    FailClosedWebAuthnSpikeVerifier,
    LabHmacCeremonyVerifier,
    MemoryEvidenceStore,
    PlatformHelperCeremonyVerifier,
    ProfileBError,
    ProfileBSessionService,
    decode_challenge,
)


ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 11, 6, 0, 0, tzinfo=timezone.utc)
LAB_KEY = b"lab-profile-b-test-key-32-bytes!"


def _clock(moment: datetime):
    return lambda: moment


class LoopbackRuleTests(unittest.TestCase):
    def test_bind_accepts_only_ipv4_loopback(self):
        assert_loopback_bind("127.0.0.1")
        for host in ("0.0.0.0", "::", "::1", "localhost", "10.0.0.8"):
            with self.assertRaises(LoopbackBindError):
                assert_loopback_bind(host)

    def test_client_and_host_header_stay_on_loopback(self):
        self.assertTrue(client_is_loopback("127.0.0.1"))
        self.assertFalse(client_is_loopback("10.1.1.1"))
        self.assertTrue(host_header_is_loopback("127.0.0.1:8766", 8766))
        self.assertTrue(host_header_is_loopback("localhost:8766", 8766))
        self.assertFalse(host_header_is_loopback("evil.example", 8766))
        self.assertFalse(host_header_is_loopback("127.0.0.1:1", 8766))


class ProfileBCeremonyTests(unittest.TestCase):
    def setUp(self):
        self.moment = NOW
        self.store = MemoryEvidenceStore()
        self.verifier = LabHmacCeremonyVerifier(LAB_KEY)
        self.sessions = ProfileBSessionService(
            self.store,
            verifier=self.verifier,
            clock=lambda: self.moment,
        )

    def _login(self, owner: str = "Phil") -> dict:
        begin = self.sessions.begin(owner_display_name=owner, confirmation=BEGIN_CONFIRMATION)
        assertion = self.verifier.assertion_for(decode_challenge(begin["challenge_b64url"]))
        session = self.sessions.complete(challenge_id=begin["challenge_id"], assertion=assertion)
        return {"begin": begin, "assertion": assertion, "session": session}

    def test_lab_verifier_creates_a_non_authorizing_session(self):
        logged_in = self._login()
        session = logged_in["session"]
        self.assertTrue(session["named_owner"])
        self.assertTrue(session["device_bound"])
        self.assertTrue(session["mfa_verified"])
        self.assertFalse(session["survives_restart"])
        self.assertFalse(session["approval_authority"])
        self.assertFalse(session["approval_token_allowed"])
        self.assertFalse(session["arc_dispatch_allowed"])
        self.assertFalse(session["operator_authentication_manifest"])
        self.assertEqual("stub_only", session["positive_approval_step_up"])
        self.assertFalse(session["step_up_issued"])
        self.assertEqual(self.sessions.step_up_stub()["approval_token_allowed"], False)
        self.assertNotIn("Phil", json.dumps(self.store.events))
        self.assertNotIn(logged_in["assertion"], json.dumps(self.store.events))
        self.assertNotIn(LAB_KEY.decode(), json.dumps(self.store.events))

    def test_session_does_not_survive_a_new_process_or_ttl(self):
        session = self._login()["session"]
        restarted = ProfileBSessionService(
            self.store,
            verifier=self.verifier,
            clock=lambda: self.moment,
        )
        with self.assertRaises(ProfileBError):
            restarted.require_active(session["binding_id"])
        self.moment = NOW + timedelta(seconds=1801)
        with self.assertRaises(ProfileBError):
            self.sessions.require_active(session["binding_id"])

    def test_challenge_is_one_time_and_fail_closed_verifier_creates_no_session(self):
        begin = self.sessions.begin(owner_display_name="Phil", confirmation=BEGIN_CONFIRMATION)
        assertion = self.verifier.assertion_for(decode_challenge(begin["challenge_b64url"]))
        self.sessions.complete(challenge_id=begin["challenge_id"], assertion=assertion)
        with self.assertRaises(ProfileBError):
            self.sessions.complete(challenge_id=begin["challenge_id"], assertion=assertion)

        spike = ProfileBSessionService(
            MemoryEvidenceStore(),
            verifier=FailClosedWebAuthnSpikeVerifier(),
            clock=_clock(NOW),
        )
        offered = spike.begin(owner_display_name="Phil", confirmation=BEGIN_CONFIRMATION)
        self.assertTrue(offered["ceremony_available"])
        self.assertEqual("localhost", offered["public_key_request"]["rp_id"])
        self.assertEqual("required", offered["public_key_request"]["user_verification"])
        with self.assertRaises(ProfileBError):
            spike.complete(challenge_id=offered["challenge_id"], assertion={"id": "not-a-proof"})
        self.assertFalse(spike.public_summary()["active"])
        self.assertNotIn("binding_id", spike.public_summary())

    def test_platform_helper_is_explicit_and_fail_closed(self):
        relative = ProfileBSessionService(
            MemoryEvidenceStore(),
            verifier=PlatformHelperCeremonyVerifier(Path("helper")),
            clock=_clock(NOW),
        )
        unavailable = relative.begin(owner_display_name="Phil", confirmation=BEGIN_CONFIRMATION)
        self.assertEqual("ceremony_unavailable", unavailable["status"])
        self.assertFalse(unavailable["session_created"])

        with tempfile.TemporaryDirectory() as raw:
            helper = Path(raw) / "profile-b-helper.py"
            helper.write_text(
                "#!/usr/bin/env python3\n"
                "import json, sys\n"
                "payload = json.load(sys.stdin)\n"
                "verified = payload.get('assertion') == 'helper-ok'\n"
                "json.dump({\n"
                "  'verified': verified,\n"
                "  'device_binding_ref': 'ab' * 16,\n"
                "  'credential_id_hash': 'sha256:' + ('cd' * 32),\n"
                "}, sys.stdout)\n",
                encoding="utf-8",
            )
            helper.chmod(0o755)
            service = ProfileBSessionService(
                MemoryEvidenceStore(),
                verifier=PlatformHelperCeremonyVerifier(helper),
                clock=_clock(NOW),
            )
            begin = service.begin(owner_display_name="Ada", confirmation=BEGIN_CONFIRMATION)
            with self.assertRaises(ProfileBError):
                service.complete(challenge_id=begin["challenge_id"], assertion="helper-no")
            begin = service.begin(owner_display_name="Ada", confirmation=BEGIN_CONFIRMATION)
            session = service.complete(challenge_id=begin["challenge_id"], assertion="helper-ok")
            self.assertEqual("webauthn_platform", session["auth_method"])
            self.assertFalse(session["approval_authority"])
            self.assertNotIn("helper-ok", json.dumps(service.store.events))

    def test_guardian_denies_an_unverified_profile_b_login(self):
        decision = GuardianPolicy().decide("operator_profile_b_login", {"tenant_id": "tenant-lab-001"})
        self.assertEqual("deny", decision["decision"])


class ApiAuthorizationTests(unittest.TestCase):
    def test_unauthenticated_mutating_routes_are_denied(self):
        api = LocalLoopbackApi(clock=_clock(NOW))
        checked = 0
        for route in ROUTES:
            if route.method != "POST" or route.auth != "session_required":
                continue
            checked += 1
            with self.assertRaises(LocalApiError) as caught:
                api.dispatch(route.method, route.path, {}, None)
            self.assertEqual(401, caught.exception.status)
            self.assertEqual("unauthenticated", caught.exception.code)
        self.assertGreaterEqual(checked, 8)
        with self.assertRaises(LocalApiError) as unknown:
            api.dispatch("POST", "/api/v1/not-a-route", {}, None)
        self.assertEqual(401, unknown.exception.status)

    def test_public_reads_keep_manifest_flags_false(self):
        api = LocalLoopbackApi(clock=_clock(NOW))
        health = api.health()
        descriptor = api.descriptor()
        self.assertFalse(health["production_ready"])
        self.assertFalse(health["customer_pilot_allowed"])
        self.assertFalse(health["operator_authentication"])
        self.assertEqual("127.0.0.1", health["bind_host"])
        self.assertFalse(descriptor["anonymous_mutating_routes"])
        self.assertFalse(descriptor["foreign_operator_shell_dependency"])
        self.assertEqual(
            [(route.method, route.path, route.auth, route.mutating) for route in ROUTES],
            [(item["method"], item["path"], item["auth"], item["mutating"]) for item in descriptor["routes"]],
        )

    def test_profile_a_lab_flag_can_refuse_the_legacy_bind_on_v1(self):
        api = LocalLoopbackApi(profile_a_lab_enabled=False, clock=_clock(NOW))
        with self.assertRaises(LocalApiError) as caught:
            api.dispatch(
                "POST",
                "/api/v1/operator-session/bind",
                {"confirmation": BIND_CONFIRMATION},
                None,
            )
        self.assertEqual("profile_a_disabled", caught.exception.code)

    def test_manifest_builder_keeps_pilot_flags_false(self):
        spec = importlib.util.spec_from_file_location(
            "build_lab_preview_profile_b",
            ROOT / "scripts" / "build-lab-preview.py",
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        manifest = module.build_manifest("profile-b-slice", "1" * 40)
        self.assertFalse(manifest["production_ready"])
        self.assertFalse(manifest["customer_pilot_allowed"])
        self.assertFalse(manifest["operator_authentication"])

    def test_new_runtime_modules_do_not_reference_a_foreign_shell(self):
        for relative in (
            "lima_office/runtime/profile_b_session.py",
            "lima_office/runtime/local_loopback_api.py",
            "scripts/arc-runtime-harness.py",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8").lower()
            self.assertNotIn("sparkbot", text)


class HarnessApiTests(unittest.TestCase):
    def _server(self, *, profile_b=None, sessions=None):
        spec = importlib.util.spec_from_file_location(
            "_arc_runtime_harness_profile_b",
            ROOT / "scripts" / "arc-runtime-harness.py",
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        class FakeHarness:
            mode = "training"

            def state(self):
                return {
                    "mode": "training",
                    "office_integration": {"connected": True, "inventory": {"workers": []}},
                }

            def refresh_office_workers(self):
                return {"workers": [], "runtime_authority_blocked": True, "approval_authority": False}

        server = module.HarnessHTTPServer(
            ("127.0.0.1", 0),
            FakeHarness(),
            b"arc",
            b"office",
            operator_sessions=sessions,
            profile_b=profile_b,
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return module, server, thread

    def test_harness_refuses_a_non_loopback_bind(self):
        spec = importlib.util.spec_from_file_location(
            "_arc_runtime_harness_bind",
            ROOT / "scripts" / "arc-runtime-harness.py",
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with self.assertRaises(LoopbackBindError):
            module.HarnessHTTPServer(("0.0.0.0", 0), object(), b"arc", b"office")

    def test_http_denies_unauthenticated_mutation_and_accepts_profile_b(self):
        verifier = LabHmacCeremonyVerifier(LAB_KEY)
        profile_b = ProfileBSessionService(MemoryEvidenceStore(), verifier=verifier, clock=_clock(NOW))
        module, server, thread = self._server(profile_b=profile_b)
        try:
            host, port = server.server_address
            base = f"http://{host}:{port}"
            with urlopen(f"{base}/api/v1/health", timeout=3) as response:
                health = json.loads(response.read())
            self.assertEqual("ready", health["status"])
            self.assertFalse(health["operator_authentication"])
            self.assertFalse(health["production_ready"])
            self.assertFalse(health["customer_pilot_allowed"])

            with urlopen(f"{base}/api/office/state", timeout=3) as response:
                self.assertEqual("true", response.headers.get("Deprecation"))
                self.assertIn("/api/v1", response.headers.get("Link", ""))

            body = json.dumps({}).encode()
            denied = Request(
                f"{base}/api/v1/workers",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with self.assertRaises(HTTPError) as caught:
                urlopen(denied, timeout=3)
            self.assertEqual(401, caught.exception.code)
            payload = json.loads(caught.exception.read())
            self.assertEqual("unauthenticated", payload["error"])
            self.assertFalse(payload["approval_authority"])

            foreign_host = HTTPConnection(host, port, timeout=3)
            foreign_host.request("POST", "/api/v1/workers", body=body, headers={
                "Host": "evil.example",
                "Content-Type": "application/json",
                "Content-Length": str(len(body)),
            })
            foreign = foreign_host.getresponse()
            self.assertEqual(403, foreign.status)
            foreign.read()
            foreign_host.close()

            begin_req = Request(
                f"{base}/api/v1/operator-session/profile-b/begin",
                data=json.dumps({
                    "owner_display_name": "Phil",
                    "confirmation": BEGIN_CONFIRMATION,
                }).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(begin_req, timeout=3) as response:
                begin = json.loads(response.read())
            assertion = verifier.assertion_for(decode_challenge(begin["challenge_b64url"]))
            complete_req = Request(
                f"{base}/api/v1/operator-session/profile-b/complete",
                data=json.dumps({
                    "challenge_id": begin["challenge_id"],
                    "assertion": assertion,
                }).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(complete_req, timeout=3) as response:
                session = json.loads(response.read())
            self.assertFalse(session["approval_authority"])
            status_req = urlopen(f"{base}/api/v1/operator-session", timeout=3)
            status = json.loads(status_req.read())
            self.assertTrue(status["active"])
            self.assertNotIn("binding_id", status)
            self.assertNotIn(assertion, json.dumps(status))
            allowed = Request(
                f"{base}/api/v1/workers",
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Lima-Operator-Session": session["binding_id"],
                },
                method="POST",
            )
            with urlopen(allowed, timeout=3) as response:
                workers = json.loads(response.read())
            self.assertFalse(workers["approval_authority"])
            self.assertTrue(workers["runtime_authority_blocked"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)
            del module

    def test_profile_a_session_satisfies_v1_and_legacy_alias_remains(self):
        from lima_office.runtime.operator_harness import HarnessStateStore

        with tempfile.TemporaryDirectory() as raw:
            store = HarnessStateStore(Path(raw) / "state.sqlite3")
            sessions = AttendedOperatorSessionService(
                store,
                clock=_clock(NOW),
                subject_provider=lambda: "Local User",
            )
            module, server, thread = self._server(sessions=sessions)
            try:
                host, port = server.server_address
                base = f"http://{host}:{port}"
                bind = Request(
                    f"{base}/api/office/operator-session/bind",
                    data=json.dumps({"confirmation": BIND_CONFIRMATION}).encode(),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urlopen(bind, timeout=3) as response:
                    legacy = json.loads(response.read())
                    self.assertEqual("true", response.headers.get("Deprecation"))
                workers = Request(
                    f"{base}/api/v1/workers",
                    data=b"{}",
                    headers={
                        "Content-Type": "application/json",
                        "X-Lima-Operator-Session": legacy["binding_id"],
                    },
                    method="POST",
                )
                with urlopen(workers, timeout=3) as response:
                    self.assertEqual(200, response.status)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)
                store.close()


class ProfileBUiTests(unittest.TestCase):
    def test_console_offers_profile_b_without_leaving_localhost(self):
        source = (ROOT / "ui" / "lima_office_supervisor_console.html").read_text(encoding="utf-8")
        self.assertIn("Sign in with Windows Hello / passkey", source)
        self.assertIn("/api/v1/operator-session/profile-b/begin", source)
        self.assertIn("BEGIN PROFILE B OPERATOR LOGIN", source)
        self.assertIn("Lab-only Profile A", source)
        self.assertIn('fetch("/api/office/workers"', source)
        self.assertIn('fetch("/api/v1/workers"', source)
        self.assertNotIn("http://", source)
        self.assertNotIn("https://", source)
        self.assertNotIn("setInterval", source)


if __name__ == "__main__":
    unittest.main()
