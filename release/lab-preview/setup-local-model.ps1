[CmdletBinding()]
param(
    [string]$Model = "qwen2.5:7b",
    [switch]$InstallOllama,
    [switch]$PullModel
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($env:OS -ne "Windows_NT") {
    throw "This lab model setup supports Windows only."
}
if ([string]::IsNullOrWhiteSpace($Model) -or $Model -match "\s") {
    throw "Model must be a non-empty Ollama model name without whitespace."
}

$ollamaCommand = Get-Command ollama -ErrorAction SilentlyContinue
if ($null -eq $ollamaCommand -and $InstallOllama) {
    $wingetCommand = Get-Command winget -ErrorAction SilentlyContinue
    if ($null -eq $wingetCommand) {
        throw "Ollama is missing and winget is unavailable. Install Ollama from https://ollama.com/download/windows."
    }
    Write-Output "Installing Ollama because -InstallOllama was explicitly supplied."
    & $wingetCommand.Source install --exact --id Ollama.Ollama --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) { throw "Ollama installation failed." }
    $ollamaCommand = Get-Command ollama -ErrorAction SilentlyContinue
}
if ($null -eq $ollamaCommand) {
    [ordered]@{
        status = "action_required"
        ollama_installed = $false
        model = $Model
        next_step = "Install Ollama, then rerun with -PullModel."
    } | ConvertTo-Json
    exit 2
}

if ($PullModel) {
    Write-Output "Downloading $Model because -PullModel was explicitly supplied."
    & $ollamaCommand.Source pull $Model
    if ($LASTEXITCODE -ne 0) { throw "Ollama model download failed." }
}

$installedNames = @(
    & $ollamaCommand.Source list |
        Select-Object -Skip 1 |
        ForEach-Object { ($_ -split "\s+")[0] }
)
$modelReady = $installedNames -contains $Model
$result = [ordered]@{
    status = if ($modelReady) { "ready" } else { "action_required" }
    ollama_installed = $true
    model = $Model
    model_installed = $modelReady
    endpoint = "http://127.0.0.1:11434"
    network_scope = "loopback_only"
    automatic_startup_added = $false
    next_step = if ($modelReady) {
        "Start the preview with -EnableLocalModel -LocalModelSupervisorOptIn -LocalModelArcOptIn."
    } else {
        "Rerun this script with -PullModel."
    }
}
$result | ConvertTo-Json
if (-not $modelReady) { exit 2 }
