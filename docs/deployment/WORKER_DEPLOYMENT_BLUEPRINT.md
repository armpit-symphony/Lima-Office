# Worker Deployment Blueprint

## Purpose

Define the practical Arc worker mini PC deployment model for LIMA Office OS.
This blueprint is docs/contracts scaffolding only. It does not install software,
start services, run background workers, wire live connectors, call external
model providers, send messages, mutate customer systems, or perform remediation.

Worker attestation trust-root posture in this lane is tracked by
`worker.attestation` metadata and
[Worker Attestation Trust Root](../architecture/WORKER_ATTESTATION_TRUST_ROOT.md).

## Target Deployment

The target deployment is:

- 1 Supervisor Server.
- 1-8 Arc worker mini PCs.
- One small-business tenant/customer context at a time.
- Guardian-gated model, tool, file, network, connector, outbound, scheduled,
  and privileged operations.
- Human approval for privileged or high-risk work.
- Evidence refs for important setup, health, quarantine, update, and rollback
  events.

Lab mode should start with 1-3 workers and scale only after the field checklist,
health/heartbeat posture, quarantine, and rollback gates are exercised.

## Supervisor Placement Assumptions

- Supervisor Server is on trusted business-owned infrastructure.
- Supervisor has stable local hostname/addressing and a documented endpoint ref.
- Supervisor storage, backup, and restore posture remain planning topics; this
  blueprint does not implement backup services.
- Supervisor restart must be visible to workers as degraded or unreachable
  heartbeat state, not hidden background recovery.
- Operator access to Supervisor status requires future IdP/MFA and RBAC policy.
- Governance scaffolding for identity/MFA, access review, approver separation,
  breakglass, attestation, and update/rollback is documented in
  [Governance Docs](../governance/README.md). Provider selection and runtime
  enforcement remain blocked.

## Deployment Modes

### Lab Mock

- Mock/in-memory runtime state only.
- No live connectors or external sends.
- Supervisor and workers may run on a trusted lab LAN.
- Worker deployment records can be represented through
  `worker.deployment` examples and docs.
- Validation is local contract/doc/test validation, not production
  certification.

### Small-Business Local

- Planned deployment mode for one business-owned site.
- Supervisor and workers are on a controlled local network segment.
- Workers initiate heartbeat to the Supervisor Server.
- No public inbound worker exposure.
- Connectors remain mock/readiness-only until separate connector trust approval.
- LIMA IT handoff remains diagnostics/read-only unless future approval expands
  it.

### Hybrid Planned

- Future posture where the Supervisor Server may use approved cloud or managed
  components for policy, evidence export, or model routing.
- Worker nodes still require Guardian decisions and evidence.
- External model/provider use remains blocked until model routing defaults,
  data classification, egress posture, redaction, and approval rules are
  resolved.

## Worker Role Examples

### Admin Worker

Coordinates low-risk internal admin drafts, internal summaries, and read-only
status preparation. It does not receive unrestricted file, browser, network, or
connector access.

### File Clerk Worker

Prepares draft file organization plans, reads allowed metadata, and produces
evidence refs. File move, rename, export, delete, or overwrite remains approval
required or blocked by policy.

### Customer Service Draft Worker

Drafts customer-service replies and classifies inbound issues. It cannot send
external email/text/chat and cannot mutate customer records.

### IT Diagnostic Helper Worker

Collects read-only diagnostic summaries and prepares LIMA IT handoff metadata.
It cannot run remediation, install/update software, reconfigure networks, or
touch production servers.

Despite the name, this is an Arc worker role. It is not a supervisor-side helper
agent and it does not inherit helper-agent trust or unrestricted tools.

## Hardware Assumptions

### Minimum

- 4-core CPU.
- 16 GB RAM.
- 256 GB SSD.
- Reliable wired LAN preferred; Wi-Fi acceptable only for lab mock.
- Dedicated OS account for worker operation.
- Storage encryption enabled where the OS supports it.

### Recommended

- 6-8 CPU cores.
- 32 GB RAM.
- 512 GB SSD.
- Wired Ethernet.
- TPM or equivalent device identity support preferred.
- Secure boot enabled where practical.

### Local-Model Capable

- 8+ CPU cores or suitable GPU/NPU.
- 32-64 GB RAM depending on model class.
- 1 TB SSD preferred for model bundles and cache headroom.
- Local model bundle refs are policy-controlled and hash-tracked.

### Cloud/Subscription-Model Only

- No local model bundle required.
- Worker may prepare model route metadata only.
- External model calls remain blocked until model routing policy, provider class,
  data classification, egress, redaction, and approval gates are approved.

See [Worker Hardware Baseline](WORKER_HARDWARE_BASELINE.md) for the detailed
class table.

## OS Assumptions

- Windows or Linux are acceptable for planning.
- Dedicated non-admin worker account.
- Disk encryption enabled where available.
- Automatic login is not assumed.
- OS patch posture is recorded, but software install/update execution requires
  approval.
- Secrets are not stored in repo files or config examples.

## Network Assumptions

- Workers initiate communication to the Supervisor Server.
- No inbound public worker exposure in MVP.
- No direct cross-worker trust.
- Firewall policy allows worker-to-supervisor heartbeat and scoped local control
  traffic only.
- DNS/hostname naming should be stable and inventory-backed.
- Hybrid egress, if later approved, must go through Guardian policy and evidence.

See [Network Blueprint](NETWORK_BLUEPRINT.md).

## Supervisor Connectivity

Supervisor connectivity expectations:

- Stable supervisor endpoint ref.
- Authenticated worker-supervisor channel planned through mTLS or equivalent.
- Worker heartbeat target and expected interval recorded.
- Supervisor owns worker registry, policy bundle refs, capability leases,
  quarantine/revoke state, and evidence refs.

## Worker Identity

Each worker must have:

- Stable `worker_id`.
- Device identity ref.
- Channel identity ref.
- Tenant/customer context binding.
- Capability manifest hash ref.
- Policy bundle ref.
- Role assignment.
- Operator enrollment evidence.

Attestation is a placeholder in this phase. TPM/secure boot are preferred future
inputs, but absence of attestation cannot be treated as stronger trust.
See [Worker Attestation Policy](../governance/WORKER_ATTESTATION_POLICY.md) and
[Worker Attestation Failure](../runbooks/worker-attestation-failure.md).

## Policy/Model Hash Expectations

Workers should record:

- Policy bundle ref and hash.
- Capability manifest hash ref.
- Tool-pack scope version.
- Model bundle ref or explicit cloud-only placeholder.
- Update channel and rollback state.

Policy/model hashes are refs, not raw payloads. A hash mismatch should degrade
or quarantine the worker until reviewed.

## Local Encrypted Cache Expectations

The local cache is planned only. It must be:

- Tenant-bound.
- Task-scoped.
- Encrypted at rest where available.
- Expiring.
- Cleared on revoke or approved retirement.
- Free of plaintext secrets, bearer tokens, raw sensitive connector payloads,
  and unredacted customer data.

## Logging Expectations

Worker logs should include operational state, correlation IDs, heartbeat state,
policy/model refs, and error codes. Logs must not include secrets, tokens, raw
prompts, raw connector payloads, or unredacted sensitive data.

## Support Ownership

Small-business support ownership should be explicit:

- Operator: approves enrollment, re-enrollment, quarantine release requests, and
  visible deployment state.
- Supervisor admin: maintains Supervisor status views and worker registry
  metadata.
- Field IT reviewer: verifies hardware, OS, network, DNS, time sync, and
  rollback/readiness checklists.
- Security reviewer: reviews identity mismatch, attestation failure, capability
  drift, suspicious tool requests, and release from security quarantine.
- LIMA IT handoff owner: receives read-only diagnostic handoff metadata only.

## Health/Heartbeat Expectations

Planned heartbeat posture:

- Default lab interval: 60 seconds unless policy changes it.
- Degraded candidate: 2 missed heartbeats or evidence writer degraded.
- Offline candidate: 5 missed heartbeats or supervisor unreachable.
- Quarantine candidate: identity failure, capability mismatch, evidence writer
  failure, suspicious tool request, update verification failure, or operator
  containment.

These values are planning defaults. Runtime thresholds remain policy-controlled
and must be tested before any lab expansion.

## Update/Rollback Expectations

Update channels:

- Policy bundle.
- Worker runtime.
- Model bundle.
- Config.

All update plans require evidence refs, operator visibility, known-good rollback
state, and quarantine on failed or suspicious update. Software install/update
execution requires approval and is not implemented by this blueprint.
See [Signed Update Rollback Policy](../governance/SIGNED_UPDATE_ROLLBACK_POLICY.md)
and [Update Rollback Approval](../runbooks/update-rollback-approval.md).

## Quarantine/Re-Enrollment Expectations

Quarantine stops new assignments and blocks privileged actions. Re-enrollment
requires:

- Operator review.
- Identity recheck.
- Capability manifest review.
- Policy bundle review.
- Cache purge evidence where required.
- Guardian decision and evidence refs.

## Blocked For MVP

- Live connectors, OAuth/provider wiring, connector tokens, webhooks, live reads,
  or live writes.
- External email/text/chat sends or form submission.
- External model provider calls.
- Browser automation.
- Real remediation, software install/update execution, endpoint control, network
  changes, or production server touch.
- Databases, queues, web servers, schedulers, daemons, UI frameworks, or
  production operations.
- Unrestricted browser, file, network, shell, connector, or tool access.
- Cross-tenant memory sharing.
- Marketing, pricing, sales, TAM, or production-readiness claims.

## Acceptance Gates

- Blueprint stays inside 1 Supervisor Server and 1-8 Arc workers.
- Worker roles map to least-privilege tool-pack scopes.
- Worker identity, policy refs, model refs, encryption status, attestation
  placeholder, update channel, rollback state, and evidence refs can be
  represented by `worker.deployment`.
- No worker has public inbound exposure or direct cross-worker trust.
- Every action path remains Guardian-gated and evidence-producing.
- Quarantine, revoke, re-enrollment, update, and rollback are visible and
  documented.
- Validation passes for schemas, examples, docs links, tests, compile checks,
  and git whitespace checks.
