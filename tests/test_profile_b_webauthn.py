"""Profile B localhost WebAuthn assertion verification."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from datetime import datetime, timedelta, timezone
from http.client import HTTPConnection
from pathlib import Path
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import cbor2
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from webauthn.helpers import bytes_to_base64url

from lima_office.contracts import ContractValidator
from lima_office.runtime.profile_b_session import (
    BEGIN_CONFIRMATION,
    MemoryEvidenceStore,
    ProfileBError,
    ProfileBSessionService,
    decode_challenge,
)
from lima_office.runtime.webauthn_verifier import LocalhostWebAuthnVerifier


ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 11, 6, 0, 0, tzinfo=timezone.utc)
ORIGIN = "http://localhost:8765"


def _clock(moment: datetime):
    return lambda: moment


class LabPasskey:
    """ES256 platform credential used only by these tests."""

    def __init__(self, *, rp_id: str = "localhost") -> None:
        self.rp_id = rp_id
        self.private_key = ec.generate_private_key(ec.SECP256R1())
        self.credential_id = os.urandom(32)
        self.sign_count = 0

    def registration_and_assertion(
        self,
        challenge: bytes,
        *,
        origin: str = ORIGIN,
        uv: bool = True,
        up: bool = True,
        rp_id: str | None = None,
        assertion_sign_count: int = 1,
        tamper_signature: bool = False,
        cross_origin: bool = False,
        other_credential_id: bytes | None = None,
    ) -> dict:
        rp_id = self.rp_id if rp_id is None else rp_id
        registration = self._registration(challenge, origin=origin, uv=uv, up=up, rp_id=rp_id, cross_origin=cross_origin)
        authentication = self._authentication(
            challenge,
            origin=origin,
            uv=uv,
            up=up,
            rp_id=rp_id,
            sign_count=assertion_sign_count,
            tamper_signature=tamper_signature,
            cross_origin=cross_origin,
            credential_id=other_credential_id,
        )
        return {"registration": registration, "authentication": authentication}

    def authentication_only(
        self,
        challenge: bytes,
        *,
        origin: str = ORIGIN,
        sign_count: int | None = None,
        uv: bool = True,
        tamper_signature: bool = False,
    ) -> dict:
        count = self.sign_count + 1 if sign_count is None else sign_count
        payload = self._authentication(
            challenge,
            origin=origin,
            uv=uv,
            up=True,
            rp_id=self.rp_id,
            sign_count=count,
            tamper_signature=tamper_signature,
            cross_origin=False,
            credential_id=None,
        )
        if not tamper_signature and uv:
            self.sign_count = count
        return {"authentication": payload}

    def _registration(self, challenge, *, origin, uv, up, rp_id, cross_origin) -> dict:
        auth_data = self._auth_data(rp_id=rp_id, up=up, uv=uv, attested=True, sign_count=0)
        attestation = cbor2.dumps({"fmt": "none", "attStmt": {}, "authData": auth_data})
        client_data = _client_data("webauthn.create", challenge, origin, cross_origin)
        return _credential(self.credential_id, client_data, attestation_object=attestation)

    def _authentication(
        self,
        challenge,
        *,
        origin,
        uv,
        up,
        rp_id,
        sign_count,
        tamper_signature,
        cross_origin,
        credential_id,
    ) -> dict:
        auth_data = self._auth_data(rp_id=rp_id, up=up, uv=uv, attested=False, sign_count=sign_count)
        client_data = _client_data("webauthn.get", challenge, origin, cross_origin)
        signed = auth_data + hashlib.sha256(client_data).digest()
        signature = self.private_key.sign(signed, ec.ECDSA(hashes.SHA256()))
        if tamper_signature:
            signature = signature[:-1] + bytes([signature[-1] ^ 0x01])
        return _credential(
            self.credential_id if credential_id is None else credential_id,
            client_data,
            authenticator_data=auth_data,
            signature=signature,
        )

    def _auth_data(self, *, rp_id, up, uv, attested, sign_count) -> bytes:
        flags = 0
        if up:
            flags |= 0x01
        if uv:
            flags |= 0x04
        if attested:
            flags |= 0x40
        body = hashlib.sha256(rp_id.encode("utf-8")).digest() + bytes([flags]) + sign_count.to_bytes(4, "big")
        if not attested:
            return body
        numbers = self.private_key.public_key().public_numbers()
        cose = cbor2.dumps({
            1: 2,
            3: -7,
            -1: 1,
            -2: numbers.x.to_bytes(32, "big"),
            -3: numbers.y.to_bytes(32, "big"),
        })
        return body + bytes(16) + len(self.credential_id).to_bytes(2, "big") + self.credential_id + cose


def _client_data(kind: str, challenge: bytes, origin: str, cross_origin: bool) -> bytes:
    return json.dumps(
        {
            "type": kind,
            "challenge": bytes_to_base64url(challenge),
            "origin": origin,
            "crossOrigin": cross_origin,
        },
        separators=(",", ":"),
    ).encode("utf-8")


def _credential(credential_id: bytes, client_data: bytes, **response_parts: bytes) -> dict:
    encoded = bytes_to_base64url(credential_id)
    response = {"clientDataJSON": bytes_to_base64url(client_data)}
    for key, value in response_parts.items():
        response[_camel(key)] = bytes_to_base64url(value)
    return {"id": encoded, "rawId": encoded, "type": "public-key", "response": response}


def _camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


class ProfileBWebAuthnTests(unittest.TestCase):
    def setUp(self):
        self.moment = NOW
        self.store = MemoryEvidenceStore()
        self.verifier = LocalhostWebAuthnVerifier()
        self.sessions = ProfileBSessionService(
            self.store,
            verifier=self.verifier,
            clock=lambda: self.moment,
        )
        self.passkey = LabPasskey()
        self.validator = ContractValidator()

    def _begin(self, owner: str = "Phil") -> dict:
        return self.sessions.begin(owner_display_name=owner, confirmation=BEGIN_CONFIRMATION)

    def _enroll(self, owner: str = "Phil", **kwargs) -> dict:
        begin = self._begin(owner)
        challenge = decode_challenge(begin["challenge_b64url"])
        assertion = self.passkey.registration_and_assertion(challenge, **kwargs)
        session = self.sessions.complete(challenge_id=begin["challenge_id"], assertion=assertion)
        self.passkey.sign_count = kwargs.get("assertion_sign_count", 1)
        return {"begin": begin, "assertion": assertion, "session": session}

    def test_verified_localhost_assertion_creates_a_named_session(self):
        begin = self._begin()
        self.assertEqual("localhost_webauthn", begin["verification_mode"])
        self.assertEqual("registration_then_assertion", begin["ceremony_kind"])
        self.assertEqual("localhost", begin["public_key_request"]["rp_id"])
        self.assertEqual("localhost", begin["assertion_request"]["rp_id"])
        self.assertEqual([], begin["assertion_request"]["allow_credential_ids_b64url"])
        self.assertFalse(begin["session_created"])
        self.validator.validate(begin, "operator.profile_b.ceremony")

        logged_in = self._enroll()
        session = logged_in["session"]
        self.validator.validate(session, "operator.profile_b.session")
        self.assertEqual("Phil", session["owner_display_name"])
        self.assertTrue(session["named_owner"])
        self.assertTrue(session["device_bound"])
        self.assertEqual("webauthn_platform", session["auth_method"])
        self.assertEqual("profile_b_platform_webauthn", session["assurance_level"])
        self.assertFalse(session["survives_restart"])
        self.assertFalse(session["approval_authority"])
        self.assertFalse(session["approval_token_allowed"])
        self.assertFalse(session["arc_dispatch_allowed"])
        self.assertTrue(session["operator_authentication_manifest"])
        self.assertFalse(session["production_identity_verified"])
        self.assertEqual("stub_only", session["positive_approval_step_up"])
        summary = self.sessions.public_summary()
        self.assertTrue(summary["active"])
        self.assertNotIn("binding_id", summary)
        self.assertTrue(summary["operator_authentication_manifest"])
        self.assertFalse(summary["approval_authority"])
        rendered = json.dumps(self.store.events)
        self.assertNotIn("Phil", rendered)
        self.assertNotIn(logged_in["assertion"]["authentication"]["response"]["signature"], rendered)
        self.assertNotIn(logged_in["assertion"]["registration"]["response"]["attestationObject"], rendered)

        restarted = ProfileBSessionService(
            MemoryEvidenceStore(),
            verifier=LocalhostWebAuthnVerifier(),
            clock=_clock(NOW),
        )
        with self.assertRaises(ProfileBError):
            restarted.require_active(session["binding_id"])
        self.assertEqual("registration_then_assertion", restarted.begin(
            owner_display_name="Phil",
            confirmation=BEGIN_CONFIRMATION,
        )["ceremony_kind"])

    def test_later_assertion_in_the_same_process_verifies_and_a_clone_does_not(self):
        session = self._enroll()["session"]
        begin = self._begin()
        self.assertEqual("assertion", begin["ceremony_kind"])
        self.assertIsNone(begin["public_key_request"])
        self.assertEqual(
            [bytes_to_base64url(self.passkey.credential_id)],
            begin["assertion_request"]["allow_credential_ids_b64url"],
        )
        self.validator.validate(begin, "operator.profile_b.ceremony")
        challenge = decode_challenge(begin["challenge_b64url"])
        again = self.sessions.complete(
            challenge_id=begin["challenge_id"],
            assertion=self.passkey.authentication_only(challenge),
        )
        self.assertNotEqual(session["binding_id"], again["binding_id"])
        self.assertFalse(again["survives_restart"])
        with self.assertRaises(ProfileBError):
            self.sessions.require_active(session["binding_id"])

        cloned = self._begin()
        cloned_challenge = decode_challenge(cloned["challenge_b64url"])
        with self.assertRaises(ProfileBError):
            self.sessions.complete(
                challenge_id=cloned["challenge_id"],
                assertion=self.passkey.authentication_only(cloned_challenge, sign_count=self.passkey.sign_count),
            )
        self.assertEqual(again["binding_id"], self.sessions.require_active(again["binding_id"])["binding_id"])

    def test_tampered_or_unverified_assertions_create_no_session(self):
        cases = {
            "tampered_signature": {"tamper_signature": True},
            "numeric_loopback_origin": {"origin": "http://127.0.0.1:8765"},
            "foreign_origin": {"origin": "https://evil.example"},
            "wrong_rp_id": {"rp_id": "evil.example"},
            "user_not_verified": {"uv": False},
            "cross_origin": {"cross_origin": True},
            "credential_mismatch": {"other_credential_id": os.urandom(32)},
        }
        for name, kwargs in cases.items():
            with self.subTest(name=name):
                service = ProfileBSessionService(
                    MemoryEvidenceStore(),
                    verifier=LocalhostWebAuthnVerifier(),
                    clock=_clock(NOW),
                )
                begin = service.begin(owner_display_name="Phil", confirmation=BEGIN_CONFIRMATION)
                challenge = decode_challenge(begin["challenge_b64url"])
                with self.assertRaises(ProfileBError):
                    service.complete(
                        challenge_id=begin["challenge_id"],
                        assertion=LabPasskey().registration_and_assertion(challenge, **kwargs),
                    )
                self.assertFalse(service.public_summary()["active"])
                self.assertNotIn("binding_id", service.public_summary())
                self.assertEqual(
                    "registration_then_assertion",
                    service.begin(owner_display_name="Phil", confirmation=BEGIN_CONFIRMATION)["ceremony_kind"],
                )

        service = ProfileBSessionService(
            MemoryEvidenceStore(),
            verifier=LocalhostWebAuthnVerifier(),
            clock=_clock(NOW),
        )
        begin = service.begin(owner_display_name="Phil", confirmation=BEGIN_CONFIRMATION)
        with self.assertRaises(ProfileBError):
            service.complete(challenge_id=begin["challenge_id"], assertion={"id": "not-a-proof"})
        begin = service.begin(owner_display_name="Phil", confirmation=BEGIN_CONFIRMATION)
        challenge = decode_challenge(begin["challenge_b64url"])
        registration = LabPasskey().registration_and_assertion(challenge)["registration"]
        with self.assertRaises(ProfileBError):
            service.complete(challenge_id=begin["challenge_id"], assertion={"registration": registration})
        self.assertFalse(service.public_summary()["active"])

    def test_assertion_is_bound_to_the_named_owner_and_one_challenge(self):
        logged_in = self._enroll()
        replay = self._begin()
        challenge = decode_challenge(replay["challenge_b64url"])
        assertion = self.passkey.authentication_only(challenge, sign_count=self.passkey.sign_count + 1)
        self.sessions.complete(challenge_id=replay["challenge_id"], assertion=assertion)
        with self.assertRaises(ProfileBError):
            self.sessions.complete(challenge_id=replay["challenge_id"], assertion=assertion)

        other = ProfileBSessionService(
            MemoryEvidenceStore(),
            verifier=self.verifier,
            clock=_clock(NOW),
        )
        foreign = other.begin(owner_display_name="Ada", confirmation=BEGIN_CONFIRMATION)
        self.assertEqual("registration_then_assertion", foreign["ceremony_kind"])
        foreign_challenge = decode_challenge(foreign["challenge_b64url"])
        with self.assertRaises(ProfileBError):
            other.complete(
                challenge_id=foreign["challenge_id"],
                assertion=self.passkey.authentication_only(foreign_challenge, sign_count=99),
            )
        self.assertFalse(other.public_summary()["active"])
        self.assertTrue(self.sessions.public_summary()["active"])
        self.assertNotIn(logged_in["session"]["binding_id"], json.dumps(other.public_summary()))

        self.moment = NOW + timedelta(seconds=121)
        expired = self.sessions.begin(owner_display_name="Phil", confirmation=BEGIN_CONFIRMATION)
        self.moment = NOW + timedelta(seconds=121 + 120)
        with self.assertRaises(ProfileBError) as caught:
            self.sessions.complete(
                challenge_id=expired["challenge_id"],
                assertion=self.passkey.authentication_only(decode_challenge(expired["challenge_b64url"])),
            )
        self.assertIn("expired", str(caught.exception))

    def test_manifest_flags_and_loopback_refusals_stay_closed(self):
        spec = importlib.util.spec_from_file_location(
            "build_lab_preview_webauthn",
            ROOT / "scripts" / "build-lab-preview.py",
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        manifest = module.build_manifest("profile-b-webauthn", "2" * 40)
        self.assertTrue(manifest["operator_authentication"])
        self.assertFalse(manifest["production_ready"])
        self.assertFalse(manifest["customer_pilot_allowed"])
        source = (ROOT / "lima_office" / "runtime" / "webauthn_verifier.py").read_text(encoding="utf-8").lower()
        self.assertNotIn("sparkbot", source)
        self.assertNotIn("import socket", source)
        self.assertNotIn("import requests", source)

        verifier = LocalhostWebAuthnVerifier()
        profile_b = ProfileBSessionService(MemoryEvidenceStore(), verifier=verifier, clock=_clock(NOW))
        harness_spec = importlib.util.spec_from_file_location(
            "_arc_runtime_harness_webauthn",
            ROOT / "scripts" / "arc-runtime-harness.py",
        )
        harness = importlib.util.module_from_spec(harness_spec)
        harness_spec.loader.exec_module(harness)

        class FakeHarness:
            mode = "training"

            def state(self):
                return {"mode": "training", "office_integration": {"connected": True, "inventory": {"workers": []}}}

            def refresh_office_workers(self):
                return {"workers": [], "runtime_authority_blocked": True, "approval_authority": False}

        server = harness.HarnessHTTPServer(
            ("127.0.0.1", 0),
            FakeHarness(),
            b"arc",
            b"office",
            profile_b=profile_b,
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            host, port = server.server_address
            base = f"http://{host}:{port}"
            with urlopen(f"{base}/api/v1/health", timeout=3) as response:
                health = json.loads(response.read())
            self.assertTrue(health["operator_authentication"])
            self.assertFalse(health["production_ready"])
            self.assertFalse(health["customer_pilot_allowed"])

            body = b"{}"
            denied = Request(
                f"{base}/api/v1/workers",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with self.assertRaises(HTTPError) as caught:
                urlopen(denied, timeout=3)
            self.assertEqual(401, caught.exception.code)

            foreign = HTTPConnection(host, port, timeout=3)
            foreign.request("POST", "/api/v1/workers", body=body, headers={
                "Host": "evil.example",
                "Content-Type": "application/json",
                "Content-Length": str(len(body)),
            })
            refused = foreign.getresponse()
            self.assertEqual(403, refused.status)
            refused.read()
            foreign.close()

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
            challenge = decode_challenge(begin["challenge_b64url"])
            complete_req = Request(
                f"{base}/api/v1/operator-session/profile-b/complete",
                data=json.dumps({
                    "challenge_id": begin["challenge_id"],
                    "assertion": self.passkey.registration_and_assertion(challenge),
                }).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(complete_req, timeout=3) as response:
                session = json.loads(response.read())
            self.assertEqual("webauthn_platform", session["auth_method"])
            self.assertFalse(session["approval_authority"])
            self.assertTrue(session["operator_authentication_manifest"])
            self.assertFalse(session["arc_dispatch_allowed"])
            self.assertEqual("stub_only", session["positive_approval_step_up"])
            self.assertFalse(session["survives_restart"])
            with urlopen(f"{base}/api/v1/operator-session", timeout=3) as response:
                status = json.loads(response.read())
            self.assertTrue(status["active"])
            self.assertTrue(status["operator_authentication_manifest"])
            self.assertFalse(status["approval_authority"])
            self.assertEqual("stub_only", status["positive_approval_step_up"])
            self.assertNotIn("binding_id", status)
            self.assertNotIn(session["binding_id"], json.dumps(status))
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


if __name__ == "__main__":
    unittest.main()
