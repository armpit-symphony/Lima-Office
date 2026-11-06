"""Profile B operator login: named owner, device-bound, process-local.

The default verifier checks a localhost WebAuthn assertion before a session
exists. A lab HMAC verifier and an operator-configured platform helper remain
explicit overrides. Positive approval step-up is a stub and is never issued.
"""

from __future__ import annotations

import base64
from collections.abc import Callable, Mapping
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import re
import subprocess
from typing import Any, Protocol
from uuid import uuid4

from lima_office.contracts import ContractValidator
from lima_office.guardian import GuardianPolicy
from lima_office.runtime.lab_packaging import OPERATOR_AUTHENTICATION_MANIFEST
from lima_office.runtime.webauthn_verifier import LocalhostWebAuthnVerifier


BEGIN_CONFIRMATION = "BEGIN PROFILE B OPERATOR LOGIN"
POLICY_VERSION = "policy-operator-profile-b-session-lab-v1"
SESSION_TTL_SECONDS = 1800
STEP_UP_TTL_SECONDS = 300
CHALLENGE_TTL_SECONDS = 120
HELPER_TIMEOUT_SECONDS = 15
HELPER_STDOUT_LIMIT = 8 * 1024
_OWNER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 .'-]{0,79}$")
_CHALLENGE_RE = re.compile(r"^profile-b-challenge:[0-9a-f]{32}$")
_HEX32_RE = re.compile(r"^[0-9a-f]{32}$")
_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_CREDENTIAL_ID_RE = re.compile(r"^[A-Za-z0-9_-]{16,256}$")
_BANNED_EVIDENCE_FRAGMENTS = (
    "assertion",
    "challenge_b64",
    "password",
    "private_key",
    "secret",
    "token",
)


class ProfileBError(RuntimeError):
    """Safe failure for the Profile B ceremony. Details stay static."""

    def __init__(self, message: str, *, code: str = "ceremony_rejected") -> None:
        super().__init__(message)
        self.code = code


class ProfileBStore(Protocol):
    def record_event(self, event_type: str, payload: Mapping[str, Any]) -> str: ...


class CeremonyVerifier(Protocol):
    verification_mode: str

    def begin(self, *, owner_display_name: str | None = None) -> Mapping[str, Any]: ...

    def complete(
        self,
        *,
        challenge: bytes,
        assertion: Any,
        owner_display_name: str | None = None,
    ) -> Mapping[str, Any]: ...


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * ((4 - len(value) % 4) % 4)
    return base64.urlsafe_b64decode(value + padding)


class MemoryEvidenceStore:
    """Process-local evidence sink for tests and the fail-closed default."""

    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, Any], str]] = []

    def record_event(self, event_type: str, payload: Mapping[str, Any]) -> str:
        event_id = f"memory-event:{len(self.events):04d}"
        self.events.append((event_type, dict(payload), event_id))
        return event_id


class FailClosedWebAuthnSpikeVerifier:
    """Test double that offers a browser ceremony and never accepts it.

    The harness default is ``LocalhostWebAuthnVerifier``. This double remains
    so tests can prove an unverified ceremony still creates no session.
    """

    verification_mode = "fail_closed"

    def begin(self, *, owner_display_name: str | None = None) -> Mapping[str, Any]:
        del owner_display_name
        return {"ceremony_available": True, "offer_browser_ceremony": True, "ceremony_kind": None}

    def complete(
        self,
        *,
        challenge: bytes,
        assertion: Any,
        owner_display_name: str | None = None,
    ) -> Mapping[str, Any]:
        del challenge, assertion, owner_display_name
        return {"verified": False}


class LabHmacCeremonyVerifier:
    """In-process ceremony for tests. The key never leaves this object."""

    verification_mode = "lab_hmac"

    def __init__(self, key: bytes) -> None:
        if not isinstance(key, bytes) or len(key) < 32:
            raise ProfileBError("The lab ceremony verifier is not configured.", code="ceremony_unavailable")
        self._key = key
        digest = hashlib.sha256(self._key).hexdigest()
        self._device_binding_ref = digest[:32]
        self._credential_id_hash = "sha256:" + digest

    def begin(self, *, owner_display_name: str | None = None) -> Mapping[str, Any]:
        del owner_display_name
        return {"ceremony_available": True, "offer_browser_ceremony": False, "ceremony_kind": None}

    def assertion_for(self, challenge: bytes) -> str:
        return hmac.new(self._key, challenge, hashlib.sha256).hexdigest()

    def complete(
        self,
        *,
        challenge: bytes,
        assertion: Any,
        owner_display_name: str | None = None,
    ) -> Mapping[str, Any]:
        del owner_display_name
        if not isinstance(assertion, str) or not re.fullmatch(r"[0-9a-f]{64}", assertion):
            return {"verified": False}
        expected = hmac.new(self._key, challenge, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, assertion):
            return {"verified": False}
        return {
            "verified": True,
            "device_binding_ref": self._device_binding_ref,
            "credential_id_hash": self._credential_id_hash,
            "assurance_level": "profile_b_lab_ceremony",
            "auth_method": "lab_hmac_ceremony",
        }


class PlatformHelperCeremonyVerifier:
    """Call an operator-configured absolute helper. Stderr is discarded."""

    verification_mode = "platform_helper"

    def __init__(self, path: Any) -> None:
        self.path = path

    def _executable(self) -> Any:
        candidate = self.path
        if not getattr(candidate, "is_absolute", lambda: False)() or not candidate.is_file():
            return None
        return candidate

    def begin(self, *, owner_display_name: str | None = None) -> Mapping[str, Any]:
        del owner_display_name
        if self._executable() is None:
            return {"ceremony_available": False, "offer_browser_ceremony": False, "ceremony_kind": None}
        return {"ceremony_available": True, "offer_browser_ceremony": True, "ceremony_kind": None}

    def complete(
        self,
        *,
        challenge: bytes,
        assertion: Any,
        owner_display_name: str | None = None,
    ) -> Mapping[str, Any]:
        del owner_display_name
        executable = self._executable()
        if executable is None:
            raise ProfileBError(
                "The platform ceremony helper is not available.",
                code="ceremony_unavailable",
            )
        request = {
            "action": "complete",
            "challenge_b64url": _b64url(challenge),
            "assertion": assertion,
        }
        raw = json.dumps(request, sort_keys=True).encode("utf-8")
        if len(raw) > 64 * 1024:
            return {"verified": False}
        try:
            completed = subprocess.run(
                [str(executable)],
                input=raw,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                timeout=HELPER_TIMEOUT_SECONDS,
                check=False,
                shell=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return {"verified": False}
        if completed.returncode != 0 or len(completed.stdout) > HELPER_STDOUT_LIMIT:
            return {"verified": False}
        try:
            parsed = json.loads(completed.stdout.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            return {"verified": False}
        if not isinstance(parsed, dict) or parsed.get("verified") is not True:
            return {"verified": False}
        device = parsed.get("device_binding_ref")
        credential = parsed.get("credential_id_hash")
        if not isinstance(device, str) or not _HEX32_RE.fullmatch(device):
            return {"verified": False}
        if not isinstance(credential, str) or not _SHA256_RE.fullmatch(credential):
            return {"verified": False}
        return {
            "verified": True,
            "device_binding_ref": device,
            "credential_id_hash": credential,
            "assurance_level": "profile_b_platform_webauthn",
            "auth_method": "webauthn_platform",
        }


def _assert_safe_evidence(payload: Mapping[str, Any]) -> None:
    for key, value in payload.items():
        lowered = str(key).lower()
        if any(fragment in lowered for fragment in _BANNED_EVIDENCE_FRAGMENTS):
            raise ProfileBError("Evidence payload was rejected.")
        if isinstance(value, str) and len(value) > 500:
            raise ProfileBError("Evidence payload was rejected.")
        if isinstance(value, (dict, list)):
            raise ProfileBError("Evidence payload was rejected.")


class ProfileBSessionService:
    """Named-owner Profile B session. Restart drops it. Approval stays off."""

    def __init__(
        self,
        store: ProfileBStore,
        *,
        verifier: CeremonyVerifier | None = None,
        tenant_id: str = "tenant-lab-001",
        customer_context_id: str = "customer-context-main",
        validator: ContractValidator | None = None,
        guardian: GuardianPolicy | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.store = store
        self.verifier = verifier or LocalhostWebAuthnVerifier()
        self.tenant_id = tenant_id
        self.customer_context_id = customer_context_id
        self.validator = validator or ContractValidator()
        self.guardian = guardian or GuardianPolicy()
        self.clock = clock or _utc_now
        self._challenges: dict[str, dict[str, Any]] = {}
        self._active: dict[str, Any] | None = None

    def step_up_stub(self) -> dict[str, Any]:
        """Document the later positive-approval step-up without issuing one."""

        return {
            "positive_approval_step_up": "stub_only",
            "step_up_issued": False,
            "step_up_ttl_seconds": STEP_UP_TTL_SECONDS,
            "approval_token_allowed": False,
            "approval_authority": False,
        }

    def state_summary(self) -> dict[str, Any]:
        record = self._current_record()
        return {
            "runtime_enabled": True,
            "active": record is not None,
            "binding": record,
            "process_bound": True,
            "survives_restart": False,
            "production_identity_verified": False,
            "approval_authority": False,
            "verification_mode": self.verifier.verification_mode,
        }

    def public_summary(self) -> dict[str, Any]:
        """Loopback status read. The session handle is not republished."""

        record = self._current_record()
        summary: dict[str, Any] = {
            "profile_id": "windows_hello_passkey",
            "active": record is not None,
            "survives_restart": False,
            "approval_authority": False,
            "production_identity_verified": False,
            "customer_or_production_use_allowed": False,
            "operator_authentication_manifest": OPERATOR_AUTHENTICATION_MANIFEST,
            "verification_mode": self.verifier.verification_mode,
            "binding_published": False,
            "positive_approval_step_up": "stub_only",
        }
        if record is not None:
            summary["assurance_level"] = record["assurance_level"]
            summary["owner_display_name"] = record["owner_display_name"]
            summary["expires_at"] = record["expires_at"]
            summary["auth_method"] = record["auth_method"]
        return summary

    def begin(self, *, owner_display_name: Any, confirmation: Any) -> dict[str, Any]:
        if confirmation != BEGIN_CONFIRMATION:
            raise ProfileBError(
                "Explicit Profile B confirmation is required.",
                code="request_invalid",
            )
        if not isinstance(owner_display_name, str) or not _OWNER_RE.fullmatch(owner_display_name):
            raise ProfileBError(
                "Owner display name must be a short label without control characters.",
                code="request_invalid",
            )
        offered = dict(self.verifier.begin(owner_display_name=owner_display_name))
        now = self.clock()
        ceremony_kind = offered.get("ceremony_kind")
        if ceremony_kind not in {None, "registration_then_assertion", "assertion"}:
            ceremony_kind = None
        if offered.get("ceremony_available") is not True:
            return self._ceremony(
                now=now,
                status="ceremony_unavailable",
                ceremony_available=False,
                verification_mode=self.verifier.verification_mode,
                ceremony_kind=None,
                challenge_id=None,
                challenge_b64url=None,
                public_key_request=None,
                assertion_request=None,
                owner_display_name_accepted=True,
                detail="Windows Hello / passkey ceremony is not available on this host.",
                expires_at=None,
            )
        token = uuid4().hex
        challenge = token.encode("ascii")
        challenge_id = f"profile-b-challenge:{token}"
        challenge_b64url = _b64url(challenge)
        allow_ids = _allow_credential_ids(offered.get("allow_credential_ids_b64url"))
        public_key = None
        assertion_request = None
        if ceremony_kind == "assertion":
            if not allow_ids:
                return self._ceremony(
                    now=now,
                    status="ceremony_unavailable",
                    ceremony_available=False,
                    verification_mode=self.verifier.verification_mode,
                    ceremony_kind=None,
                    challenge_id=None,
                    challenge_b64url=None,
                    public_key_request=None,
                    assertion_request=None,
                    owner_display_name_accepted=True,
                    detail="Windows Hello / passkey ceremony is not available on this host.",
                    expires_at=None,
                )
            assertion_request = _assertion_request(challenge_b64url, allow_ids)
            detail = "Sign the Profile B assertion. No session exists yet."
        else:
            if offered.get("offer_browser_ceremony") is True:
                public_key = {
                    "rp_id": "localhost",
                    "rp_name": "LIMA Office",
                    "user_display_name": owner_display_name,
                    "user_id_b64url": _b64url(uuid4().bytes),
                    "challenge_b64url": challenge_b64url,
                    "user_verification": "required",
                    "authenticator_attachment": "platform",
                    "timeout_ms": CHALLENGE_TTL_SECONDS * 1000,
                    "attestation": "none",
                    "resident_key": "preferred",
                }
            if ceremony_kind == "registration_then_assertion":
                if public_key is None:
                    ceremony_kind = None
                else:
                    assertion_request = _assertion_request(challenge_b64url, [])
            detail = "Complete the Profile B ceremony. No session exists yet."
            if ceremony_kind == "registration_then_assertion":
                detail = "Create the passkey, then sign the assertion. No session exists yet."
        self._record(
            "operator_profile_b_ceremony_requested",
            {
                "challenge_id": challenge_id,
                "verification_mode": self.verifier.verification_mode,
                "owner_display_name_sha256": hashlib.sha256(owner_display_name.encode()).hexdigest(),
                "credentials_collected": False,
                "session_created": False,
                "approval_authority": False,
            },
        )
        expires = now + timedelta(seconds=CHALLENGE_TTL_SECONDS)
        self._challenges[challenge_id] = {
            "challenge": challenge,
            "owner_display_name": owner_display_name,
            "expires_at": expires,
        }
        return self._ceremony(
            now=now,
            status="challenge_issued",
            ceremony_available=True,
            verification_mode=self.verifier.verification_mode,
            ceremony_kind=ceremony_kind,
            challenge_id=challenge_id,
            challenge_b64url=challenge_b64url,
            public_key_request=public_key,
            assertion_request=assertion_request,
            owner_display_name_accepted=True,
            detail=detail,
            expires_at=_timestamp(expires),
        )

    def complete(self, *, challenge_id: Any, assertion: Any) -> dict[str, Any]:
        if not isinstance(challenge_id, str) or not _CHALLENGE_RE.fullmatch(challenge_id):
            raise ProfileBError("The ceremony challenge is not active.", code="ceremony_rejected")
        pending = self._challenges.pop(challenge_id, None)
        if pending is None or self.clock() >= pending["expires_at"]:
            raise ProfileBError("The ceremony challenge expired.", code="ceremony_rejected")
        try:
            verified = dict(
                self.verifier.complete(
                    challenge=pending["challenge"],
                    assertion=assertion,
                    owner_display_name=pending["owner_display_name"],
                )
            )
        except ProfileBError:
            self._reject(challenge_id)
            raise
        except Exception as exc:
            self._reject(challenge_id)
            raise ProfileBError("The ceremony assertion was not accepted.", code="ceremony_rejected") from exc
        if verified.get("verified") is not True:
            self._reject(challenge_id)
            raise ProfileBError(
                "The ceremony assertion was not accepted. No session was created.",
                code="ceremony_rejected",
            )
        return self._commit_session(pending["owner_display_name"], verified)

    def require_active(self, binding_id: Any) -> dict[str, Any]:
        record = self._current_record()
        if not isinstance(binding_id, str) or record is None or record["binding_id"] != binding_id:
            raise ProfileBError("The Profile B operator session is not active.")
        self.validator.validate(record, "operator.profile_b.session")
        return dict(record)

    def _commit_session(self, owner_display_name: str, verified: Mapping[str, Any]) -> dict[str, Any]:
        device = verified.get("device_binding_ref")
        credential = verified.get("credential_id_hash")
        auth_method = verified.get("auth_method")
        assurance = verified.get("assurance_level")
        if not isinstance(device, str) or not isinstance(credential, str):
            raise ProfileBError("The ceremony assertion was not accepted.", code="ceremony_rejected")
        if auth_method not in {"lab_hmac_ceremony", "webauthn_platform"}:
            raise ProfileBError("The ceremony assertion was not accepted.", code="ceremony_rejected")
        if assurance not in {"profile_b_lab_ceremony", "profile_b_platform_webauthn"}:
            raise ProfileBError("The ceremony assertion was not accepted.", code="ceremony_rejected")
        now = self.clock()
        token = uuid4().hex
        binding_id = f"operator-profile-b-session:{token}"
        operator_id = "operator-profile-b:" + hashlib.sha256(
            f"{self.tenant_id}:{owner_display_name}:{device}:{token}".encode()
        ).hexdigest()[:24]
        evidence_id = f"ev-operator-profile-b:{token}"
        safe = {
            "binding_id": binding_id,
            "operator_id": operator_id,
            "auth_method": auth_method,
            "assurance_level": assurance,
            "device_binding_ref": device,
            "credential_id_hash": credential,
            "owner_display_name_sha256": hashlib.sha256(owner_display_name.encode()).hexdigest(),
            "raw_os_username_stored": False,
            "credentials_collected": False,
            "approval_authority": False,
            "session_created": False,
        }
        pre = self._record("operator_profile_b_login_requested", safe)
        context = self._guardian_context(
            token=token,
            binding_id=binding_id,
            operator_id=operator_id,
            evidence_id=evidence_id,
            pre_ref=pre,
        )
        decision = self.guardian.decide("operator_profile_b_login", context)
        self.validator.validate(decision, "guardian.decision")
        if decision["decision"] not in {"allow", "allow_with_evidence"}:
            raise ProfileBError("Guardian denied the Profile B login.", code="ceremony_rejected")
        expires = now + timedelta(seconds=SESSION_TTL_SECONDS)
        post = self._record(
            "operator_profile_b_login_committed",
            {**safe, "session_created": True, "guardian_decision_id": decision["decision_id"],
             "expires_at": _timestamp(expires)},
        )
        record = {
            **self._envelope(now, token),
            "binding_id": binding_id,
            "operator_id": operator_id,
            "auth_method": auth_method,
            "assurance_level": assurance,
            "status": "active",
            "owner_display_name": owner_display_name,
            "named_owner": True,
            "device_bound": True,
            "device_binding_ref": device,
            "credential_id_hash": credential,
            "local_loopback_only": True,
            "process_bound": True,
            "survives_process_restart": False,
            "survives_restart": False,
            "raw_os_username_stored": False,
            "credentials_collected": False,
            "pin_required": False,
            "mfa_verified": True,
            "production_identity_verified": False,
            "customer_or_production_use_allowed": False,
            "approval_authority": False,
            "approval_result_allowed": False,
            "approval_token_allowed": False,
            "arc_dispatch_allowed": False,
            "positive_approval_step_up": "stub_only",
            "step_up_issued": False,
            "step_up_ttl_seconds": STEP_UP_TTL_SECONDS,
            "session_ttl_seconds": SESSION_TTL_SECONDS,
            "runtime_authority_blocked": True,
            "operator_authentication_manifest": OPERATOR_AUTHENTICATION_MANIFEST,
            "guardian_decision_id": decision["decision_id"],
            "pre_action_evidence_ref": pre,
            "post_action_evidence_ref": post,
            "issued_at": _timestamp(now),
            "expires_at": _timestamp(expires),
        }
        self.validator.validate(record, "operator.profile_b.session")
        self._active = record
        return dict(record)

    def _reject(self, challenge_id: str) -> None:
        self._record(
            "operator_profile_b_ceremony_rejected",
            {
                "challenge_id": challenge_id,
                "result": "rejected",
                "session_created": False,
                "approval_authority": False,
                "credentials_collected": False,
            },
        )

    def _record(self, event_type: str, payload: Mapping[str, Any]) -> str:
        _assert_safe_evidence(payload)
        try:
            return self.store.record_event(event_type, payload)
        except ProfileBError:
            raise
        except Exception as exc:
            raise ProfileBError("Evidence failed; Profile B login was denied.", code="ceremony_rejected") from exc

    def _current_record(self) -> dict[str, Any] | None:
        record = dict(self._active) if self._active is not None else None
        if record is None:
            return None
        if self.clock() >= _parse_timestamp(record["expires_at"]):
            return None
        return record

    def _envelope(self, now: datetime, token: str) -> dict[str, Any]:
        return {
            "contract_name": "operator.profile_b.session",
            "contract_version": "1.0.0",
            "schema_version": "1.0.0",
            "tenant_id": self.tenant_id,
            "customer_context_id": self.customer_context_id,
            "environment": "phase0_lab",
            "correlation_id": f"corr-operator-profile-b-{token}",
            "causation_id": None,
            "idempotency_key": f"idem-operator-profile-b-{token}",
            "producer": {"component": "operator_console", "produced_at": _timestamp(now)},
            "policy_version": POLICY_VERSION,
        }

    def _ceremony(
        self,
        *,
        now: datetime,
        status: str,
        ceremony_available: bool,
        verification_mode: str,
        ceremony_kind: str | None,
        challenge_id: str | None,
        challenge_b64url: str | None,
        public_key_request: dict[str, Any] | None,
        assertion_request: dict[str, Any] | None,
        owner_display_name_accepted: bool,
        detail: str,
        expires_at: str | None,
    ) -> dict[str, Any]:
        token = uuid4().hex
        record = {
            "contract_name": "operator.profile_b.ceremony",
            "contract_version": "1.0.0",
            "schema_version": "1.0.0",
            "tenant_id": self.tenant_id,
            "customer_context_id": self.customer_context_id,
            "environment": "phase0_lab",
            "correlation_id": f"corr-profile-b-ceremony-{token}",
            "causation_id": None,
            "idempotency_key": f"idem-profile-b-ceremony-{token}",
            "producer": {"component": "operator_console", "produced_at": _timestamp(now)},
            "policy_version": POLICY_VERSION,
            "status": status,
            "ceremony_available": ceremony_available,
            "verification_mode": verification_mode,
            "ceremony_kind": ceremony_kind,
            "challenge_id": challenge_id,
            "challenge_b64url": challenge_b64url,
            "public_key_request": public_key_request,
            "assertion_request": assertion_request,
            "owner_display_name_accepted": owner_display_name_accepted,
            "session_created": False,
            "binding_id": None,
            "detail": detail,
            "local_loopback_only": True,
            "credentials_collected": False,
            "approval_authority": False,
            "runtime_authority_blocked": True,
            "positive_approval_step_up": "stub_only",
            "survives_restart": False,
            "expires_at": expires_at,
        }
        self.validator.validate(record, "operator.profile_b.ceremony")
        return record

    def _guardian_context(
        self,
        *,
        token: str,
        binding_id: str,
        operator_id: str,
        evidence_id: str,
        pre_ref: str,
    ) -> dict[str, Any]:
        return {
            "decision_id": f"gd-operator-profile-b:{token}",
            "request_id": f"request-operator-profile-b:{token}",
            "tenant_id": self.tenant_id,
            "customer_context_id": self.customer_context_id,
            "subject": {"subject_type": "operator", "subject_id": operator_id},
            "schema_action_class": "internal_operator_session_binding",
            "resource_ref": {
                "resource_type": "operator_session",
                "resource_id": binding_id,
                "resource_scope": "operator_scoped",
            },
            "data_classification": "internal",
            "risk_tier": "low",
            "policy_refs": [
                "policy.operator.profile-b.session.lab.v1",
                "policy.guardian.syscall_gate.v1",
            ],
            "policy_version": POLICY_VERSION,
            "valid_for_action_ref": binding_id,
            "decision_scope_hash": "sha256:" + hashlib.sha256(binding_id.encode()).hexdigest(),
            "bound_action_type": "operator_profile_b_login",
            "bound_tool_scope": {
                "resource_refs": [binding_id],
                "allowed_operations": ["bind_profile_b_local_session"],
                "prohibited_operations": [
                    "approve_request",
                    "issue_token",
                    "dispatch_arc",
                    "connector_access",
                    "external_effect",
                ],
            },
            "execution_mode": "identity_metadata_only",
            "external_effect": "none",
            "evidence_required": True,
            "evidence_artifact_id": evidence_id,
            "evidence_artifact_ids": [evidence_id],
            "pre_action_evidence_refs": [evidence_id],
            "post_action_evidence_refs": [evidence_id],
            "storage_evidence_ref": pre_ref,
            "attended": True,
            "operator_confirmation": True,
            "local_loopback_only": True,
            "process_bound": True,
            "raw_os_username_stored": False,
            "credentials_collected": False,
            "production_identity_verified": False,
            "approval_authority": False,
            "approval_result_allowed": False,
            "approval_token_access_allowed": False,
            "arc_dispatch_allowed": False,
            "connector_access_allowed": False,
            "submission_allowed": False,
            "approval_required": False,
            "phishing_resistant_step_up": True,
            "named_owner": True,
            "device_bound": True,
            "mfa_verified": True,
            "survives_process_restart": False,
            "positive_approval_step_up_issued": False,
            "step_up_stub_only": True,
            "ceremony_verified": True,
        }


def _allow_credential_ids(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    allowed: list[str] = []
    for item in value:
        if isinstance(item, str) and _CREDENTIAL_ID_RE.fullmatch(item) and item not in allowed:
            allowed.append(item)
        if len(allowed) == 8:
            break
    return allowed


def _assertion_request(challenge_b64url: str, allow_ids: list[str]) -> dict[str, Any]:
    return {
        "rp_id": "localhost",
        "challenge_b64url": challenge_b64url,
        "user_verification": "required",
        "timeout_ms": CHALLENGE_TTL_SECONDS * 1000,
        "allow_credential_ids_b64url": allow_ids,
    }


def decode_challenge(challenge_b64url: str) -> bytes:
    """Test helper so clients can answer a lab HMAC challenge."""

    return _b64url_decode(challenge_b64url)
