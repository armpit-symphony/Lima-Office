# Profile B Operator Login

## Purpose

Let an attended operator start a Windows Hello or passkey ceremony against the localhost Supervisor UI, and see that the lab build does not turn that ceremony into approval authority.

## Scope

One Supervisor Server on the lab PC. Loopback only. One named local owner. No customer data, no connectors, and no Arc dispatch.

## Preconditions

- Windows 10 or 11 with Windows Hello already enrolled for the person at the keyboard.
- Microsoft Edge or Chrome. The page hostname must be `localhost`. The numeric loopback address is not a valid passkey origin.
- The harness is bound to `127.0.0.1`. Open the office UI through the localhost hostname on that same port.
- No LAN interface, reverse proxy, or extra startup task is enabled for this check.
- Profile A may still be offered. It is the lab-only attended bind, not Profile B.

## Required approval

None for this login check. The ceremony does not approve work. Do not treat a successful Hello prompt as permission to send mail, change records, install software, or dispatch Arc.

## Evidence to capture

- Harness readiness JSON showing `loopback_only: true` and `operator_authentication_manifest: false`.
- The UI message after the ceremony. The default lab verifier says no session was created.
- A redacted note of the owner display name and the time. Do not copy ceremony bytes, helper output, or session handles into tickets or screenshots.

## Procedure

1. Start the existing lab harness. Do not pass a helper path unless a later reviewed helper is present.
2. Open the Supervisor Console on localhost and choose Profile B sign-in.
3. Enter the owner display name and start the Windows Hello / passkey ceremony.
4. Complete Hello at the keyboard if the browser shows it.
5. Read the UI result. With the default fail-closed verifier, Hello may run and the API still refuses the session.
6. Confirm health still reports `production_ready: false`, `customer_pilot_allowed: false`, and `operator_authentication: false`.
7. Confirm a worker refresh through `/api/v1/workers` without a session handle is denied.

A configured platform helper is optional and operator-trusted. Leave it unset for this spike. The lab HMAC verifier is for automated tests, not for the attended PC.

## Rollback or stop

Stop the harness from its terminal or the existing lab stop control. The Profile B session is process memory and ends with the process. Profile A, if still enabled, is unchanged. Do not delete evidence to clear a failed ceremony.

## Escalation

Stop if the browser offers a ceremony for any host other than localhost, if the UI claims approval or dispatch, or if a session appears while the helper path was unset and the message says the assertion was accepted. Capture the redacted UI text and hand it to the lab owner. Do not retry with a copied assertion.

## Open questions

Signature verification of a real WebAuthn attestation is not implemented. `operator_authentication` stays false in the lab manifest until that verifier and a later packaging brief exist. Positive approval step-up remains a stub.
