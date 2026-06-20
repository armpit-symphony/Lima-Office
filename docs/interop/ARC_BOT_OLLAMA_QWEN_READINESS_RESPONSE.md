# Arc Bot Ollama/Qwen Readiness Response

Arc Bot can consume a read-only readiness packet with these safe fields:

- `worker_id`
- `tenant_id`
- supervisor attachment status as operator-attested, no-probe metadata
- `route_mode` limited to `mock_only` or `local_planned` for this packet
- `route_status` using the current schema values:
  `selected`, `degraded`, `denied`, `blocked_mvp`, or `unavailable`
- Arc-local presentation labels `ready`, `setup_required`, `blocked`, and
  `degraded` may still be shown, but they must map onto the canonical LIMA
  Office route states above and must not become a second source of truth.
- `approved_runtime_family: ollama`
- `approved_model_family: qwen`
- `approved_model_alias` or tag
- a localhost endpoint label or route ID, not a live endpoint claim
- `hardware_profile_ref` or hardware-profile summary metadata
- Ollama install attestation ref
- Ollama service reachable attestation ref
- Qwen model present attestation ref
- Guardian decision refs
- evidence refs
- policy refs for local-model-only, no-cloud-fallback, and no-provider-token

Fail closed if any required field is missing, mismatched, or ambiguous. In
particular, fail closed if the packet would imply live execution, provider
fallback, socket probing, connector behavior, or provider-token use.

Arc Bot must not infer permission to call Ollama, call Qwen, open sockets, use
provider credentials, or treat the endpoint label as connectivity proof.

LIMA Office will not provide runtime execution, live model calls, connector
behavior, or provider-token wiring in this handoff. This is metadata only.

Next handshake recommendation: keep this as a docs-only, operator-attested
projection and open a separate later-phase review only if a dedicated schema is
needed for attachment status or model-alias labels.
