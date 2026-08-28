# LIMA Office + Arc Lab Preview

This artifact installs one attended, localhost-only LIMA Office Supervisor and
the Arc worker source selected by the release manifest. It is a test preview,
not a customer pilot or production release.

## Verify

Compare the ZIP SHA-256 with the adjacent checksum file before extraction.
Open manifest.json and confirm production_ready is false.

## Install on Windows

Run PowerShell from the extracted artifact directory:

    powershell -ExecutionPolicy Bypass -File .\install-lab-preview.ps1

The default destination is:

    %LOCALAPPDATA%\SparkPitLabs\LimaOfficeLabPreview

The installer requires Python 3.11 or newer, Git, and network access to fetch
the exact manifest commits. It creates an isolated virtual environment. It
does not install a model, create a startup task, open a firewall rule, or start
a background service.

## Smoke

    powershell -ExecutionPolicy Bypass -File .\smoke-lab-preview.ps1

## Start in Training mode

    powershell -ExecutionPolicy Bypass -File .\start-lab-preview.ps1

The printed URL is bound to 127.0.0.1. Keep the terminal open and press Ctrl+C
to stop.

## Enable the bounded document lane

Use test documents only. Both execution owners must opt in separately:

    powershell -ExecutionPolicy Bypass -File .\start-lab-preview.ps1 -DocumentRoot C:\safe-test-documents -SupervisorExecutionOptIn -ArcExecutionOptIn

Add -EmitDocumentContent only when the operator intends the UI to display the
bounded document contents. The allowed working capabilities are document-list
and document-read. External sends, connectors, mutations, remediation,
production access, robotics, LAN exposure, and hidden background actions are
blocked.

The localhost UI does not yet authenticate the operator. Do not expose it to a
LAN, reverse proxy, customer data, or unattended use.
