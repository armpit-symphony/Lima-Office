# Worker Install Layout

## Purpose

Define a proposed filesystem layout and naming convention for future Arc worker
deployment planning. This document does not install files, create services, or
provide executable automation.

## Service Naming Conventions

Planning names:

- Worker service: `lima-arc-worker`
- Heartbeat reporter: `lima-arc-heartbeat`
- Evidence spool helper: `lima-arc-evidence-spool`
- Update staging helper: `lima-arc-update-stage`

These names are placeholders. No service is implemented or enabled by this
blueprint.

## Linux Layout

```text
/opt/lima-office/worker/
  bin/
  config/
  policy/
  model/
  cache/
  logs/
  evidence-spool/
  updates/staging/
  updates/rollback/
```

## Windows Layout

```text
C:\ProgramData\LIMAOffice\Worker\
  bin\
  config\
  policy\
  model\
  cache\
  logs\
  evidence-spool\
  updates\staging\
  updates\rollback\
```

## Directory Expectations

| Directory | Purpose | Boundary |
| --- | --- | --- |
| `bin` | Future worker binaries or scripts | Empty in docs-only phase |
| `config` | Environment-specific config refs | No secrets or bearer tokens |
| `policy` | Policy bundle refs and hashes | Guardian-controlled |
| `model` | Local model bundle refs | No external provider credentials |
| `cache` | Task-scoped local cache | Encrypted, tenant-bound, purgeable |
| `logs` | Operational logs | No secrets or raw sensitive payloads |
| `evidence-spool` | Emergency evidence placeholder | Metadata refs only until durable posture is approved |
| `updates/staging` | Future staged update files | Signed/verified update gate required later |
| `updates/rollback` | Known-good rollback refs | Evidence required |

## Config Directory

Config examples should use placeholders only:

```text
LIMA_TENANT_ID=<tenant-ref>
LIMA_CUSTOMER_CONTEXT_ID=<customer-context-ref>
LIMA_WORKER_ID=<worker-id>
LIMA_SUPERVISOR_ENDPOINT_REF=<supervisor-endpoint-ref>
LIMA_POLICY_BUNDLE_REF=<policy-bundle-ref>
LIMA_MODEL_BUNDLE_REF=<model-bundle-ref-or-none>
```

No API keys, OAuth codes, passwords, cookies, bearer tokens, signatures, or
private keys belong in repo docs or config examples.

## Policy Bundle Directory

Policy bundle files are future artifacts. Deployment records should reference
policy bundle refs and hashes, not embed policy payloads in worker logs or
evidence summaries.

## Model/Cache Directory

Local model bundles are optional and policy-controlled. Cloud/subscription-only
workers should use an explicit model placeholder ref rather than a provider
credential.

Local cache must be tenant-bound, encrypted where available, expiring, and
purgeable on revoke, quarantine, retirement, or customer exit/delete.

## Logs Directory

Logs should be operational and metadata-only. Include correlation IDs, worker
state, heartbeat state, and error codes. Do not log raw prompts, connector
payloads, customer files, secrets, or approval token material.

## Evidence Spool Placeholder

The evidence spool directory is a placeholder for future durable evidence
posture. Evidence writer failure remains fail-closed for privileged actions.
Spool depth, retry/backoff, disk-full threshold, reconciliation, and export
rules remain policy gates.

## Update And Rollback Directories

Update staging and rollback directories are planning placeholders. Automatic
update execution is blocked. Software install/update requires approval,
evidence, signed/verified source, known-good rollback ref, and quarantine on
failed verification.
