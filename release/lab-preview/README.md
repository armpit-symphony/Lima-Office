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
The separate model setup script changes nothing unless the operator explicitly
supplies `-InstallOllama` or `-PullModel`.

## Smoke

    powershell -ExecutionPolicy Bypass -File .\smoke-lab-preview.ps1

## Start in Training mode

    powershell -ExecutionPolicy Bypass -File .\start-lab-preview.ps1

The printed URL is bound to 127.0.0.1. Keep the terminal open and press Ctrl+C
to stop.
## Enable local AI-assisted SOP drafting

Check whether Ollama and the Apache-2.0 Qwen2.5 7B model are ready:

    powershell -ExecutionPolicy Bypass -File .\setup-local-model.ps1

On a PC where the model is missing, explicitly authorize its download:

    powershell -ExecutionPolicy Bypass -File .\setup-local-model.ps1 -PullModel

Then start with both independent local-model opt-ins:

    powershell -ExecutionPolicy Bypass -File .\start-lab-preview.ps1 -EnableLocalModel -LocalModelSupervisorOptIn -LocalModelArcOptIn

The AI can draft an SOP in Training mode. The draft is transient and is not
saved until a human reviews it and clicks **Save instruction**. Use synthetic
data only. No browser automation or form submission is included.

## Run the synthetic registration curriculum

Start the local-AI training mode, open the printed localhost URL, and use the
**Registration practice lab** panel. It contains five fixed fictional cases:
a complete record, a missing phone, an invalid email, an invalid postal code,
and contact consent not granted.

Use **Prepare practice form** for one case or **Run all 5** for the curriculum.
Arc copies valid supplied values exactly, leaves missing or invalid fields
blank, marks them `NEEDS_HUMAN_INPUT`, and records sanitized score/evidence
summaries in the local harness database. The mock Submit control is always
disabled, and the server has no registration-submit route.

This is repeatable SOP practice, not model-weight fine-tuning. Do not enter real
people's information. The curriculum has no browser, connector, customer-system
write, or external-send capability.

## Enable the bounded document lane

Use test documents only. Both execution owners must opt in separately:

    powershell -ExecutionPolicy Bypass -File .\start-lab-preview.ps1 -DocumentRoot C:\safe-test-documents -SupervisorExecutionOptIn -ArcExecutionOptIn

Add -EmitDocumentContent only when the operator intends the UI to display the
bounded document contents. The allowed working capabilities are document-list
and document-read. External sends, connectors, mutations, remediation,
cloud models, browser automation, production access, robotics, LAN exposure,
and hidden background actions are
blocked.

The localhost UI does not yet authenticate the operator. Do not expose it to a
LAN, reverse proxy, customer data, or unattended use.
