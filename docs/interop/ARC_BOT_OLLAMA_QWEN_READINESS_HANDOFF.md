# Arc Bot Ollama/Qwen Readiness Handoff

## Purpose

This document answers the Arc Bot team's readiness question with LIMA Office
contract and policy references only. It is a docs/contracts/handoff artifact,
not a runtime integration.

Status: handoff and metadata contract only. It does not authorize model calls,
socket checks, provider access, connector behavior, or production claims.

## Arc Bot Request Summary

Arc Bot asked LIMA Office to confirm the safe worker and model-route metadata
fields it should consume for an Ollama/Qwen local readiness projection.

The Arc request is explicitly read-only and no-probe. It must not be treated as
permission to invoke Ollama, invoke Qwen, fall back to cloud providers, or use
provider tokens.

## LIMA Office Answer

LIMA Office already represents the required worker, deployment, lifecycle,
attestation, device trust, model-route, Guardian, policy, and evidence
boundaries in existing contracts and docs.

Several Arc request labels are not dedicated schema fields yet. For this handoff
they should remain packet labels mapped to existing refs and docs, not a new
runtime interface.

## Field Mapping

| Arc Bot requested field | LIMA Office contract/source | Required/optional | Example value shape | Notes / boundaries |
| --- | --- | --- | --- | --- |
| `worker_id` | `worker.deployment.worker_id`, `worker.lifecycle.worker_id`, `worker.heartbeat.worker_id`, `worker.attestation.worker_id` | Required | Opaque string | Worker identity metadata only. |
| `tenant_id` | Common v1 envelope across contracts | Required | Opaque string | Keep single-tenant scope explicit. |
| worker display name | `worker.deployment.role`, `worker.lifecycle.worker_role`, worker registry metadata if present | Optional | Human-readable label | No dedicated display-name field in the current core contracts. |
| supervisor attachment status | `worker.deployment.supervisor_endpoint_ref`, `worker.lifecycle.channel_identity_ref`, `worker.heartbeat.supervisor_received_at`, `worker.lifecycle.lifecycle_state`, `governance.device_trust` | Required as packet label | `operator_attested_no_probe` | Metadata only; do not infer live connectivity. |
| approved runtime family | `model.route.route_mode`, `model.route.provider_ref.provider_ref_type`, `docs/architecture/MODEL_ROUTING_DEFAULTS.md` | Required as packet label | `ollama` | Label only, not authorization. |
| approved model family | `model.route.local_model_bundle_ref`, `worker.deployment.model_bundle_ref`, `worker.deployment.model_bundle_hash_ref` | Required as packet label | `qwen` | Label only, not a live inference promise. |
| approved model alias / tag | `model.route.local_model_bundle_ref`, `worker.deployment.model_bundle_ref`, `worker.attestation.model_bundle_hash` | Required as packet label | `qwen2.5:7b` | Alias only; never a call target. |
| localhost endpoint label or route ID | `model.route.provider_ref.placeholder_ref`, `model.route.local_model_bundle_ref.bundle_ref`, `worker.deployment.supervisor_endpoint_ref` | Required as packet label | `route-label-ollama-qwen-local-001` | Label or route ID only. No live endpoint claim. |
| model-route status values | `model.route.route_status`, `model.route.route_mode`, `docs/architecture/MODEL_ROUTING_DEFAULTS.md` | Required | `selected`, `degraded`, `denied`, `blocked_mvp`, `unavailable` | `blocked_mvp` cannot be treated as selected. |
| Ollama install attestation | `worker.attestation.attestation_id`, `worker.attestation.evidence_refs`, `attestation.result`, `governance.device_trust.attestation_refs` | Required if claimed | Opaque attestation ref | Operator-attested snapshot only, no probe. |
| Ollama service reachable attestation | `worker.attestation.evidence_refs`, `attestation.result`, `governance.device_trust.attestation_refs` | Required if claimed | Opaque attestation ref | Must not be a socket probe or reachability proof. |
| Qwen model present attestation | `worker.deployment.model_bundle_ref`, `worker.deployment.model_bundle_hash_ref`, `worker.attestation.model_bundle_hash`, `attestation.result.reference_value_refs` | Required if claimed | Opaque attestation ref | No live inference and no provider fallback. |
| hardware profile | `worker.deployment.hardware_profile`, `docs/deployment/WORKER_HARDWARE_BASELINE.md` | Required | Hardware profile ref or summary object | Keep it metadata-only; no raw benchmark or probe output. |
| Guardian decision refs | `guardian.decision_id`, `policy_refs`, `docs/policies/README.md` | Required for future invocation linkage; not authorizing | Opaque ref array | Future-only linkage, not execution permission. |
| evidence refs | `evidence_refs` on `model.route`, `worker.deployment`, `worker.attestation`, `governance.device_trust`, `attestation.result`, `attestation.result.lineage` | Required | Opaque ref array | Refs only; no raw secrets or raw customer content. |
| local-model-only policy refs | `policy.model_routing_defaults.phase1a`, `policy.worker_attestation.phase0` | Required | Opaque ref array | Local-only posture only. |
| no-cloud-fallback policy refs | `policy.model_routing_defaults.phase1a`, `model.route.fallback_allowed`, `model.route.fallback_policy`, `model.route.fallback_reason_codes` | Required | Opaque ref array | Cloud/provider fallback is not allowed in this packet. |
| no-provider-token policy refs | `policy.approval_token_lifecycle.phase0`, `docs/CONTRACTS.md` | Optional but recommended | Opaque ref array | Current docs treat this as a boundary note, not a dedicated provider-token policy field. |

## Local-Only Boundaries

- No cloud fallback.
- No provider token.
- No live model call.
- No Ollama call.
- No Qwen inference.
- No connector behavior.
- No socket or network probe.
- No runtime authorization expansion.

## Model Route Readiness Semantics

- For this packet, `route_mode` should remain `mock_only` or `local_planned`
  unless a future change explicitly approves a different lane.
- `route_status` examples remain `selected`, `degraded`, `denied`,
  `blocked_mvp`, and `unavailable` as defined in the current schema.
- `blocked_mvp` cannot be treated as selected.
- `local_planned` means bundle-selection intent only. It does not imply local
  inference execution.
- `subscription_planned` and any cloud/provider fallback posture are not part
  of this readiness packet.
- `fallback_allowed` should remain false for this packet; if it is true, the
  packet is no longer safe for local-only readiness consumption.

## Worker Readiness Semantics

- Worker identity must include `worker_id` and `tenant_id`.
- Supervisor attachment must be represented as metadata only, using existing
  refs such as `supervisor_endpoint_ref`, `channel_identity_ref`, and
  `supervisor_received_at`.
- Worker lifecycle must not be treated as healthy-ready if the worker is
  quarantined, revoked, or retired.
- Device trust and attestation remain metadata only. They do not grant runtime
  execution or local model authority.

## Attestation Readiness Semantics

- `ollama_install_attestation_ref`,
  `ollama_service_reachable_attestation_ref`, and
  `qwen_model_present_attestation_ref` are readiness refs, not probes.
- `model_bundle_ref` and `model_bundle_hash_ref` may be used if the local
  bundle is already represented in deployment metadata.
- No raw TPM quotes, certificates, private keys, secrets, or provider tokens.
- No live inference should be inferred from any attestation ref.

## Guardian And Evidence Refs

- Readiness packets should carry Guardian decision refs and evidence refs.
- These refs provide audit and traceability only.
- They do not authorize model execution, endpoint access, connector behavior,
  or provider-token use.

## Safe Response To Arc Bot

- Arc Bot may consume this packet as read-only readiness metadata.
- Arc Bot must fail closed if any required field is missing, mismatched, or
  ambiguous.
- Arc Bot must not infer permission to execute models, call endpoints, or use
  provider tokens.
- Arc Bot must treat `blocked_mvp`, `quarantined`, `revoked`, and `retired`
  worker states as stop conditions.
- Arc Bot must treat endpoint labels as labels, not live reachability proof.

## Open Questions

- Should `supervisor_attachment_status` become a dedicated schema field, or
  remain a composed packet label?
- Should `approved_runtime_family`, `approved_model_family`, and
  `approved_model_alias` become dedicated schema fields in a later version, or
  remain packet labels only?
- Should there be a separate seat-readiness runbook for Ollama/Qwen local model
  checks, distinct from worker deployment and worker attestation review?
- Should a dedicated `no-provider-token` policy artifact be added later, or is
  the current contract and approval-token posture sufficient?

## Non-Goals

- No Ollama integration.
- No Qwen inference runtime.
- No live connector behavior.
- No socket, network, or provider probe.
- No provider-token wiring.
- No runtime authorization behavior.
- No background workers or daemons.
- No production-readiness claim.

## Source Links

- [Model Routing Defaults](../architecture/MODEL_ROUTING_DEFAULTS.md)
- [Worker Deployment Blueprint](../deployment/WORKER_DEPLOYMENT_BLUEPRINT.md)
- [Worker Hardware Baseline](../deployment/WORKER_HARDWARE_BASELINE.md)
- [Worker Lifecycle](../deployment/WORKER_LIFECYCLE.md)
- [Worker Attestation Policy](../governance/WORKER_ATTESTATION_POLICY.md)
- [Worker Attestation Trust Root](../architecture/WORKER_ATTESTATION_TRUST_ROOT.md)
- [Attestation Verifier Policy Reference Values](../architecture/ATTESTATION_VERIFIER_POLICY_REFERENCE_VALUES.md)
- [Durable Attestation Result Lineage](../architecture/DURABLE_ATTESTATION_RESULT_LINEAGE.md)
- [LIMA Office Contracts](../CONTRACTS.md)
