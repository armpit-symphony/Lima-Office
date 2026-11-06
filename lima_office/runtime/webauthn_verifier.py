"""Localhost WebAuthn assertion verification for Profile B.

A session is created only when ``complete`` returns ``verified: True``.
Registration may store a public key, and only after the matching assertion
signature verifies. Credential records stay in process memory. See
``docs/PROFILE_B_WEBAUTHN_VERIFICATION.md``.
"""

from __future__ import annotations

import base64
from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
import re
import threading
from typing import Any


RP_ID = "localhost"
_ORIGIN_RE = re.compile(r"^https?://localhost(?::([0-9]{1,5}))?$")
_CREDENTIAL_ID_RE = re.compile(r"^[A-Za-z0-9_-]{16,256}$")
_MAX_FIELD = 16_384
_MAX_DEPTH = 6
_MIN_CREDENTIAL_ID = 16
_MAX_CREDENTIAL_ID = 128


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _load_webauthn() -> tuple[Any, Any] | None:
    try:
        import webauthn
        from webauthn.helpers.cose import COSEAlgorithmIdentifier
    except ImportError:
        return None
    return webauthn, COSEAlgorithmIdentifier


def _bounded(value: Any, depth: int = 0) -> bool:
    if depth > _MAX_DEPTH:
        return False
    if value is None or isinstance(value, bool):
        return True
    if isinstance(value, str):
        return len(value) <= _MAX_FIELD
    if isinstance(value, dict):
        if len(value) > 12:
            return False
        return all(
            isinstance(key, str) and len(key) <= 64 and _bounded(item, depth + 1)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return len(value) <= 8 and all(_bounded(item, depth + 1) for item in value)
    return False


def _localhost_origin(client_data_json: bytes) -> str | None:
    try:
        parsed = json.loads(client_data_json.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        return None
    if not isinstance(parsed, dict):
        return None
    if parsed.get("crossOrigin") is True:
        return None
    origin = parsed.get("origin")
    if not isinstance(origin, str) or len(origin) > 64:
        return None
    match = _ORIGIN_RE.fullmatch(origin)
    if match is None:
        return None
    port = match.group(1)
    if port is not None:
        number = int(port)
        if number < 1 or number > 65535 or port != str(number):
            return None
    return origin


def _client_data_json(credential: Mapping[str, Any], webauthn: Any) -> bytes | None:
    response = credential.get("response")
    if not isinstance(response, dict):
        return None
    encoded = response.get("clientDataJSON")
    if not isinstance(encoded, str):
        return None
    try:
        return webauthn.base64url_to_bytes(encoded)
    except Exception:
        return None


def _credential_id(credential: Mapping[str, Any], webauthn: Any) -> bytes | None:
    raw_id = credential.get("rawId")
    if not isinstance(raw_id, str) or not _CREDENTIAL_ID_RE.fullmatch(raw_id):
        return None
    try:
        decoded = webauthn.base64url_to_bytes(raw_id)
    except Exception:
        return None
    if not _MIN_CREDENTIAL_ID <= len(decoded) <= _MAX_CREDENTIAL_ID:
        return None
    if _b64url(decoded) != raw_id:
        return None
    return decoded


@dataclass
class _StoredCredential:
    owner_display_name: str
    credential_id: bytes
    credential_id_b64url: str
    public_key: bytes
    sign_count: int


class LocalhostWebAuthnVerifier:
    """Verify ES256 WebAuthn assertions for RP ID ``localhost`` only."""

    verification_mode = "localhost_webauthn"

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._by_owner: dict[str, _StoredCredential] = {}

    def begin(self, *, owner_display_name: str | None = None) -> Mapping[str, Any]:
        if _load_webauthn() is None or not isinstance(owner_display_name, str):
            return {
                "ceremony_available": False,
                "offer_browser_ceremony": False,
                "ceremony_kind": None,
            }
        with self._lock:
            stored = self._by_owner.get(owner_display_name)
            if stored is None:
                return {
                    "ceremony_available": True,
                    "offer_browser_ceremony": True,
                    "ceremony_kind": "registration_then_assertion",
                    "allow_credential_ids_b64url": [],
                }
            return {
                "ceremony_available": True,
                "offer_browser_ceremony": False,
                "ceremony_kind": "assertion",
                "allow_credential_ids_b64url": [stored.credential_id_b64url],
            }

    def complete(
        self,
        *,
        challenge: bytes,
        assertion: Any,
        owner_display_name: str | None = None,
    ) -> Mapping[str, Any]:
        loaded = _load_webauthn()
        if loaded is None or not isinstance(owner_display_name, str) or not isinstance(challenge, bytes):
            return {"verified": False}
        if not _bounded(assertion):
            return {"verified": False}
        webauthn, algorithm = loaded
        try:
            if _is_registration_then_assertion(assertion):
                return self._verify_registration_then_assertion(
                    webauthn,
                    algorithm,
                    challenge=challenge,
                    assertion=assertion,
                    owner_display_name=owner_display_name,
                )
            if _is_assertion(assertion):
                return self._verify_stored_assertion(
                    webauthn,
                    challenge=challenge,
                    assertion=assertion,
                    owner_display_name=owner_display_name,
                )
        except Exception:
            return {"verified": False}
        return {"verified": False}

    def _verify_registration_then_assertion(
        self,
        webauthn: Any,
        algorithm: Any,
        *,
        challenge: bytes,
        assertion: Mapping[str, Any],
        owner_display_name: str,
    ) -> Mapping[str, Any]:
        registration = assertion.get("registration")
        authentication = assertion.get("authentication")
        if not isinstance(registration, dict) or not isinstance(authentication, dict):
            return {"verified": False}
        origin = _shared_origin(registration, authentication, webauthn)
        if origin is None:
            return {"verified": False}
        registered = webauthn.verify_registration_response(
            credential=registration,
            expected_challenge=challenge,
            expected_rp_id=RP_ID,
            expected_origin=origin,
            require_user_presence=True,
            require_user_verification=True,
            supported_pub_key_algs=[algorithm.ECDSA_SHA_256],
        )
        credential_id = _credential_id(authentication, webauthn)
        if credential_id is None or credential_id != registered.credential_id:
            return {"verified": False}
        authenticated = webauthn.verify_authentication_response(
            credential=authentication,
            expected_challenge=challenge,
            expected_rp_id=RP_ID,
            expected_origin=origin,
            credential_public_key=registered.credential_public_key,
            credential_current_sign_count=0,
            require_user_verification=True,
        )
        if authenticated.credential_id != registered.credential_id:
            return {"verified": False}
        self._store(
            owner_display_name,
            credential_id=registered.credential_id,
            public_key=registered.credential_public_key,
            sign_count=authenticated.new_sign_count,
        )
        return _accepted(registered.credential_id)

    def _verify_stored_assertion(
        self,
        webauthn: Any,
        *,
        challenge: bytes,
        assertion: Mapping[str, Any],
        owner_display_name: str,
    ) -> Mapping[str, Any]:
        authentication = assertion.get("authentication") if "authentication" in assertion else assertion
        if not isinstance(authentication, dict):
            return {"verified": False}
        client_data = _client_data_json(authentication, webauthn)
        if client_data is None:
            return {"verified": False}
        origin = _localhost_origin(client_data)
        if origin is None:
            return {"verified": False}
        credential_id = _credential_id(authentication, webauthn)
        if credential_id is None:
            return {"verified": False}
        with self._lock:
            stored = self._by_owner.get(owner_display_name)
            if stored is None or stored.credential_id != credential_id:
                return {"verified": False}
            authenticated = webauthn.verify_authentication_response(
                credential=authentication,
                expected_challenge=challenge,
                expected_rp_id=RP_ID,
                expected_origin=origin,
                credential_public_key=stored.public_key,
                credential_current_sign_count=stored.sign_count,
                require_user_verification=True,
            )
            if authenticated.credential_id != credential_id:
                return {"verified": False}
            stored.sign_count = authenticated.new_sign_count
        return _accepted(credential_id)

    def _store(
        self,
        owner_display_name: str,
        *,
        credential_id: bytes,
        public_key: bytes,
        sign_count: int,
    ) -> None:
        encoded = _b64url(credential_id)
        if not _CREDENTIAL_ID_RE.fullmatch(encoded):
            raise ValueError("credential id is outside the lab bound")
        record = _StoredCredential(
            owner_display_name=owner_display_name,
            credential_id=credential_id,
            credential_id_b64url=encoded,
            public_key=public_key,
            sign_count=sign_count,
        )
        with self._lock:
            self._by_owner[owner_display_name] = record


def _is_registration_then_assertion(assertion: Any) -> bool:
    return isinstance(assertion, dict) and "registration" in assertion


def _is_assertion(assertion: Any) -> bool:
    if not isinstance(assertion, dict) or "registration" in assertion:
        return False
    if "authentication" in assertion:
        return True
    response = assertion.get("response")
    return isinstance(response, dict) and "signature" in response


def _shared_origin(registration: Mapping[str, Any], authentication: Mapping[str, Any], webauthn: Any) -> str | None:
    registered = _client_data_json(registration, webauthn)
    authenticated = _client_data_json(authentication, webauthn)
    if registered is None or authenticated is None:
        return None
    origin = _localhost_origin(registered)
    if origin is None or origin != _localhost_origin(authenticated):
        return None
    return origin


def _accepted(credential_id: bytes) -> dict[str, Any]:
    digest = hashlib.sha256(credential_id).hexdigest()
    return {
        "verified": True,
        "device_binding_ref": digest[:32],
        "credential_id_hash": "sha256:" + digest,
        "assurance_level": "profile_b_platform_webauthn",
        "auth_method": "webauthn_platform",
    }
