# Field IT Checklist

## Purpose

Provide a practical preflight checklist for field deployment planning. This is a
manual checklist only and does not authorize installation, remediation, or
production operations.

## Pre-Install

- Confirm deployment is lab mock or approved small-business local planning.
- Confirm customer/tenant context is one tenant only.
- Confirm no live connector credentials are present.
- Confirm no remediation or production server access is being requested.
- Confirm operator, field IT reviewer, and security reviewer contacts.

## Network Readiness

- Supervisor endpoint ref recorded.
- Worker hostname planned.
- Worker can reach Supervisor Server on the approved local path.
- No inbound public worker exposure.
- Guest Wi-Fi and production management networks are not used.
- DNS/hostname entry matches inventory.
- Clock sync source is identified.

## Hardware Readiness

- Worker ID assigned.
- Hardware class selected.
- CPU/RAM/storage recorded.
- Storage encryption availability recorded.
- TPM/secure boot availability recorded as future attestation input.
- Wired Ethernet available or Wi-Fi exception documented for lab mock.

## OS Readiness

- OS family and version ref recorded.
- Dedicated worker account planned.
- Local admin posture reviewed.
- Disk encryption enabled where available.
- Patch posture recorded.
- No secrets in config files.

## Security Readiness

- Device identity ref planned.
- Channel identity ref planned.
- Capability manifest hash ref planned.
- Policy bundle ref planned.
- Model bundle ref or cloud-only placeholder planned.
- Blocked tool packs documented.
- Guardian decision/evidence refs required for enrollment.

## Supervisor Readiness

- Worker registry can represent the worker.
- Supervisor health view requirements are known.
- Evidence writer posture is visible.
- Quarantine and revoke states are documented.
- LIMA IT handoff is diagnostic/read-only.

## Worker Enrollment Readiness

- Role selected: admin, file clerk, customer service draft, IT diagnostic helper,
  or general office.
- Heartbeat interval planned.
- Update channel and rollback state recorded.
- Local cache expectations recorded.
- Field notes avoid secrets and raw customer payloads.

## Validation Steps

- Validate deployment contract example shape.
- Confirm docs links pass.
- Confirm current unit tests pass.
- Confirm compile checks pass.
- Confirm git whitespace checks pass.

## Handoff Notes

Record:

- Worker ID and hostname.
- Supervisor endpoint ref.
- Hardware/OS profile.
- Policy/model refs.
- Encryption/attestation status.
- Quarantine/re-enrollment contacts.
- Evidence refs.

## Support Ownership

| Situation | Primary owner | Escalation |
| --- | --- | --- |
| Enrollment preflight issue | Field IT reviewer | Supervisor admin |
| Identity or attestation mismatch | Security reviewer | Operator |
| Heartbeat or network degradation | Field IT reviewer | Supervisor admin |
| Evidence writer failure | Supervisor admin | Security reviewer |
| Quarantine release request | Operator | Security reviewer or field IT reviewer |
| LIMA IT diagnostic handoff | LIMA IT handoff owner | Operator |

## Rollback/Escape Plan

- If identity, policy, network, or evidence checks fail, do not enroll the
  worker.
- If a worker becomes suspicious, quarantine it and stop new assignments.
- If update verification fails, roll back to known-good refs or keep the worker
  quarantined.
- If evidence cannot be written, block privileged action and follow the evidence
  writer failure runbook.
