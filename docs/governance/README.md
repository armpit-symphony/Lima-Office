# Governance Docs

Governance docs are policy scaffolding only. They do not implement identity,
MFA, breakglass, connector consent, attestation, update signing, audit export,
delete workflows, live connectors, external sends, remediation, or production
operations.

Runtime must fail closed when governance policy is missing, ambiguous,
expired, contradictory, or not linked to a Guardian decision, approval state
where required, evidence, and auditability.

Privileged actions require:

- Policy coverage.
- Guardian decision.
- Human approval when required.
- Evidence refs.
- Auditability.

This governance set does not claim SOC 2, HIPAA, ISO, GDPR, PCI, legal, or
production compliance.

## Governance Policies

- [Identity And MFA Policy](IDENTITY_AND_MFA_POLICY.md)
- [RBAC IdP MFA Session Device Trust Matrix](RBAC_IDP_MFA_SESSION_DEVICE_TRUST_MATRIX.md)
- [Approver Separation Policy](APPROVER_SEPARATION_POLICY.md)
- [Breakglass Policy](BREAKGLASS_POLICY.md)
- [Retention Redaction Policy](RETENTION_REDACTION_POLICY.md)
- [Audit Export And Customer Exit Policy](AUDIT_EXPORT_AND_CUSTOMER_EXIT_POLICY.md)
- [Export Delete Conflict Policy](EXPORT_DELETE_CONFLICT_POLICY.md)
- [Connector Consent Scope Revocation Policy](CONNECTOR_CONSENT_SCOPE_REVOCATION_POLICY.md)
- [Worker Attestation Policy](WORKER_ATTESTATION_POLICY.md)
- [Signed Update Rollback Policy](SIGNED_UPDATE_ROLLBACK_POLICY.md)

## Supporting Runbooks

- [Access Review](../runbooks/access-review.md)
- [Breakglass Review](../runbooks/breakglass-review.md)
- [Customer Exit Delete](../runbooks/customer-exit-delete.md)
- [Connector Revocation](../runbooks/connector-revocation.md)
- [Worker Attestation Failure](../runbooks/worker-attestation-failure.md)
- [Update Rollback Approval](../runbooks/update-rollback-approval.md)
- [RBAC IdP MFA Access Review](../runbooks/rbac-idp-mfa-access-review.md)

## Supporting Contracts

- [governance.identity](../../contracts/v1/governance.identity.schema.json)
- [governance.access_review](../../contracts/v1/governance.access_review.schema.json)
- [governance.breakglass](../../contracts/v1/governance.breakglass.schema.json)
- [governance.rbac_matrix](../../contracts/v1/governance.rbac_matrix.schema.json)
- [governance.session_policy](../../contracts/v1/governance.session_policy.schema.json)
- [governance.device_trust](../../contracts/v1/governance.device_trust.schema.json)
- [governance.audit_export](../../contracts/v1/governance.audit_export.schema.json)
- [governance.export_delete_review](../../contracts/v1/governance.export_delete_review.schema.json)
- [governance.connector_consent](../../contracts/v1/governance.connector_consent.schema.json)
- [governance.update_record](../../contracts/v1/governance.update_record.schema.json)

## Console Visibility

Governance state is operator-visible through the
[Operator Console Spec](../ux/OPERATOR_CONSOLE_SPEC.md), especially identity/MFA
blockers, access review, approver separation, breakglass denial, connector
revocation, audit/export/delete review, attestation failure, and update/rollback
states.
