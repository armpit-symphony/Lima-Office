# Phase 1A Runtime Scaffolding

Phase 1A adds the smallest safe Python runtime skeleton for LIMA Office OS. It
is mock runtime scaffolding only.

It does not add live connectors, OAuth or provider wiring, external model API
calls, external email/text/chat sends, browser automation, real IT remediation,
production-system access, web servers, databases, background workers, queue
services, or production-readiness claims.

## Runtime Package

[lima_office](../lima_office) contains:

- `contracts.loader`: loads schemas from [contracts/v1](../contracts/v1) and
  fails closed on missing, unreadable, invalid, or ambiguous schemas.
- `contracts.validator`: validates contract-shaped payloads with Python
  `jsonschema` draft 2020-12 and format checks. Runtime validation fails closed
  if `jsonschema` or required format support is unavailable.
- `guardian.policy`: a default-deny Guardian policy stub. It allows only
  explicitly low-risk mock/read-only/internal actions with explicit tenant,
  customer context, execution mode, external-effect posture, and evidence refs.
- `supervisor.worker_registry`: an in-memory mock registry for one tenant and up
  to eight Arc workers.
- `supervisor.heartbeat`: validates mock `worker.heartbeat` payloads and blocks
  unknown, wrong-tenant, stale, Guardian-unreachable, or evidence-failed
  workers.
- `supervisor.task_queue`: validates mock `task.execution` payloads and stores
  task records in memory only. It requires a validated Guardian decision before
  assignment and blocks quarantined/revoked/offline workers.
- `evidence.writer`: writes metadata-only, in-memory, test-only
  `evidence.artifact` records and `evidence.failure` records when simulated
  writes fail.
- `runtime.errors`: explicit fail-closed exception classes.

## Deny Defaults

The Guardian policy stub denies by default. It denies external sends,
remediation, file delete, live connector access, unrestricted tool/browser/file/
network access, cross-tenant access, tainted privileged actions, approval-
required actions without valid token verification metadata, bad token states,
and evidence-required actions without evidence refs.

Policy stubs are not final authorization logic. They are a Phase 1A control
surface for tests and future runtime design.

## Evidence Limits

The mock evidence writer is in-memory and test-only. Its deterministic refs and
hashes are not durable audit proofs, ledger integrity, customer export records,
or compliance evidence. Summaries are constrained to metadata-only text and
reject obvious secret-like content.

If evidence is required and the mock evidence writer cannot write, the path
fails closed with an `evidence.failure` record.

## Dependency Requirement

Runtime validation requires real JSON Schema validation:

```powershell
python -m pip install -r requirements-dev.txt
```

`requirements-dev.txt` includes `jsonschema` and `rfc3339-validator` so
`format: date-time` checks run locally and in CI.

## Local Checks

Run:

```powershell
python scripts/validate-contracts.py --require-jsonschema --check-formats --warnings-as-errors
python scripts/check-doc-links.py
python -m unittest discover -s tests -v
python -m compileall lima_office scripts tests
git diff --check
```

## What Phase 1A Does Not Prove

Phase 1A does not prove production safety, live connector readiness, identity or
MFA assurance, worker attestation, durable evidence storage, audit export,
customer exit/delete, connector consent/revocation, model-routing safety, or
LIMA IT separation of duties. Those remain open before any live runtime.
