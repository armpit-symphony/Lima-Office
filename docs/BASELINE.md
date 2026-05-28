# Canonical Baseline

Date: May 26, 2026

This baseline is a docs/contracts/tests/mock-hardening checkpoint. It is not production readiness, not runtime implementation approval, and not compliance certification.

## Baseline branch and commit

- Latest baseline checkpoint branch: `connector-source-of-truth-values-slo-target-finalization`
- Latest baseline checkpoint commit: `a92606a9cbb3bc3e4271fb8ccfdff0839c79de6e`
- Frozen planning baseline branch in repo: `integration/phase-0-1b-planning-baseline` / `b81dcb6e1e947c4f59ec19d9222e219b4a7600a8`
- Frozen simulator baseline branch in repo: `integration/phase-1b-simulator-baseline` (current branch tip)
- Frozen simulator baseline branch in repo for Phase 1C: `integration/phase-1c-simulator-baseline`
- Prior integration baseline branch: `integration/phase-0-1a-baseline` / `26d5789ff62318ede69abf3296139eea7eaac8f0`
- Main branch: `main` / `e4bb6105a9d668ddffe21892da3aaff16a0d8ca0`

## Canonical checkpoint summary

The repo contains a reachable hardening chain from Phase 0 through Phase 1A
metadata hardening (`a92606a`) plus:

- Phase 1B planning-only freeze (`b81dcb6`), and
- Phase 1B simulator freeze (`integration/phase-1b-simulator-baseline`) that
  includes worker lifecycle simulator + audit and task lifecycle simulator + audit.
- Phase 1C simulator freeze (`integration/phase-1c-simulator-baseline`) that
  includes evidence lifecycle simulator + audit/hardening and Guardian replay drill
  simulator + audit/hardening.

Both freezes remain mock/in-memory posture and do not approve broader runtime
expansion.

## Important branches since `integration/phase-0-1a-baseline`

| Branch | Commit | Purpose |
| --- | --- | --- |
| `phase-1a-invariant-checkpoint-v2` | `efcaaee` | Reachable invariant checkpoint replacement/hardening. |
| `approval-token-runtime-binding-design` | `1a8dd55` | Approval token binding metadata and tests. |
| `guardian-expiry-replay-policy-design` | `004dd67` | Guardian decision expiry/replay fail-closed posture. |
| `durable-replay-evidence-posture` | `7123163` | Replay/evidence durable posture contracts and mock checks. |
| `durable-transaction-storage-rfc` | `c0e1e28` | Storage/transaction architecture RFC posture. |
| `durable-transaction-coordinator-design` | `fe2f9a0` | Coordinator sequencing/idempotency posture. |
| `cross-contract-linkage-hardening` | `801481a` | Cross-contract linkage fail-closed hardening. |
| `approval-guardian-linkage-reconciliation-drills` | `59083ce` | Approval/Guardian reconciliation drill posture. |
| `governance-export-delete-taxonomy-finalization` | `5100a4f` | Export/delete taxonomy governance hardening. |
| `reason-code-registry-compatibility-policy` | `cf9b647` | Registry and compatibility governance hardening. |
| `reason-code-conformance-ci-gate` | `d693c75` | Reason-code conformance gating. |
| `taxonomy-version-enforcement-hardening` | `f3b3f66` | Mandatory taxonomy version enforcement. |
| `rbac-idp-mfa-session-device-trust-matrix` | `f73dbc5` | Identity/session/device trust governance posture. |
| `model-routing-defaults-health-taxonomy-refinement` | `71480d7` | Model-route defaults and health taxonomy hardening. |
| `worker-attestation-trust-root-signed-update-rollback-hardening` | `7753f25` | Worker trust/update rollback posture. |
| `attestation-verifier-policy-reference-values-design` | `87976c9` | Attestation verifier/reference policy posture. |
| `durable-attestation-lineage-authority-design` | `cf53178` | Attestation lineage/authority posture. |
| `attestation-revocation-reconciliation-drills` | `c94f260` | Attestation revocation reconciliation drill posture. |
| `live-connector-criteria-design` | `85ab3d5` | Live connector criteria and gate posture. |
| `connector-provider-risk-profile-revocation-disable-drills` | `bcaca8f` | Connector provider risk and disable drill posture. |
| `connector-trust-boundary-linkage-invariants` | `3968ad9` | Connector trust-boundary reconciliation invariants. |
| `connector-provider-acceptance-scoring-reconciliation-slo` | `14f298e` | Acceptance scoring and reconciliation-SLO posture. |
| `connector-source-of-truth-ownership-escalation-accountability` | `5d9590e` | Ownership/escalation accountability posture. |
| `connector-source-of-truth-values-slo-target-finalization` | `a92606a` | Connector defaults, SLO targets, threshold posture finalization. |

## Integration branch status

- `integration/phase-0-1b-planning-baseline` is the frozen planning baseline
  for Phase 0 through Phase 1B planning-only state (`b81dcb6`).
- `integration/phase-1b-simulator-baseline` is the frozen simulator baseline
  for approved Phase 1B worker/task lifecycle simulator slices and their audits.
- `integration/phase-1c-simulator-baseline` is the frozen simulator baseline
  for approved Phase 1C evidence lifecycle and Guardian replay drill simulator
  slices and their warning-hardening/audit chains.
- Canonical Phase 1C provenance anchor tag is
  `lima-office-phase-1c-simulator-baseline-annotated` and targets
  `8232970eb5e18e1c5db29e78f673b42f15b07ccc`.
- Original lightweight tag
  `lima-office-phase-1c-simulator-baseline` is retained for historical
  continuity and points to the same commit.
- Provenance fix branch: `phase-1c-annotated-tag-provenance-fix`.
- `integration/phase-0-1a-baseline` remains the prior refreshed integration
  baseline (`26d5789`).
- `main` remains untouched and must stay untouched unless explicitly approved.
- `taxonomy-family-constraint-hardening` (`674f41d`) and
  `model-routing-defaults-health-taxonomy-refinement` (`ba534b2`) are not
  direct ancestors of this integration tip and remain separately tracked side branches.

## Next gate

- Use annotated provenance tag:
  `lima-office-phase-1c-simulator-baseline-annotated` (supersedes lightweight
  `lima-office-phase-1c-simulator-baseline`) for current Phase 1C baseline
  traceability.
- Run independent gate audit on that tag before any additional implementation proposal.

## Must not be treated as production-ready

Do not treat this baseline as production-ready. It does not include:

- live connector execution,
- OAuth/OIDC/SAML/provider runtime wiring,
- token runtime storage/rotation,
- real model provider/local inference runtime,
- durable production storage services,
- production runtime authorization,
- remediation execution,
- UI/frontend runtime implementation.
