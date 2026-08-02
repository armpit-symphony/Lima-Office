# Governed Arc office session

One command that brings up a worker and a Supervisor and takes repeated
requests at a prompt.

```bash
python scripts/arc-office-session.py \
  --arc-source /path/to/Arc-Bot-shell \
  --document-root /path/to/documents \
  --execution-opt-in \
  --execute-granted-capability \
  --emit-document-content
```

```
arc> read report.txt
  status     : acknowledged
  grant      : issued
  performed  : True
  bytes      : 61
  capability : document_read
  side effects: False

Q3 revenue summary for the governed office lab.
Second line.

arc> quit
```

## Why it exists

Running the lab by hand means three terminals, two ephemeral keys pasted on
stdin in the right order, and ports copied out of readiness JSON — and one
request per invocation. That is workable for proving the path and unusable for
actually working in it for an hour.

## What it does not do

It is convenience around the real processes, not a shortcut through them.

- **It does not weaken either gate.** `--execution-opt-in` and
  `--execute-granted-capability` are still off unless passed, and they are
  handed to the processes that own them rather than being decided here. All
  four gate combinations behave exactly as they do when run by hand.
- **It does not print, log, or persist a channel key.** Both keys are generated
  per session and reach the child processes only on stdin.
- **It performs no read itself.** Every request runs the real Arc operator CLI
  against the real Supervisor, so a session behaves like the hand-run path.
- **It refuses to continue if a component reports an executable boundary.**

## Commands

| Command | Effect |
|---|---|
| `read <path>` | Governed document read, relative to the document root |
| `status` | Read-only worker status request |
| `info` | Identities, ports, and gate settings |
| `help` | Command list |
| `quit` / `exit` | Stop both processes and leave |

`status` never produces a grant. `it_diagnostics_read_only` is not in
`EXECUTABLE_CAPABILITIES`, so it stays a preview-only request and reports
`execution_grant_absent`. That is correct, not a failure.

## resource_type is enumerated, and "document" is not a member

Worth knowing before it costs you an hour.

`guardian.decision` enumerates `resource_type`. The members include `file`,
`folder`, `worker_status`, `draft_message`, `terminal`, `credential_ref`, and
others — but **not** `document`.

A request naming `document` is denied *before Guardian produces any decision*,
and surfaces as:

```
status     : denied
denied for : recon_missing_guardian_decision
```

That reason code describes the reconciliation symptom rather than the cause,
which is a poor diagnostic for what is really "unsupported resource_type". The
session uses `file` for documents, which is the correct member.

Note that `scripts/arc-operator-supervisor-smoke.py` reads a document while
passing `resource_type=worker_status`. That is valid and it works, but it
describes the resource incorrectly.

## Reading a denial

The summary reports the Supervisor's own outcome first, then Arc's.

An upstream denial and a gate refusal look completely different, and reporting
only Arc's reason code hides the difference: a request denied by the Supervisor
shows up downstream as `execution_grant_absent`, which points at the Supervisor
opt-in when the actual cause was the request itself. Check `status` and
`denied for` before assuming a gate is misconfigured.

| Reason | Meaning |
|---|---|
| `execution_grant_absent` | No grant arrived — Supervisor opt-in off, or the capability is not grantable |
| `arc_execution_opt_in_disabled` | Grant arrived, Arc opt-in off |
| `document_root_not_configured` | Arc has nothing it may read |
| `document_not_utf8_text` | Read succeeded, text withheld as it is not UTF-8 |
| `content_not_requested` | Read succeeded, `--emit-document-content` not passed |

## Session state

Replay and evidence databases live in a temporary directory that is removed on
exit. Pass `--session-dir` to keep them — the Supervisor evidence database is
the record of what the session did.
