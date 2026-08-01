# Worker Deployment Runbook

## Purpose

Deploy an Arc worker mini PC into a LIMA Office OS lab or planned local
small-business environment.

## When To Use

Use when preparing a worker for enrollment under one Supervisor Server and one
tenant/customer context.

## Prerequisites

- Deployment remains lab mock or approved small-business local planning.
- Supervisor endpoint ref is known.
- Worker hardware and OS profile are inventoried.
- Operator has authority to approve enrollment.
- No live connectors, OAuth/provider wiring, external sends, remediation, or
  production server access are being configured.

## Procedure

1. Record `deployment_id`, `worker_id`, hostname, role, tenant, and customer
   context.
2. Confirm hardware class and OS profile.
3. Confirm storage encryption availability.
4. Record TPM/secure boot availability as attestation input only.
5. Confirm worker can reach the Supervisor Server on the approved local network.
6. Confirm no public inbound worker exposure.
7. Record policy bundle ref, capability manifest hash ref, and model bundle ref
   or cloud-only placeholder.
8. Confirm blocked tool packs include unrestricted browser, unrestricted file
   access, unrestricted network, live connector writes, production remediation,
   and payment or regulated systems.
9. Request Guardian enrollment decision.
10. Capture operator approval and evidence refs.
11. Mark the worker enrolled only after first heartbeat and evidence posture are
    acceptable.
12. Keep worker in degraded or quarantined state if any identity, policy,
    network, encryption, or evidence check fails.

## Approval Requirements

Operator approval is required for enrollment. Security or field IT reviewer
approval is required for release after identity mismatch, attestation failure,
evidence writer failure, or update verification failure.

## Evidence To Capture

- Hardware inventory.
- OS profile.
- Supervisor endpoint ref.
- Device identity ref.
- Channel identity ref.
- Policy and model bundle refs.
- Capability manifest hash ref.
- Guardian decision ID.
- Operator approval ref.
- First heartbeat ref.

## Rollback/Containment

- Failed preflight: do not enroll.
- Failed identity or policy check: quarantine.
- Failed evidence writer check: block privileged work and follow
  [Evidence writer failure](evidence-writer-failure.md).
- Suspicious tool, connector, network, or file request: quarantine and follow
  [Security incident](security-incident.md).

## Escalation Path

- Identity mismatch: security reviewer.
- Network reachability problem: field IT reviewer.
- LIMA IT diagnostics: [LIMA IT handoff](lima-it-handoff.md), read-only only.
- Remediation request: approval-required and blocked from execution in MVP.

## Done Criteria

- Worker deployment record exists.
- Worker appears in supervisor registry.
- Heartbeat is current.
- Evidence refs exist.
- Tool-pack scope is least-privilege.
- No live connectors, external sends, browser automation, real remediation, or
  production-system access are enabled.
