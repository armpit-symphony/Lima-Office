# Open Questions

This file tracks remaining blockers after the Phase 0 / Phase 1A closeout. The
questions below must stay visible until they are resolved in docs, contracts,
policies, runbooks, and tests. None of these items approve live connectors,
external sends, real remediation, production operations, or customer-system
mutation.

## Security / Governance

- Operator IdP/MFA: what identity provider assumptions and MFA level should be
  required for operators, approvers, supervisor admins, security reviewers, and
  field IT reviewers?
- Breakglass: what breakglass process is acceptable, who can invoke it, what
  evidence is required, and which action classes remain blocked during
  breakglass?
- Access review cadence: how often should operator, approver, helper-agent,
  worker, and LIMA IT roles be reviewed?
- LIMA IT approver separation: who can approve LIMA IT diagnostic handoff and
  remediation requests, and what separation of duties is required?
- RBAC matrix: what exact role/action matrix applies after the operator IdP is
  selected?

## Data / Compliance

- Retention defaults: what default retention periods apply to evidence, memory,
  logs, task records, incidents, worker cache refs, and LIMA IT handoff records?
- Redaction taxonomy: what redaction profiles apply by record type, data
  classification, and free-text field?
- Audit export: what export manifest format, integrity metadata, redaction
  posture, and access-control refs are required?
- Customer exit/delete: what customer exit, delete, reset, and proof process is
  required?
- Durable evidence/export posture: what storage, emergency spool, retry/backoff,
  disk-full threshold, reconciliation, and export posture must exist before
  runtime expansion?
- First compliance target: what governance or compliance mapping matters first,
  without claiming certification?

## Runtime

- Approval-token runtime record binding: how should runtime bind approval tokens
  to exact task IDs, action classes, resource refs, policy snapshots, tenant,
  customer context, fresh operator intent, expiry, and one-time use?
- Non-test Guardian expiry policy: what decision expiry, replay rejection,
  clock-skew tolerance, and reclassification behavior apply outside tests?
- Health reason taxonomy: which reason code set should become normative for
  Supervisor health, Guardian decisions, worker state, queue depth, evidence
  status, connector readiness, LIMA IT handoff, and degraded/offline/quarantine
  transitions beyond the planning defaults in [Worker Deployment Blueprint](deployment/WORKER_DEPLOYMENT_BLUEPRINT.md)?
- Heartbeat thresholds: what heartbeat interval, missed-heartbeat thresholds,
  stale-age limits, and escalation timing should apply in lab mode?
- Worker attestation: what attestation method is required for Arc worker mini
  PCs before re-enrollment can be automated?
- Update rollback: what signed/verified source format, known-good selection,
  rollback trigger matrix, and approval workflow should be required beyond the
  planning channels in [Update Rollback Blueprint](deployment/UPDATE_ROLLBACK_BLUEPRINT.md)?
- Worker hardware baseline: what exceptions, local-model sizing thresholds, and
  exact lab acceptance criteria should be applied to the vendor-neutral classes
  in [Worker Hardware Baseline](deployment/WORKER_HARDWARE_BASELINE.md)?
- Small-business supportability: what offline/ISP outage, power-loss recovery,
  log retention, disk-full behavior, device replacement, support RACI, and
  operator escalation assumptions remain required beyond the field checklist?
- Cross-contract invariant source: the 2026-05-22 reconciliation check found no
  local object and no `origin` branch for
  `phase-1a-cross-contract-invariants` / `e71431007ddbe96c3e141b77591efc2508c53e5d`
  after `git fetch --all --prune`; should the checkpoint be pushed, restored,
  recreated, or formally superseded?

## Connectors And Deployment

- Connector consent/scope/revocation: what consent process, scope review,
  revocation evidence, and read-only limits are required before any live
  connector review?
- Model routing defaults: what tasks can use local models, what tasks can use
  subscription/cloud model classes, and what data classifications block cloud
  routing?
- First deployment posture: is the first lab deployment on-prem, hybrid, or
  managed private cloud, and what acceptance threshold moves it from lab-only to
  pilot-review?
- First workflow posture: what target vertical or workflow should be considered
  first while staying draft-only or mock-only?
- Connector prompt-injection evaluation: what test and review evidence is
  required before connector-handled content can influence model/tool decisions?

Resolved in [Deployment Docs](deployment/README.md) and `worker.deployment`:

- Vendor-neutral worker hardware classes are documented for lightweight,
  standard, local-model, and supervisor/helper-capable machines.
- Lab/default network posture is documented as no public inbound worker exposure,
  no direct cross-worker trust, local-supervisor-first communication, and no
  direct production-system remediation.
- Worker deployment records can represent hardware, OS, network, Supervisor
  endpoint, policy/model refs, encryption, attestation placeholder,
  update/rollback posture, and evidence refs.
- Worker deployment, update/rollback, and field IT preflight runbooks exist as
  manual operator docs only.

Resolved in [Schema Hardening Notes](SCHEMA_HARDENING_NOTES.md) and [contracts/v1](../contracts/v1):

- `approval.result` is a separate v1 schema.
- `helper.scope` is a separate v1 schema.
- v1 schemas include conditionals for approval token lifecycle states, blocked-MVP denial, LIMA IT remediation constraints, evidence-required completion, evidence failure, token verification, and taint refs.

Resolved in [Phase 0 Validation](VALIDATION.md) and [Phase 0 validation workflow](../.github/workflows/phase0-validation.yml):

- CI uses [requirements-dev.txt](../requirements-dev.txt) for JSON Schema draft 2020-12 validation with format checks.

Resolved in [Phase 1A Runtime Scaffolding](PHASE_1A_RUNTIME_SCAFFOLDING.md):

- Runtime contract validation requires `jsonschema` and fails closed if it is unavailable.
- Phase 1A runtime state is in-memory mock scaffolding only, with no live connectors, external sends, remediation execution, external model API calls, browser automation, services, databases, or production-system access.

## Policy Follow-Ups

- What concrete default retention periods should replace placeholders in [Retention And Redaction Matrix](policies/retention-redaction-matrix.md)?
- What redaction profile taxonomy should apply by record type and data classification?
- What redaction strategy should apply to free-text reason fields such as `denial_reason`, `failure_reason`, `summary`, and `result_summary`?
- What audit export manifest format is required?
- What customer exit/delete/reset process and proof fields are required?
- What local emergency evidence spool depth, retry/backoff, disk-full threshold, and reconciliation process should be approved?
- What update rollback runbook and policy are required before runtime?
- What connector consent, scope review, and revocation policy is required before any live connector review?
- What access role/RBAC matrix should be enforced once the operator identity provider is selected?
- What operator identity provider and MFA level should be assumed for approval and token verification?
- What worker attestation method should be used before re-enrollment can be automated?
- What breakglass policy is acceptable, and which actions remain blocked during breakglass?
- Who can approve LIMA IT remediation requests, and what separation of duties is required?
