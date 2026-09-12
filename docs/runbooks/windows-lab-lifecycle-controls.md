# Windows Lab Lifecycle Controls

Status: Profile A localhost lab only; not production-ready

## Purpose

The packaged preview exposes one shared LIMA Office Supervisor and Arc lab
process. The Windows launchers choose which UI surface to open; they do not
create separate servers and do not grant task authority.

## Attended Controls

- `Start LIMA Office.cmd` starts the shared lab if needed and opens `/office/`.
- `Restart LIMA Office.cmd` gracefully stops the managed process, starts it
  again, and opens `/office/`.
- `Stop LIMA Office.cmd` gracefully stops only the process whose installation,
  PID, start time, executable, port, and lifecycle secret match.
- The Arc-named controls use the same lifecycle but open `/`.

Start and restart retain the SQLite session directory, including reviewed SOPs
and durable synthetic review records. They do not restore the process-only
attended operator binding.

## Optional Login Startup

`Enable LIMA Office at login.cmd` is an explicit owner action. It installs one
per-user Startup shortcut for this exact installation and opens `/office/` after
login. It starts no task, changes no firewall rule, needs no administrator
privilege, and grants no approval or worker-dispatch authority.

`Disable LIMA Office at login.cmd` removes only the shortcut whose manager path
matches this installation. Login startup is off after a clean install. The
Arc-named enable control selects `/`; both names update the same per-install
shortcut rather than creating duplicate startup processes.

## Verification

1. Start LIMA Office and confirm `/api/health` is ready on loopback.
2. Confirm the browser opens `/office/` and the UI says Profile A / lab only.
3. Restart and confirm saved SOP and durable synthetic records return.
4. Confirm the attended operator session must be explicitly rebound.
5. Enable login startup only when desired, inspect its reported shortcut path,
   then disable it and confirm the shortcut is removed.

Never expose the port to a LAN, enter customer data, or treat login presence as
production identity or approval.
