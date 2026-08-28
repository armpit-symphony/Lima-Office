[CmdletBinding()]
param([string]$InstallRoot)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($InstallRoot)) {
    $InstallRoot = Join-Path $env:LOCALAPPDATA "SparkPitLabs\LimaOfficeLabPreview"
}
$InstallRoot = [System.IO.Path]::GetFullPath($InstallRoot)
$officeRoot = Join-Path $InstallRoot "sources\Lima-Office"
$arcRoot = Join-Path $InstallRoot "sources\Arc-Bot-shell"
$python = Join-Path $InstallRoot "venv\Scripts\python.exe"

& $python (Join-Path $officeRoot "scripts\check-stack-pins.py") --check-installed
if ($LASTEXITCODE -ne 0) { throw "Office pin smoke failed." }
& $python (Join-Path $arcRoot "scripts\check-stack-pins.py") --check-installed
if ($LASTEXITCODE -ne 0) { throw "Arc pin smoke failed." }
& $python (Join-Path $officeRoot "scripts\arc-execution-grant-smoke.py") --arc-source $arcRoot
if ($LASTEXITCODE -ne 0) { throw "Execution-grant smoke failed." }
& $python (Join-Path $officeRoot "scripts\arc-multi-worker-supervisor-smoke.py") --arc-source $arcRoot --worker-count 1
if ($LASTEXITCODE -ne 0) { throw "Single-worker supervisor smoke failed." }

Write-Output "LIMA Office + Arc Lab Preview smoke: PASS"
