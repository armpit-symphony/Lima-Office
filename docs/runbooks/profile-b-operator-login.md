# Profile B Operator Login

## Purpose

Let an attended operator sign in to the localhost Supervisor UI with Windows Hello or a platform passkey, and confirm that a session exists only after the assertion signature verifies.

## Scope

One Supervisor Server on the lab PC. Loopback only. One named local owner. No customer data, no connectors, and no Arc dispatch. The session dies when the harness process stops.

## Preconditions

- Windows 10 or 11 with Windows Hello already enrolled for the person at the keyboard.
- Microsoft Edge or Chrome. The page hostname must be `localhost`. The numeric loopback address is not a valid passkey origin.
- The harness is bound to `127.0.0.1`. Open the office UI through the localhost hostname on that same port.
- No LAN interface, reverse proxy, or extra startup task is enabled for this check.
- The `webauthn` package from the lab requirements is installed. If it is missing, the ceremony reports unavailable and no session is created.
- Profile A may still be offered. It is the lab-only attended bind, not Profile B.
- Leave `--profile-b-helper` unset. A helper replaces the localhost verifier and is not part of this check.

## Required approval

None for this login check. The ceremony does not approve work. Do not treat a successful Hello prompt as permission to send mail, change records, install software, or dispatch Arc.

## Evidence to capture

- Harness readiness JSON showing `loopback_only: true`, `operator_authentication_manifest: true`, `production_ready: false`, and `customer_pilot_allowed: false`.
- The UI message after both Hello prompts. The success text says the passkey assertion was verified and that approval authority remains off.
- Health JSON showing `operator_authentication: true`, `production_ready: false`, and `customer_pilot_allowed: false`.
- A redacted note of the owner display name and the time. Do not copy ceremony bytes, assertion signatures, or session handles into tickets or screenshots.

## Procedure

1. Start the existing lab harness. Do not pass a helper path.
2. Open the Supervisor Console on localhost and choose Profile B sign-in.
3. Enter the owner display name and start the Windows Hello / passkey ceremony.
4. Complete Hello when the browser asks to create the passkey, then complete Hello again when it asks to sign the assertion. Both prompts must finish within 120 seconds. They use one challenge.
5. Read the UI result. After a verified assertion, the status says signed in for this process. Approval authority stays off.
6. Confirm health reports `operator_authentication: true` while `production_ready` and `customer_pilot_allowed` stay false. Approval authority stays off. The authentication flag is a lab path claim. It does not mean the operator may approve work.
7. Confirm a worker refresh through `/api/v1/workers` without a session handle is denied. With the handle the UI holds for this tab, the refresh is allowed and still reports no approval authority.
8. Confirm public Profile B status does not show the session handle.
9. Stop and start the harness. The previous session is gone. The next sign-in creates a new passkey and signs a new assertion.

A second sign-in in the same running process only asks for the assertion. The public credential from the first sign-in stays in that process and is dropped on exit.

## Refuse path

The API still refuses a session when any of these are true:

- The assertion signature does not verify, or the body is not a WebAuthn assertion.
- The origin is not localhost, including the numeric loopback address.
- The RP ID hash is not `localhost`, user verification is missing, or the credential belongs to a different owner display name.
- The challenge is expired, reused, or does not match the assertion.
- The helper path is unset and something other than the localhost verifier claims the assertion was accepted without a signature check.

Hello may still appear on the screen in those cases. The UI must say that no approval authority was created, and public status must stay signed out when no earlier session exists.

The lab HMAC verifier is for automated tests, not for the attended PC. The old fail-closed test double is not the harness default.

## Rollback or stop

Stop the harness from its terminal or the existing lab stop control. The Profile B session and the in-memory public credential end with the process. Profile A, if still enabled, is unchanged. Do not delete evidence to clear a failed ceremony.

## Escalation

Stop if the browser offers a ceremony for any host other than localhost, if the UI claims approval or dispatch, or if a session appears when the assertion was cancelled or the UI says it was not accepted. Capture the redacted UI text and hand it to the lab owner. Do not retry with a copied assertion.

## Open questions

`operator_authentication: true` is the signed lab path claim. It does not grant approval, Arc dispatch, production readiness, or customer-pilot permission. Positive approval step-up remains a stub. The display name is keyboard-chosen and is not directory identity. Hello proves local user verification only. Attestation format is `none`. A signature counter that stays at zero cannot show that the authenticator was cloned. The credential is process memory only. Profile C is still a separate identity choice. A separate yes is still required before any tag, prerelease, or installer publish.
