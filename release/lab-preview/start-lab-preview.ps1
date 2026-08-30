[CmdletBinding()]
param(
    [string]$InstallRoot,
    [string]$DocumentRoot,
    [switch]$SupervisorExecutionOptIn,
    [switch]$ArcExecutionOptIn,
    [switch]$EmitDocumentContent,
    [int]$UiPort = 8765,
    [switch]$EnableLocalModel,
    [switch]$LocalModelSupervisorOptIn,
    [switch]$LocalModelArcOptIn,
    [string]$LocalModelName = "qwen2.5:7b",
    [string]$LocalModelEndpoint = "http://127.0.0.1:11434"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($InstallRoot)) {
    $InstallRoot = Join-Path $env:LOCALAPPDATA "SparkPitLabs\LimaOfficeLabPreview"
}
$InstallRoot = [System.IO.Path]::GetFullPath($InstallRoot)
$officeRoot = Join-Path $InstallRoot "sources\Lima-Office"
$arcRoot = Join-Path $InstallRoot "sources\Arc-Bot-shell"
$python = Join-Path $InstallRoot "venv\Scripts\python.exe"
$manifest = Join-Path $InstallRoot "config\installation.json"

foreach ($required in @($officeRoot, $arcRoot, $python, $manifest)) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "The lab preview is not completely installed: $required"
    }
}
if ($SupervisorExecutionOptIn -xor $ArcExecutionOptIn) {
    throw "Working mode requires separate Supervisor and Arc opt-ins."
}
if ($EmitDocumentContent -and (-not $SupervisorExecutionOptIn -or -not $ArcExecutionOptIn)) {
    throw "Document content requires both execution opt-ins."
}
if (($SupervisorExecutionOptIn -or $ArcExecutionOptIn) -and [string]::IsNullOrWhiteSpace($DocumentRoot)) {
    throw "Working mode requires an explicit safe document root."
}

if (($LocalModelSupervisorOptIn -or $LocalModelArcOptIn) -and -not $EnableLocalModel) {
    throw "Local-model opt-ins require -EnableLocalModel."
}
if ($LocalModelEndpoint -notin @("http://127.0.0.1:11434", "http://localhost:11434")) {
    throw "The lab local-model endpoint must be loopback Ollama on port 11434."
}
if ([string]::IsNullOrWhiteSpace($LocalModelName) -or $LocalModelName -match "\s") {
    throw "Local model name must be non-empty and contain no whitespace."
}
if (($LocalModelSupervisorOptIn -xor $LocalModelArcOptIn) -and $EnableLocalModel) {
    Write-Warning "Local AI will remain disabled until both independent opt-ins are supplied."
}

$arguments = @(
    (Join-Path $officeRoot "scripts\arc-runtime-harness.py"),
    "--arc-source", $arcRoot,
    "--session-dir", (Join-Path $InstallRoot "data\runtime-harness"),
    "--ui-port", [string]$UiPort
)
if (-not [string]::IsNullOrWhiteSpace($DocumentRoot)) {
    $resolvedDocuments = [System.IO.Path]::GetFullPath($DocumentRoot)
    if (-not (Test-Path -LiteralPath $resolvedDocuments -PathType Container)) {
        throw "Document root is not a directory."
    }
    $arguments += @("--document-root", $resolvedDocuments)
}
if ($SupervisorExecutionOptIn) { $arguments += "--execution-opt-in" }
if ($ArcExecutionOptIn) { $arguments += "--execute-granted-capability" }
if ($EmitDocumentContent) { $arguments += "--emit-document-content" }

Write-Output "Starting attended localhost lab preview. Press Ctrl+C to stop."
if ($EnableLocalModel) {
    $arguments += @("--local-model-enabled", "--local-model-endpoint", $LocalModelEndpoint, "--local-model-name", $LocalModelName)
}
if ($LocalModelSupervisorOptIn) { $arguments += "--local-model-supervisor-opt-in" }
if ($LocalModelArcOptIn) { $arguments += "--local-model-arc-opt-in" }

& $python @arguments
exit $LASTEXITCODE
