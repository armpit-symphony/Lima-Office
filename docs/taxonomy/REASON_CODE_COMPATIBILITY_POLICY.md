# Reason Code Compatibility Policy

Status: Phase 1A design-only compatibility policy. Not implemented runtime.

## Purpose

Define how reason codes are added, deprecated, aliased, and removed without
silent semantic drift across contracts, examples, and mock helpers.

## Compatibility Contract

- `taxonomy_version` identifies the compatible reason-code set.
- Unknown or unsupported `taxonomy_version` values fail closed.
- Every reason-code change must be represented by:
  - registry record (`reason.code.registry`)
  - compatibility record (`reason.code.compatibility`)
  - updated examples/tests/docs
- Authorization-sensitive paths default to fail-closed on ambiguity.

## When A Reason Code May Be Added

Allowed when all are true:

- category is explicit
- description and severity are defined
- evidence and fail-closed requirements are explicit
- at least one example and one test use/validate the new code
- taxonomy version is bumped

## When A Reason Code May Be Deprecated

Allowed when all are true:

- replacement code (or explicit no-replacement rationale) is defined
- compatibility record marks `compatibility_action: deprecate`
- migration notes and affected contracts are listed
- deprecated code remains readable for at least one major cycle

## When A Reason Code May Be Removed

Allowed only when all are true:

- previously deprecated
- major taxonomy version bump
- compatibility record marks `remove_planned`
- examples/tests/contracts migrated
- policy review approves removal

## When An Alias Is Allowed

- Legacy rename compatibility only.
- Alias must map to one canonical active code.
- Alias mapping cannot broaden authorization.
- Alias lookup is metadata normalization, not permission grant.

## Schema Example Requirements For `taxonomy_version`

- Decision-relevant schemas/examples must include `taxonomy_version`.
- All reason-bearing schemas/examples must include `taxonomy_version`.
- Versionless reason-code payloads are invalid.
- Examples should use canonical active codes unless testing deprecation/alias
  handling.
- Deprecated or alias examples must carry explicit compatibility evidence.
- Model-route and health route/status examples must carry taxonomy version and
  canonical route/health reason codes.
- Worker-attestation and signed-update/rollback examples must carry taxonomy
  version and canonical trust/update reason codes.
- Attestation verifier/reference-value examples must carry taxonomy version and
  canonical appraisal/reference/endorsement reason codes.
- Connector readiness/scope-review/consent examples must carry taxonomy version
  and canonical connector consent/scope/revocation/object-property authorization
  reason codes.
- Connector acceptance-score and reconciliation-SLO examples must carry
  taxonomy version and canonical score/cadence/revocation-propagation reason
  codes.
- Connector ownership/escalation examples must carry taxonomy version and
  canonical ownership/accountability/escalation reason codes.
- Connector defaults/SLO-target/score-threshold examples must carry taxonomy
  version and canonical defaults/threshold/cadence reason codes.

## Runtime Helper Rules For Unknown Codes

- Unknown codes are rejected by default.
- Unknown code outcome is fail-closed for authorization/reconciliation/export/
  delete classifications.
- Unknown or unsupported `taxonomy_version` is also fail-closed.
- Helper output may include unknown-code diagnostics but `can_authorize` must
  remain `false`.
- CI reason-code conformance gate must fail on unknown codes found in schemas
  or examples.

## Export/Audit Preservation Of Old Codes

- Export/audit records preserve raw historical code values.
- Where normalization exists, store both raw and canonicalized interpretation in
  metadata fields.
- Historical evidence must remain readable after deprecation.

## Operator UI Handling Of Deprecated/Unknown Codes

- Deprecated: show warning label and replacement guidance.
- Unknown: show blocked/review-required label.
- Neither deprecated nor unknown codes can silently appear as success/authorized
  outcomes.

## Fail-Closed Behavior

- Unknown, blocked, or breaking-change compatibility statuses fail closed.
- Deprecated codes cannot authorize privileged outcomes unless policy explicitly
  allows warning-only metadata use.
- Deprecated/alias handling remains metadata-only in Phase 1A unless a future
  approved policy lane changes this.
- Breaking changes require review/evidence before any decision path uses them.
- Blocked codes cannot appear in success/authorization-complete metadata states.

## Migration Checklist

1. Add/update registry entries.
2. Add compatibility records with action/status.
3. Update affected schema enums/conditionals/fields.
4. Update examples with `taxonomy_version` and evidence refs as required.
5. Update helper constants and normalization logic.
6. Add/refresh tests for unknown/deprecated/blocked/breaking paths.
7. Update docs and blockers.

## Acceptance Gates

- No unknown reason code can authorize privileged actions.
- Deprecated alias mapping is deterministic and test-covered.
- Breaking-change records include affected contracts and evidence refs.
- Contracts/examples/runtime helper remain mock-only with no live service
  expansion.
- CI executes `python scripts/check-reason-codes.py` and fails non-zero on
  conformance violations.
