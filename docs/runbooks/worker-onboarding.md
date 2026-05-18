# Worker Onboarding Runbook

## Purpose

Onboard an Arc worker mini PC into a lab LIMA Office OS environment.

## When To Use

Use when adding a new worker to the Supervisor Server registry in lab mode.

## Prerequisites

- Supervisor Server is reachable.
- Worker mini PC is physically identified.
- Operator has approval authority for lab enrollment.
- Capability manifest has been reviewed.
- No live connector credentials are present.

## Steps

1. Record worker device details and intended role.
2. Verify the worker is in lab mode.
3. Register the worker identity reference with the supervisor.
4. Attach tenant ID and role.
5. Review capability manifest and tool-pack scope.
6. Confirm heartbeat interval and evidence writer status.
7. Request Guardian registration decision.
8. Record operator approval if required.
9. Mark worker `registered` and then `healthy` only after heartbeat succeeds.
10. Capture evidence artifact IDs.

## Approval Requirements

Operator approval is required to enroll a worker. Privileged tool packs require separate approval and may remain blocked.

## Evidence To Capture

- Worker ID.
- Device identity reference.
- Tenant ID.
- Role.
- Capability manifest version.
- Guardian decision ID.
- Approver identity.
- First heartbeat timestamp.

## Rollback/Containment

If identity, capability, or heartbeat checks fail, mark the worker `quarantined` or `revoked` and stop assignment.

## Escalation

Escalate to security reviewer for identity mismatch. Escalate to LIMA IT only for diagnostic handoff, not remediation, unless approved.

## Done Criteria

- Worker appears in registry.
- Heartbeat is current.
- Capability manifest is recorded.
- Evidence artifact exists.
- No live connectors or unrestricted tools are enabled.
