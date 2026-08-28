[CmdletBinding()]
param(
    [string]$InstallRoot,
    [string]$DocumentRoot,
    [switch]$SupervisorExecutionOptIn,
    [switch]$ArcExecutionOptIn,
    [switch]$EmitDocumentContent,
    [int]$UiPort = 8765
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
& $python @arguments
exit $LASTEXITCODE
