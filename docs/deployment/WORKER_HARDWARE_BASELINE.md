# Worker Hardware Baseline

## Purpose

Define vendor-neutral mini PC classes for Arc workers and supervisor-adjacent
machines. This is a planning baseline, not a purchasing recommendation.

## Mini PC Classes

| Class | CPU | RAM | Storage | Network | Intended use |
| --- | --- | --- | --- | --- | --- |
| Lightweight worker | 4 cores | 16 GB | 256 GB SSD | Wired preferred, Wi-Fi acceptable in lab | Drafting, ticket classification, metadata-only file planning |
| Standard worker | 6-8 cores | 32 GB | 512 GB SSD | Wired Ethernet | General office drafts, file clerk work, read-only diagnostics |
| Local-model worker | 8+ cores or suitable GPU/NPU | 32-64 GB | 1 TB SSD preferred | Wired Ethernet | Local-first model routes where policy permits |
| Supervisor/helper-capable machine | 8+ cores | 32-64 GB | 1 TB SSD preferred | Wired Ethernet | Supervisor-side services or helper-agent planning, not independent workers |

## CPU/RAM/Storage Assumptions

- Minimum worker CPU: 4 cores.
- Minimum worker RAM: 16 GB.
- Minimum worker storage: 256 GB SSD.
- Standard worker storage should leave headroom for logs, local cache, evidence
  spool placeholder, update staging, and rollback records.
- Local-model workers need extra RAM/storage based on the model bundle class.

## Network Assumptions

- Wired Ethernet is preferred for stable heartbeat.
- Wi-Fi is acceptable only for lab mock or non-critical draft workers.
- Workers should not sit on guest networks or direct production management
  networks.

## TPM And Secure Boot

TPM, secure boot, or equivalent device identity support is preferred for future
attestation. In this phase, attestation remains a placeholder. A missing TPM or
secure boot signal cannot be treated as higher trust.

## Storage Encryption

Storage encryption is expected where the OS supports it. If encryption is not
available, the worker should remain blocked from sensitive data, local model
cache, durable memory, and privileged work until policy defines the exception.

## Backup/Restore Expectations

- Worker nodes should be replaceable rather than treated as durable sources of
  truth.
- Supervisor-owned records, policy refs, and evidence refs are the authoritative
  sources.
- Local cache should be purgeable on revoke, quarantine, retirement, or customer
  exit/delete.
- Backup of raw worker cache is not approved in this blueprint.

## Hardware Inventory Fields

Inventory should record:

- Worker ID.
- Deployment ID.
- Hostname.
- Intended role.
- Hardware class.
- CPU class.
- RAM GB.
- Storage GB.
- Storage encryption status.
- TPM/secure boot availability.
- Network interface.
- OS family and version ref.
- Supervisor endpoint ref.
- Policy bundle ref.
- Model bundle ref or cloud-only placeholder.
- Last field IT reviewer.
- Evidence refs.

## What Not To Require Yet

- Exact consumer product SKUs.
- Enterprise device-management platform.
- Production remote-control stack.
- Hardware attestation enforcement.
- GPU/NPU for every worker.
- Multi-site or multi-tenant hardware standard.
