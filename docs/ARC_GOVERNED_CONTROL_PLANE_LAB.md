# Arc governed control-plane lab slice

This slice proves one narrow operating path:

```text
structured operator request
  -> Supervisor-derived classification
  -> mandatory Guardian Core decision
  -> lima.runtime.run_governed_request
  -> SQLite evidence
  -> non-executing Arc assignment preview
  -> Arc acknowledgement or rejection
  -> persisted evidence result
```

Arc Bot is the product-facing worker. Sparkbot is not required by this slice
and remains only a possible future operator/evidence display.

## Pinned lab dependencies

- Guardian Suite:
  `69e843218c521b913edcec404dea6b7be8c64f06`
- LIMA AI OS:
  `4e9b08a69fc8a8cbe5aba685198a30770627422f`
- LIMA package:
  `lima-runtime==0.1.0rc1`
- Supported LIMA API:
  `lima.runtime.run_governed_request`

Install the isolated lab dependencies with:

```bash
python -m pip install -r requirements-lab.txt
```

Run the end-to-end smoke with an explicit disposable database path:

```bash
python scripts/arc_control_plane_smoke.py \
  --database /tmp/lima-office-control-plane.db \
  --request-id arc-control-plane-smoke-001
```

The smoke must show an acknowledged safe-read preview, preserved SQLite
evidence after reopening the database, replay rejection, Guardian policy
identity, and zero side-effect counters.

## Safety boundary

- The caller cannot set action category, tool identity, tenant role, or policy
  authority.
- Guardian is mandatory. Missing, invalid, expired, or mismatched Guardian
  decisions deny the request.
- LIMA must carry the same non-authorizing Guardian decision reference that the
  Supervisor verified, including the policy snapshot, request and payload
  hashes, tenant, worker, action, and expiry. The Supervisor verifies the exact
  echo and persists its hash before an Arc assignment preview can be offered.
- The Supervisor rejects LIMA's compatibility fallback policy.
- Arc receives metadata only through `worker.assignment.preview`.
- Every result preserves `runtime_authority_blocked=true`,
  `executable=false`, `execution_allowed=false`, and
  `side_effects_allowed=false`.
- SQLite stores redacted metadata and hashes, not raw prompts, credentials,
  provider tokens, tool arguments, or secret values.
- Duplicate request hashes and idempotency keys fail closed.
- Offline, quarantined, unknown, or capability-ineligible workers receive no
  assignment preview.

This is a single-process lab control plane with an in-process Arc preview
endpoint and configured actor identities. It does not provide network
transport, production authentication, multi-tenant operation, approval
execution, providers, models, tools, connectors, external sends, file
mutation, background work, robotics, IoT, or physical-world control.
