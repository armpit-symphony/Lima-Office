# Field IT Preflight Runbook

## Purpose

Perform a practical field preflight before enrolling an Arc worker mini PC.

## When To Use

Use before worker deployment, re-enrollment, replacement, or planned update
review.

## Prerequisites

- Deployment remains within one Supervisor Server and 1-8 Arc workers.
- Field IT reviewer has site access.
- Operator contact is known.
- No live connectors, external sends, remediation, or production server touch
  are being configured.

## Procedure

1. Confirm deployment mode: lab mock, small-business local planning, or hybrid
   planned.
2. Confirm tenant/customer context.
3. Record hardware inventory and hostname.
4. Confirm OS family, version ref, worker account, and disk encryption status.
5. Confirm network segment, DNS/hostname, supervisor endpoint ref, and clock
   sync source.
6. Confirm no public inbound worker exposure.
7. Confirm worker is not placed on guest Wi-Fi or production management network.
8. Confirm device identity ref and channel identity ref are planned.
9. Confirm policy bundle ref, capability manifest hash ref, and model bundle ref
   or cloud-only placeholder.
10. Confirm evidence writer posture and emergency spool placeholder are
    understood.
11. Confirm rollback/escape plan.
12. Stop deployment if any identity, network, encryption, policy, or evidence
    check is missing or ambiguous.

## Approval Requirements

Operator approval is required before enrollment. Field IT preflight does not
approve remediation, software installation, connector access, or production
system access.

## Evidence To Capture

- Completed checklist ref.
- Hardware and OS profile refs.
- Network readiness ref.
- Supervisor endpoint ref.
- Identity/channel refs.
- Policy/model refs.
- Reviewer ID.
- Open blocker list.

## Rollback/Containment

- Missing supervisor reachability: do not enroll.
- Missing identity/channel refs: do not enroll.
- Encryption unavailable for sensitive-worker plan: block sensitive work.
- Suspicious device or network posture: quarantine or reject worker.

## Escalation Path

- Network or DNS issue: field IT reviewer.
- Identity or attestation issue: security reviewer.
- Evidence failure: evidence writer failure runbook.
- LIMA IT request: diagnostic/read-only handoff only.

## Done Criteria

- Preflight evidence exists.
- All blockers are resolved or explicitly accepted as blocked/deferred.
- Worker deployment can proceed to enrollment review or remains blocked.
