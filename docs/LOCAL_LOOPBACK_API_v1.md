# Local Loopback API v1

Status: lab source. Not a production or customer-pilot API.
Scope: one Supervisor Server, one tenant, localhost only.

## Bind

The harness listens on `127.0.0.1` only. Any other bind address is refused before the socket opens. A request whose client address is not `127.0.0.1`, or whose `Host` header is not `127.0.0.1` or `localhost` for this port, is denied. LAN bind, reverse proxies, and non-loopback origins are out of scope.

## Versioning

- Current prefix: `/api/v1`.
- Legacy prefix: `/api/office`. Those routes remain during the lab.7 transition and respond with `Deprecation: true` and a successor link to `/api/v1`.
- New UI login uses `/api/v1`. Existing lab screens may still call the legacy aliases until that package cut.

## Authentication

Anonymous clients may read loopback health, build identity, the API descriptor, the redacted console projection, and Profile B status. Profile B status does not republish the session handle.

These POSTs establish a session and do not authorize office work:

- `/api/v1/operator-session/bind` — Profile A, and only while the lab-only flag is on.
- `/api/v1/operator-session/profile-b/begin`
- `/api/v1/operator-session/profile-b/complete`

Every other POST under `/api/v1`, including unknown paths, requires a session handle in `X-Lima-Operator-Session`. The handle is returned once by bind or complete. It is process memory, expires in 30 minutes, and is dropped on restart. A missing, expired, or unknown handle is `unauthenticated`. The browser must not treat a public GET as a way to recover the handle.

Profile A remains available until `--disable-profile-a-lab` is set. That flag does not enable customer or production use.

## Profile B

Profile B is the Windows Hello / passkey / WebAuthn-class operator login for the localhost Supervisor UI.

- The owner supplies a display name. The raw OS username is not stored.
- The default verifier checks a WebAuthn assertion for RP ID `localhost` before it creates a session. An unverified, tampered, expired, or wrong-origin assertion does not create a session. The lab HMAC verifier remains for tests. An absolute `--profile-b-helper` / `LIMA_OFFICE_PROFILE_B_HELPER` program replaces the default verifier when the operator sets it. Helper stderr is discarded. The helper path and assertion are not written to evidence.
- The first ceremony in a process enrolls an ES256 public key and then requires an assertion signature. A later ceremony in that process checks the stored public key. Both the public key and the session stay in process memory. `survives_restart` is false.
- Positive approval step-up is `stub_only`. This API does not issue an approval token, approval result, or Arc dispatch.

The verifier note is [PROFILE_B_WEBAUTHN_VERIFICATION.md](PROFILE_B_WEBAUTHN_VERIFICATION.md). OS steps for the attended ceremony are in [profile-b-operator-login.md](runbooks/profile-b-operator-login.md).

## Resources

| Route | Auth | Notes |
| --- | --- | --- |
| `GET /api/v1` | public read | Route descriptor. `runtime_authority_blocked` is true. |
| `GET /api/v1/health` and `GET /api/v1/build` | public read | Build identity. `operator_authentication` is true as a localhost Profile B path claim. `production_ready` and `customer_pilot_allowed` stay false. |
| `GET /api/v1/state` | public read | Same redacted console projection as the legacy state alias. |
| `GET /api/v1/operator-session` | public read | Active flag, assurance, and expiry. No session handle. |
| `GET /api/v1/workers` | session | Cached worker count only. |
| `POST /api/v1/workers` | session | Explicit inventory refresh. |
| `POST /api/v1/evidence` | session | Redacted evidence trace. |
| `GET /api/v1/sop` | session | SOP titles only. Instruction bodies are not included. |
| Proposal, preview, request, conversation, and helper POSTs | session | Same lab services as the legacy aliases. They still cannot approve or dispatch. |

Downstream Guardian denials stay fail-closed after the session check. They do not become approval.

## Contracts

- [local.api.v1.descriptor.schema.json](../contracts/v1/local.api.v1.descriptor.schema.json)
- [local.api.v1.error.schema.json](../contracts/v1/local.api.v1.error.schema.json)
- [local.api.v1.health.schema.json](../contracts/v1/local.api.v1.health.schema.json)
- [local.api.v1.sop_list.schema.json](../contracts/v1/local.api.v1.sop_list.schema.json)
- [operator.profile_b.ceremony.schema.json](../contracts/v1/operator.profile_b.ceremony.schema.json)
- [operator.profile_b.session.schema.json](../contracts/v1/operator.profile_b.session.schema.json)

## Non-goals

This slice does not add a foreign operator-shell API, LAN bind, Profile C / OIDC, positive approval tokens, Arc dispatch of approved work, connectors, or customer data. The lab preview manifest keeps `production_ready` and `customer_pilot_allowed` false. `operator_authentication` true is the lab path claim from [ADR-0024](DECISIONS.md#adr-0024-claim-localhost-profile-b-authentication-in-lab-packaging-only). It does not mean production readiness, customer-pilot permission, or approval authority. A separate yes is still required before any tag or installer publish.

## Evidence and logs

Ceremony and login evidence store ids, hashes, verifier mode, and authority flags. They do not store assertions, helper output, passwords, or raw OS usernames. Request logs stay on the request line and do not include header or body values.
