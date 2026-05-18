# Security Incident Runbook

## Purpose

Triage a suspected LIMA Office OS security incident in Phase 0 or lab mode.

## When To Use

Use for suspected compromised worker, stolen secret, prompt injection, forged approval, evidence tampering, connector overreach, unauthorized outbound request, or customer network compromise.

## Prerequisites

- Operator can access supervisor status.
- Evidence ledger is available.
- Quarantine controls are available.
- Security reviewer is identified.

## Steps

1. Open an incident record.
2. Identify tenant, worker/helper, task, connector, and operator context.
3. Preserve relevant evidence artifacts and logs.
4. Quarantine affected worker or helper scope if needed.
5. Disable affected mock connector readiness state if connector risk is involved.
6. Revoke active approval tokens related to the incident.
7. Classify severity and suspected threat scenario.
8. Decide whether LIMA IT diagnostic handoff is needed.
9. Record containment action and operator owner.
10. Create post-review questions and contract gaps.

## Approval Requirements

Containment can happen immediately. Remediation, software changes, endpoint changes, production server touch, or network changes require approval.

## Evidence To Capture

- Incident ID.
- Tenant ID.
- Threat scenario.
- Affected worker/helper/connector.
- Triggering event.
- Guardian decisions.
- Approval tokens revoked.
- Containment steps.
- Operator owner.

## Rollback/Containment

Keep affected components quarantined or disabled until review. If a secret is suspected exposed, treat it as compromised and follow future rotation policy when defined.

## Escalation

Escalate to security reviewer immediately. Escalate to compliance reviewer if sensitive data may be exposed. Escalate to LIMA IT for diagnostics only unless remediation is approved.

## Done Criteria

- Incident is recorded.
- Containment is visible.
- Evidence is preserved.
- Follow-up contract or runbook gaps are listed.
