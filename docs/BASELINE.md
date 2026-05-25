# Canonical Baseline

This document defines the reachable Phase 0 / Phase 1A integration baseline for
LIMA Office OS. It is a stabilization checkpoint only. It does not approve live
connectors, OAuth/provider wiring, external model calls, external sends, browser
automation, real remediation, durable services, UI implementation, production
operations, customer-system mutation, or compliance certification claims.

## Canonical Integration Branch

- Branch: `integration/phase-0-1a-baseline`
- Base used for integration: `operator-console-ux-spec` /
  `bac6f80cc63dd15ec7cd3d669193160c3766a8e1`
- Mainline status: `main` must remain untouched unless explicitly approved.
- Stabilization mode: merge verification and docs-only baseline clarification.

## Superseding Invariant Checkpoint

- Branch: `phase-1a-invariant-checkpoint-v2`
- Base: `integration/phase-0-1a-baseline`
- Purpose: replace the absent `phase-1a-cross-contract-invariants` /
  `e71431007ddbe96c3e141b77591efc2508c53e5d` checkpoint with reachable Phase 1A
  invariant hardening.
- Scope: mock/in-memory invariant checks, `supervisor.health` contract/reporting,
  tests, and docs. No live runtime expansion is authorized.

## Approval Binding Checkpoint

- Branch: `approval-token-runtime-binding-design`
- Base: `phase-1a-invariant-checkpoint-v2`
- Purpose: define and test first-class approval-token runtime binding so
  approval metadata cannot be replayed, widened, copied across tenants, used
  after expiry, or used for the wrong action.
- Scope: docs, schemas, examples, tests, and mock/in-memory binding verifier
  only. No live connector, external send, real remediation, durable service, UI,
  or production operation is authorized.

## Guardian Expiry Replay Checkpoint

- Branch: `guardian-expiry-replay-policy-design`
- Base: `approval-token-runtime-binding-design`
- Purpose: define and test Guardian decision expiry, replay prevention, clock
  skew handling, and context binding so stale or copied decisions fail closed.
- Scope: docs, schemas, examples, tests, and mock/in-memory Guardian replay
  verifier only. No live connector, external send, real remediation, durable
  service, UI, or production operation is authorized.

## Durable Replay Evidence Posture Checkpoint

- Branch: `durable-replay-evidence-posture`
- Base: `guardian-expiry-replay-policy-design`
- Purpose: define durable replay/evidence posture contracts and fail-closed
  mock metadata checks for replay records, evidence integrity fields, and export
  manifest posture.
- Scope: docs, schemas, examples, tests, and mock/in-memory metadata helpers
  only. No durable storage engine, queue, service, live connector, external
  send, remediation, UI, or production operation is authorized.

## Durable Transaction Storage RFC Checkpoint

- Branch: `durable-transaction-storage-rfc`
- Base: `durable-replay-evidence-posture`
- Purpose: define draft transaction-boundary and evidence-ledger architecture
  posture for future atomic replay/token consumption and recovery behavior.
- Scope: docs, schemas, examples, and tests only. No database, queue, migration,
  service, or production storage implementation is authorized.

## Durable Transaction Coordinator Design Checkpoint

- Branch: `durable-transaction-coordinator-design`
- Base: `durable-transaction-storage-rfc`
- Purpose: define coordinator event sequencing, transition/immutability rules,
  tenant-scoped idempotency behavior, and recovery/reconciliation runbook
  posture for future atomic replay/token/evidence operations.
- Scope: docs, schemas, examples, tests, and mock/in-memory transition
  validation only. No database, queue, migration, service, or production
  storage implementation is authorized.

## Cross-Contract Linkage Hardening Checkpoint

- Branch: `cross-contract-linkage-hardening`
- Base: `durable-transaction-coordinator-design`
- Purpose: enforce fail-closed cross-contract linkage rules so coordinator
  events, transaction boundaries, replay records, evidence ledger entries,
  evidence artifacts, and export manifests cannot drift while remaining
  individually schema-valid.
- Scope: docs, schemas, examples, tests, and mock/in-memory linkage validation
  only. No database, queue, migration, service, or production storage
  implementation is authorized.

## Approval Guardian Reconciliation Drills Checkpoint

- Branch: `approval-guardian-linkage-reconciliation-drills`
- Base: `cross-contract-linkage-hardening`
- Purpose: harden approval/Guardian reconciliation conditionals and drill
  scenarios so approval bindings, approval chains, token verification, Guardian
  decisions/replay, replay records, coordinator events, transaction boundaries,
  and evidence ledger records fail closed on linkage drift.
- Scope: docs, schemas, tests, and mock/in-memory reconciliation classification
  only. No database, queue, migration, service, or production storage
  implementation is authorized.

## Governance Export/Delete Taxonomy Finalization Checkpoint

- Branch: `governance-export-delete-taxonomy-finalization`
- Base: `approval-guardian-linkage-reconciliation-drills`
- Purpose: finalize governance export/delete conflict posture and normalize
  reconciliation/evidence reason vocabulary across schemas, examples, and
  mock-only validation helpers.
- Scope: docs, schemas, examples, tests, and mock/in-memory taxonomy
  validation only. No export/delete implementation, database, queue, migration,
  service, or durable production storage is authorized.

## Reason-Code Registry Compatibility Policy Checkpoint

- Branch: `reason-code-registry-compatibility-policy`
- Base: `governance-export-delete-taxonomy-finalization`
- Purpose: define canonical reason-code registry and compatibility lifecycle
  rules so contracts/helpers do not drift on reason semantics.
- Scope: docs, schemas, examples, tests, and mock/in-memory reason-code
  validation only. No runtime authorization, export/delete execution, database,
  queue, migration, service, or durable production storage is authorized.

## RBAC IdP MFA Session Device Trust Matrix Checkpoint

- Branch: `rbac-idp-mfa-session-device-trust-matrix`
- Base: `taxonomy-version-enforcement-hardening`
- Purpose: define standards-aligned governance posture for operator/approver/
  worker/service identity, MFA/session/device trust expectations, and RBAC
  permission metadata with fail-closed blocked-MVP controls.
- Scope: docs, schemas, examples, tests, and mock/in-memory access-matrix
  classification only. No IdP integration, OAuth/OIDC/SAML wiring, MFA runtime,
  session runtime, device posture runtime, live connector behavior, remediation
  execution, or production authorization service is authorized.

## Included Branches And Commits

The following reachable branches are ancestors of the integration branch:

| Branch | Commit | Baseline contribution |
| --- | --- | --- |
| `phase-0-architecture-contracts-roadmap` | `ba665f8` | Phase 0 architecture, scope, roadmap, and initial governance docs. |
| `phase-0-contract-schemas` | `761c393` | Initial v1 contract schemas and sanitized examples. |
| `phase-0-policy-runbook-hardening` | `64de3f0` | Policy docs, runbooks, and safety-boundary hardening. |
| `phase-0-schema-conditionals-followups` | `fd5421d` | Schema conditionals and follow-up contracts. |
| `phase-0-ci-schema-validation` | `0be4ced` | Contract validation scripts, doc-link checks, and CI expectations. |
| `phase-1a-runtime-scaffolding` | `d259409` | Mock in-memory Phase 1A runtime scaffolding and tests. |
| `phase-0-1a-closeout-archive` | `62df67f7cd68bba57f1e332c19fb3e0ce86e69da` | Closeout archive, status, validation evidence, and runtime boundaries. |
| `worker-deployment-blueprint` | `c15b7aea1a331040924b9b3534a03c6b1def4f38` | Worker deployment blueprint docs, runbooks, and worker deployment contract. |
| `governance-policy-details` | `944088eac5d41d2547ae0343500d3ab591a1256e` | Governance policy docs, runbooks, and governance metadata contracts. |
| `operator-console-ux-spec` | `bac6f80cc63dd15ec7cd3d669193160c3766a8e1` | Operator console UX specification docs and console metadata contracts. |
| `durable-replay-evidence-posture` | `7123163482860a93992b4597d49b5231cd5cb34b` | Durable replay/evidence posture docs, schemas, examples, and mock tests. |

## Excluded Or Missing Branches

- `phase-1a-cross-contract-invariants` /
  `e71431007ddbe96c3e141b77591efc2508c53e5d` is absent locally and absent from
  `origin` after `git fetch --all --prune`. It is not integrated. The reachable
  `phase-1a-invariant-checkpoint-v2` branch supersedes it for future baseline
  review.
- `roadmap-lima-office-control-plane` and `phase-0-codex-agents-skills` are
  historical ancestors in the repo graph, not explicit stabilization targets for
  this baseline.

## Validation Baseline

The canonical validation set is:

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

Captured results for this baseline belong in
[Validation Evidence](VALIDATION_EVIDENCE.md). Passing validation is repository
health evidence only; it is not production certification.

## What Exists

- Phase 0 architecture, security, threat model, autonomy, roadmap, contracts,
  decisions, open questions, and runbook docs.
- Versioned contract schemas and sanitized examples under [contracts](../contracts).
- Contract validation, doc-link validation, unit tests, pytest coverage, and CI
  expectations.
- Phase 1A mock in-memory runtime scaffolding with worker registry, heartbeat,
  task queue, Guardian policy stub, contract loader/validator, and
  metadata-only evidence writer.
- Phase 1A v2 cross-contract invariant checks and metadata-only Supervisor
  health reporter.
- Phase 1A approval-token binding contracts, approval-chain examples, and
  mock/in-memory one-time binding verifier.
- Phase 1A Guardian expiry/replay policy, `guardian.replay` examples, and
  mock/in-memory one-time Guardian decision replay verifier.
- Closeout archive, runtime boundaries, worker deployment blueprint, governance
  policy details, and operator console UX specification.
- Worker deployment, governance, and console metadata contracts and examples.

## What Does Not Exist

- No live connectors, OAuth/provider wiring, webhooks, connector secrets, or
  customer-system reads/writes.
- No external email, text, chat, form submission, or other external send path.
- No external model provider API calls.
- No browser automation.
- No real IT remediation, production server touch, endpoint control, network
  control, or software install/update behavior.
- No durable database, queue, web server, scheduler, background service, or UI.
- No production operations posture or compliance certification.
- No marketing, pricing, sales, TAM, or financial projection content.

## Blocked Work

The following work remains blocked until a future approved lane explicitly
closes the relevant gates:

- Runtime expansion beyond the mock Phase 1A scaffold.
- Live connectors or connector OAuth/provider wiring.
- External model calls, external sends, or browser automation.
- Real remediation or production-system mutation.
- Automatic update, rollback, attestation, or re-enrollment behavior.
- Breakglass runtime behavior.
- Durable evidence/export/delete implementation without approved posture.
- Mainline update without explicit approval.

## Next Recommended Lanes

Recommended order after stabilization:

1. Coordinator/reconciliation invariant hardening and cross-contract
   transition-gating details for replay/token/evidence/export metadata.
2. Final RBAC/IdP/MFA/session/device trust matrix.
3. Model-routing defaults and health taxonomy refinement.
4. Phase 1B lab runtime expansion only after the gates above are approved.

Alternative non-runtime lanes:

- Model-routing defaults.
- Final IdP/MFA/RBAC matrix.
- Health taxonomy refinement.
- Worker attestation and signed update trust-root details.
