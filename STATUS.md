# LIMA Office OS Status

Project name: LIMA Office OS

Canonical integration branch: `integration/phase-0-1a-baseline`

Integration source branch: `operator-console-ux-spec` at
`bac6f80cc63dd15ec7cd3d669193160c3766a8e1`

Current reachable baseline: Phase 0 architecture/contracts/policies, Phase 1A
mock runtime scaffolding, closeout archive, worker deployment blueprint,
governance policy details, and operator console UX specification.

Current phase: Phase 0 / Phase 1A baseline stabilization. Phase 1A mock runtime
scaffolding is present, but expansion remains blocked until the remaining gates
in this file, [Baseline](docs/BASELINE.md), and
[Next Phase Plan](docs/NEXT_PHASE_PLAN.md) are resolved.

Missing checkpoint: the previously reported `phase-1a-cross-contract-invariants`
commit `e71431007ddbe96c3e141b77591efc2508c53e5d` remains absent from this
checkout and from `origin` after fetch. Do not treat it as integrated or
validated unless it is pushed, restored, recreated, or formally superseded.

## What Exists

- Phase 0 architecture, MVP scope, autonomy, security, threat model, supervisor,
  worker, decision, roadmap, validation, policy, and runbook docs.
- Worker deployment blueprint docs for mini PC hardware, network, install
  layout, lifecycle, update/rollback, and field IT preflight.
- Governance policy details for identity/MFA placeholders, approver separation,
  breakglass blocked status, retention/redaction, audit export/customer exit,
  connector consent, worker attestation, and signed update/rollback posture.
- Operator console UX specification docs for Supervisor health, worker fleet,
  approvals, Guardian decisions, evidence, incidents, LIMA IT handoffs,
  deployment/update/attestation, governance, connector readiness, and
  audit/export/delete views.
- Canonical integration inventory in [Baseline](docs/BASELINE.md).
- Versioned v1 contract schemas and sanitized examples in [contracts](contracts).
- `worker.deployment` contract schema and examples for deployment planning
  metadata.
- Governance metadata contract schemas and examples for identity, access
  review, breakglass, audit export, connector consent, and update records.
- Console metadata contract schemas and examples for view, alert, and
  action-review records.
- Strict contract validation through [scripts/validate-contracts.py](scripts/validate-contracts.py).
- Local Markdown link validation through [scripts/check-doc-links.py](scripts/check-doc-links.py).
- Phase 1A mock Python runtime scaffolding in [lima_office](lima_office).
- In-memory worker registry, heartbeat validation, task queue, Guardian policy
  stub, contract loader/validator, and metadata-only evidence writer.
- Unit tests for contract loading, validation, fail-closed policy, worker state,
  heartbeat, task queue, and evidence behavior.

## What Does Not Exist

- No live connectors, OAuth/provider wiring, webhooks, connector tokens, or
  live customer-system reads/writes.
- No external email, text, chat, form submission, or other external send path.
- No real IT remediation, production server touch, software install/update, or
  endpoint/network control.
- No external model provider API calls.
- No browser automation.
- No durable database, queue, web server, background service, scheduler, or UI.
- No frontend code or operator console implementation.
- No production operations or production-readiness claim.
- No marketing, pricing, sales, TAM, or financial projection content.

## Validation Commands

Run the baseline validation set before merge:

```powershell
python scripts/validate-contracts.py --require-jsonschema --check-formats --warnings-as-errors
python scripts/check-doc-links.py
python -B -m unittest discover -s tests -v
python -m pytest -q
python -B -m compileall lima_office scripts tests
git diff --check
git diff --cached --check
git status
```

See [Validation Evidence](docs/VALIDATION_EVIDENCE.md) for the captured result.

## Remaining Blockers

- Rebuild or replace the missing cross-contract invariant branch if that
  checkpoint is still needed, or formally supersede it with a documented
  contract-invariant lane.
- Bind approval-token runtime records to concrete task/action/resource inputs
  before any approval-required runtime path can expand.
- Define non-test Guardian decision expiry and replay policy.
- Promote the initial health reason taxonomy in
  [Health Reason Taxonomy](docs/ux/HEALTH_REASON_TAXONOMY.md) to normative
  runtime thresholds and owner/escalation rules.
- Define durable evidence storage, audit export, retention, redaction, and
  customer exit/delete posture.
- Select operator IdP/MFA, breakglass, access review cadence, and LIMA IT
  approver separation implementation. Governance scaffolding now defines
  fail-closed metadata, role separation, and blocked breakglass posture, but no
  provider, runtime enforcement, or final cadence is selected.
- Define final worker attestation method, trust root, signed update format,
  and rollback trigger defaults. Governance scaffolding now blocks automatic
  update behavior and automated re-enrollment.
- Define final connector consent expiry, live-review criteria, provider scope
  mapping, and prompt-injection test evidence before any live connector review.

## Next Recommended Lane

After this integration branch is reviewed, the next safe lane is to rebuild or
replace the missing Phase 1A cross-contract invariant checkpoint if needed, then
work the Phase 1B prerequisite design lanes: approval-token runtime binding,
Guardian expiry/replay policy, durable evidence/export posture, and only then
Phase 1B lab runtime expansion. Mainline update should wait for explicit
approval.
