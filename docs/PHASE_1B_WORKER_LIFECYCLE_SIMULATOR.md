# Phase 1B Worker Lifecycle Simulator

Date: May 26, 2026

## Purpose

Implement the explicitly approved narrow Phase 1B slice: a worker lifecycle
simulator only.

## Explicit Approval Scope

- In-memory Python simulation only.
- Deterministic lifecycle state transitions for worker deployment metadata.
- Contract validation using existing runtime schema validation.
- Fail-closed behavior for unsafe/invalid transitions.

## Implemented

- New module: `lima_office/supervisor/worker_lifecycle_simulator.py`.
- Uses `ContractValidator` with `worker.deployment` contract validation.
- Maintains current worker lifecycle state in memory by `worker_id`.
- Maintains transition history in memory only.
- Blocks unsafe transitions and unsafe active-state posture.
- Never authorizes real actions.

## Not Implemented

- No persistence or file-backed state.
- No network calls, sockets, APIs, or external services.
- No background worker, daemon, queue, scheduler, thread, or subprocess.
- No connector, OAuth/OIDC/SAML, token runtime, model provider, local inference,
  remediation, or UI behavior.

## Transition Matrix

Allowed transitions:

- `provisioned -> enrolled`
- `enrolled -> active`
- `enrolled -> retired`
- `active -> degraded | quarantined | revoked | retired`
- `degraded -> active | quarantined | revoked | retired`
- `quarantined -> reenrollment_pending | revoked | retired`
- `reenrollment_pending -> enrolled | revoked | retired`
- `revoked -> retired`

Blocked transitions:

- `revoked -> active`
- `retired -> active`
- `quarantined -> active` directly
- any transition not in the allowed matrix
- unknown worker
- tenant mismatch

## Fail-Closed Rules

- Schema-invalid lifecycle payloads fail validation.
- Unknown lifecycle states fail.
- Active transition fails when metadata indicates blocked posture:
  - `attestation_status` is `failed`, `expired`, `revoked`, or `blocked_mvp`
  - `trust_root_status` is `failed` or `blocked_mvp`
  - environment is `blocked_mvp`
  - `reason_codes` include device-untrusted or blocked-mvp posture markers
- If a worker was quarantined, active transition requires
  `quarantined -> reenrollment_pending -> enrolled` history path first.

## Test Coverage

`tests/test_worker_lifecycle_simulator.py` covers:

- valid lifecycle schema validation checks
- approved transition paths
- blocked transition paths
- unknown worker and tenant mismatch
- attestation/device trust active-state blocking
- in-memory-only history behavior
- no file-write behavior
- no network-call behavior
- no real-action authorization behavior

## Non-Goals

- No broader Phase 1B runtime expansion.
- No change to main branch gate posture.
- No production-readiness or compliance-certification claims.

## Remaining Blockers

- Live connectors, provider wiring, and token runtime remain blocked.
- Durable storage and transaction runtime remain blocked.
- Runtime authorization expansion beyond mock lab boundaries remains blocked.
- Real attestation/verifier/signing/update runtime remains blocked.
