"""In-memory metadata-only evidence writer for Phase 1A mock runtime."""

from __future__ import annotations

import hashlib
import copy
import json
import re
from typing import Any

from lima_office.contracts.validator import ContractValidator
from lima_office.guardian.decision import FIXED_CREATED_AT, normalize_action_class
from lima_office.runtime.errors import EvidenceRequiredError, EvidenceWriteError


class EvidenceWriter:
    """Creates test-only schema-shaped evidence metadata in memory only."""

    def __init__(self, validator: ContractValidator, fail_writes: bool = False) -> None:
        self.validator = validator
        self.fail_writes = fail_writes
        self._artifacts: dict[str, dict[str, Any]] = {}
        self._failures: dict[str, dict[str, Any]] = {}
        self._counter = 0

    @property
    def artifacts(self) -> dict[str, dict[str, Any]]:
        return copy.deepcopy(self._artifacts)

    @property
    def failures(self) -> dict[str, dict[str, Any]]:
        return copy.deepcopy(self._failures)

    def write_artifact(
        self,
        *,
        artifact_type: str,
        subject_id: str,
        subject_type: str = "task",
        action: str = "tool_invocation",
        tenant_id: str = "tenant-lab-001",
        customer_context_id: str = "customer-context-main",
        guardian_decision_id: str | None = None,
        correlation_id: str | None = None,
        causation_id: str | None = None,
        summary: str = "Phase 1A mock evidence metadata.",
    ) -> dict[str, Any]:
        if self.fail_writes:
            failure = self.write_failure(
                affected_contract=subject_type,
                action=action,
                tenant_id=tenant_id,
                customer_context_id=customer_context_id,
                guardian_decision_id=guardian_decision_id or "gd-evidence-write-failed",
                task_id=subject_id if subject_type == "task" else None,
            )
            raise EvidenceWriteError(f"mock evidence write failed: {failure['evidence_failure_id']}")
        if guardian_decision_id is None:
            raise EvidenceWriteError("action evidence requires Guardian decision linkage")
        self._validate_summary(summary)

        self._counter += 1
        artifact_id = f"ev-phase1a-{self._counter:04d}"
        payload_hash = self._hash(
            {
                "artifact_id": artifact_id,
                "artifact_type": artifact_type,
                "subject_id": subject_id,
                "action": action,
                "summary": summary,
            }
        )
        artifact = {
            "contract_name": "evidence.artifact",
            "contract_version": "1.0.0",
            "schema_version": "1.0.0",
            "tenant_id": tenant_id,
            "customer_context_id": customer_context_id,
            "environment": "phase0_lab",
            "correlation_id": correlation_id or f"corr-{artifact_id}",
            "causation_id": causation_id,
            "idempotency_key": f"idem-{artifact_id}",
            "artifact_id": artifact_id,
            "artifact_type": artifact_type,
            "producer": {"component": "supervisor", "produced_at": FIXED_CREATED_AT},
            "actor": {"actor_type": "supervisor", "actor_id": "supervisor-lab-001"},
            "subject": {"subject_type": subject_type, "subject_id": subject_id},
            "action_class": normalize_action_class(action),
            "risk_tier": "low" if action in {"mock_diagnostic", "read_only_diagnostic", "internal_note"} else "blocked",
            "data_classification": "internal",
            "guardian_decision_id": guardian_decision_id,
            "approval_request_id": None,
            "approval_token_id": None,
            "policy_version": "policy-phase1a-mock-v1",
            "policy_snapshot_hash": "hash-ref-phase1a-policy",
            "redaction_status": "metadata_only",
            "redaction_profile": "operator_safe_summary",
            "redacted_fields": ["raw_payload"],
            "retention_class": "short_term_operator_review",
            "retention_policy_ref": "retention-rule-phase1a-mock",
            "retention_expires_at": None,
            "delete_eligible": False,
            "storage_ref": {
                "location_ref": f"in-memory-evidence:{artifact_id}",
                "contains_sensitive_payload": False,
                "secret_material_present": False,
            },
            "payload_hash": payload_hash,
            "integrity_ref": f"integrity-ref-{payload_hash}",
            "previous_artifact_id": self._previous_artifact_id(),
            "access_control_ref": "access-control-ref-phase1a-operator-review",
            "export_eligible": False,
            "export_redaction_profile": "customer_safe_summary",
            "summary": summary,
            "created_at": FIXED_CREATED_AT,
        }
        artifact = self.validator.validate(artifact, "evidence.artifact")
        self._artifacts[artifact_id] = copy.deepcopy(artifact)
        return copy.deepcopy(artifact)

    def require_evidence(self, evidence_artifact_ids: list[str] | None) -> None:
        if not evidence_artifact_ids:
            raise EvidenceRequiredError("evidence artifact refs are required")
        missing = [artifact_id for artifact_id in evidence_artifact_ids if artifact_id not in self._artifacts]
        if missing:
            raise EvidenceRequiredError(f"unknown evidence artifact refs: {', '.join(missing)}")

    def write_failure(
        self,
        *,
        affected_contract: str,
        action: str,
        tenant_id: str,
        customer_context_id: str,
        guardian_decision_id: str,
        task_id: str | None = None,
        worker_id: str | None = None,
        failure_stage: str = "pre_action",
        failure_code: str = "ledger_unavailable",
    ) -> dict[str, Any]:
        failure_id = f"ef-phase1a-{len(self._failures) + 1:04d}"
        failure_hash = self._hash({"failure_id": failure_id, "affected_contract": affected_contract, "action": action})
        pre_action = failure_stage == "pre_action"
        failure = {
            "contract_name": "evidence.failure",
            "contract_version": "1.0.0",
            "schema_version": "1.0.0",
            "tenant_id": tenant_id,
            "customer_context_id": customer_context_id,
            "environment": "blocked_mvp" if pre_action else "phase0_lab",
            "correlation_id": f"corr-{failure_id}",
            "causation_id": guardian_decision_id,
            "idempotency_key": f"idem-{failure_id}",
            "evidence_failure_id": failure_id,
            "producer": {"component": "supervisor", "produced_at": FIXED_CREATED_AT},
            "failure_stage": failure_stage,
            "failure_code": failure_code,
            "affected_contract": affected_contract,
            "affected_action_class": normalize_action_class(action),
            "evidence_required": True,
            "pre_action_blocked": pre_action,
            "post_action_degraded": not pre_action,
            "action_blocked": pre_action,
            "task_id": task_id,
            "worker_id": worker_id,
            "tool_invocation_id": None,
            "last_successful_evidence_artifact_id": self._previous_artifact_id(),
            "failure_record_ref": f"in-memory-evidence-failure:{failure_id}",
            "failure_hash_ref": failure_hash,
            "emergency_spool_ref": None if pre_action else f"emergency-spool-ref-{failure_id}",
            "spool_hash_ref": None if pre_action else f"hash-ref-spool-{failure_id}",
            "retry_state": "queued" if pre_action else "exhausted",
            "reconciliation_status": "pending" if pre_action else "failed",
            "incident_id": f"inc-{failure_id}" if failure_code in {"integrity_check_failed", "queue_exhausted"} else None,
            "quarantine_required": failure_code in {"integrity_check_failed", "queue_exhausted"},
            "approval_tokens_revoked": failure_code in {"integrity_check_failed", "queue_exhausted"},
            "guardian_decision_id": guardian_decision_id,
            "policy_version": "policy-phase1a-mock-v1",
            "detected_at": FIXED_CREATED_AT,
        }
        failure = self.validator.validate(failure, "evidence.failure")
        self._failures[failure_id] = copy.deepcopy(failure)
        return copy.deepcopy(failure)

    def health_summary(self) -> dict[str, Any]:
        return {
            "evidence_writer_status": "failed" if self.fail_writes else "healthy",
            "evidence_artifact_count": len(self._artifacts),
            "evidence_failure_count": len(self._failures),
            "evidence_spool_depth": 0,
        }

    def _previous_artifact_id(self) -> str | None:
        if not self._artifacts:
            return None
        return next(reversed(self._artifacts))

    @staticmethod
    def _validate_summary(summary: str) -> None:
        if len(summary) > 240:
            raise EvidenceWriteError("mock evidence summary is too long for metadata-only evidence")
        secret_patterns = (
            re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
            re.compile(r"\bsk-[A-Za-z0-9][A-Za-z0-9_-]{20,}\b"),
            re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"),
            re.compile(r"(?i)\b(password|secret_value|private_key|api_key)\b"),
        )
        if any(pattern.search(summary) for pattern in secret_patterns):
            raise EvidenceWriteError("mock evidence summary appears to contain secret material")

    @staticmethod
    def _hash(payload: dict[str, Any]) -> str:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return "hash-ref-" + hashlib.sha256(encoded).hexdigest()[:16]
