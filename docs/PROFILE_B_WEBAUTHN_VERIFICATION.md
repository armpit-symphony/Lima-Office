# Profile B WebAuthn Verification

Status: lab source. This note is the contract for the localhost verifier. It does not make the lab manifest report operator authentication, and it does not authorize approval, Arc dispatch, connectors, or customer use.

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

## What stays false

`operator_authentication`, `production_ready`, and `customer_pilot_allowed` stay false in the lab manifest, health payload, and session record. Positive approval step-up stays `stub_only`. Profile C, LAN bind, and a durable credential store are out of scope.

## Residual risk

The display name is chosen by the person at the keyboard. Windows Hello proves user verification on this PC; it does not prove a directory identity. `fmt: none` does not prove the authenticator model. A signature counter that never moves cannot detect a cloned authenticator. Those limits are why the manifest flag stays false until a later packaging brief.
