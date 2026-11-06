# Profile B WebAuthn Verification

Status: lab source. This note is the contract for the localhost verifier. Health, the API descriptor, the session record, the public Profile B summary, the Supervisor console projection, harness readiness, and the lab-preview manifest report `operator_authentication` / `operator_authentication_manifest` true. That value is a lab capability claim for the localhost Profile B path. `production_ready` and `customer_pilot_allowed` stay false. The claim does not authorize approval, Arc dispatch, connectors, or customer use.

## Library

The verifier uses PyPI package `webauthn` 2.8.x (Duo Labs `py_webauthn`). That package checks the assertion signature with `cryptography` and decodes CBOR with `cbor2`. LIMA Office calls it only from `lima_office/runtime/webauthn_verifier.py`.

Accepted public keys are ES256 (COSE alg `-7`) only. The console asks the platform authenticator for that algorithm. The lab does not fetch attestation roots and does not add another WebAuthn stack.

If the package cannot be imported, the ceremony is unavailable and no session is created.

## Relying party

- RP ID is `localhost` only.
- Accepted origins are `http://localhost` and `https://localhost`, with an optional port from 1 through 65535.
- `127.0.0.1`, any other host, a path, or `crossOrigin: true` is refused.
- The harness bind stays `127.0.0.1`. The browser page must still be opened as `localhost` so the passkey origin matches the RP ID.

## Challenge

- One challenge is 32 random bytes, issued as base64url.
- TTL is 120 seconds (`CHALLENGE_TTL_SECONDS`). The browser timeout is the same 120000 ms.
- `complete` consumes the challenge before verification. A second submit, an expired challenge, or a challenge that does not match `clientDataJSON` does not create a session.

## Credential storage

Storage is process memory on the verifier object. It does not survive a process restart. The session record also keeps `survives_restart: false`.

Each stored record is:

- the owner display name supplied at `begin`
- the credential id
- the COSE public key
- the signature counter

One record per display name. A later verified enrollment for that same name replaces it. A different display name cannot use that credential id.

The private key stays in the platform authenticator. The lab does not collect a PIN, a shared secret, or the OS account name. Evidence and the session record store `device_binding_ref` and `credential_id_hash` only. They do not store the assertion, the attestation object, or the public key. Public `/api/v1/operator-session` does not return the session handle.

## Ceremony

First login in a process is `registration_then_assertion`:

1. The browser creates a platform credential (`attestation: none`, user verification required).
2. The browser signs an assertion for that new credential with the same challenge.
3. The server checks the registration (challenge, localhost origin, RP ID hash, user presence, user verification, ES256 public key).
4. The server checks the assertion signature over `authenticatorData || SHA-256(clientDataJSON)` with that public key.
5. A Profile B session is created only after step 4 succeeds. A registration without a verified assertion stores nothing and creates no session.

A later login in the same process is `assertion`. The server checks the signature against the stored public key for that owner. The credential id must match. When the authenticator reports a non-zero signature counter, the counter must increase. A counter that stays at zero is accepted, because some platform authenticators always report zero; the one-time challenge still blocks replay of the same assertion.

A tampered signature, wrong origin, wrong RP ID, missing user verification, mismatched credential, or unknown credential returns the static rejection. No session is created.

## Packaging claim

`operator_authentication` and `operator_authentication_manifest` are true together. They come from `lima_office/runtime/lab_packaging.py`. The value means this localhost lab package has a Profile B authentication path. It is a capability claim. It is not a live "someone is signed in" bit. Public status still uses `active` for that.

`production_ready` and `customer_pilot_allowed` stay false on every surface that carries them, including the error envelope, health, the descriptor, and the lab-preview manifest. Positive approval step-up stays `stub_only`. `approval_authority` stays false. Profile C, LAN bind, and a durable credential store stay out of scope. `survives_restart` stays false. The public credential remains process memory only.

ES256 (COSE alg `-7`) stays the only accepted public key. RP ID stays `localhost`. The challenge TTL stays 120 seconds.

## Residual limits

The display name is chosen by the person at the keyboard. It is a label for the process-local credential. It is not a directory or IdP identity. Windows Hello proves user verification on the enrolled platform authenticator of this PC. It does not prove that the person is a named business directory principal. Attestation format is `none`, so the ceremony does not prove authenticator model or a certificate chain. The signature counter may stay at zero. Some platform authenticators never increment it, so clone detection from the counter is weak. The one-time challenge still blocks replay of the same assertion. A process restart drops the public credential. The packaging claim is about the path, not durable enrollment. A true authentication flag does not mean the package is ready for production or a customer pilot.
