[CmdletBinding()]
param(
    [string]$InstallRoot,
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($env:OS -ne "Windows_NT") {
    throw "This lab-preview installer supports Windows only."
}
if ($PSVersionTable.PSVersion -lt [version]"5.1") {
    throw "PowerShell 5.1 or newer is required."
}
if ([string]::IsNullOrWhiteSpace($InstallRoot)) {
    if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
        throw "LOCALAPPDATA is required for the default installation."
    }
    $InstallRoot = Join-Path $env:LOCALAPPDATA "SparkPitLabs\LimaOfficeLabPreview"
}

$InstallRoot = [System.IO.Path]::GetFullPath($InstallRoot)
$driveRoot = [System.IO.Path]::GetPathRoot($InstallRoot)
if ($InstallRoot.TrimEnd("\") -eq $driveRoot.TrimEnd("\")) {
    throw "Refusing to install at a drive root."
}
if (-not [string]::IsNullOrWhiteSpace($env:USERPROFILE)) {
    $profile = [System.IO.Path]::GetFullPath($env:USERPROFILE).TrimEnd("\")
    if ($InstallRoot.TrimEnd("\") -eq $profile) {
        throw "Refusing to install over the user profile."
    }
}

$manifestPath = Join-Path $PSScriptRoot "manifest.json"
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    throw "The release manifest is missing."
}
$manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
if ($manifest.schema_version -ne "lima-office-arc-lab-preview-manifest-v1") {
    throw "Unsupported release manifest."
}
if ($manifest.production_ready -ne $false) {
    throw "This installer accepts lab-preview manifests only."
}

foreach ($commandName in @("python", "git")) {
    if ($null -eq (Get-Command $commandName -ErrorAction SilentlyContinue)) {
        throw "$commandName is required."
    }
}
$pythonCommand = (Get-Command python).Source
$pythonVersion = [version]((& $pythonCommand -c "import platform; print(platform.python_version())").Trim())
if ($pythonVersion -lt [version]"3.11") {
    throw "Python 3.11 or newer is required."
}

if (Test-Path -LiteralPath $InstallRoot) {
    if (-not $Force) {
        throw "Install root already exists. Re-run with -Force to move it to a recoverable backup."
    }
    $stamp = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ")
    $backup = "$InstallRoot.backup-$stamp"
    Move-Item -LiteralPath $InstallRoot -Destination $backup
}

New-Item -ItemType Directory -Force -Path $InstallRoot | Out-Null
$sources = Join-Path $InstallRoot "sources"
$officeRoot = Join-Path $sources "Lima-Office"
$arcRoot = Join-Path $sources "Arc-Bot-shell"
$venvRoot = Join-Path $InstallRoot "venv"
$configRoot = Join-Path $InstallRoot "config"
$dataRoot = Join-Path $InstallRoot "data"
foreach ($directory in @($sources, $configRoot, $dataRoot)) {
    New-Item -ItemType Directory -Force -Path $directory | Out-Null
}

function Install-ExactSource {
    param(
        [Parameter(Mandatory = $true)][string]$Repository,
        [Parameter(Mandatory = $true)][string]$Commit,
        [Parameter(Mandatory = $true)][string]$Destination
    )
    & git -c maintenance.auto=false init --quiet $Destination
    if ($LASTEXITCODE -ne 0) { throw "Unable to initialize source checkout." }
    & git -C $Destination remote add origin "https://github.com/$Repository.git"
    if ($LASTEXITCODE -ne 0) { throw "Unable to configure source remote." }
    & git -c maintenance.auto=false -C $Destination fetch --quiet --depth 1 origin $Commit
    if ($LASTEXITCODE -ne 0) { throw "Unable to fetch exact commit for $Repository." }
    & git -C $Destination checkout --quiet --detach FETCH_HEAD
    if ($LASTEXITCODE -ne 0) { throw "Unable to checkout exact commit for $Repository." }
    $actual = (& git -C $Destination rev-parse HEAD).Trim()
    if ($actual -ne $Commit) { throw "Source identity mismatch for $Repository." }
}

try {
    Install-ExactSource -Repository $manifest.components.lima_office.repo -Commit $manifest.components.lima_office.commit -Destination $officeRoot
    Install-ExactSource -Repository $manifest.components.arc_worker.repo -Commit $manifest.components.arc_worker.commit -Destination $arcRoot

    $officeLock = Get-Content -Raw -LiteralPath (Join-Path $officeRoot "stack.lock.json") | ConvertFrom-Json
    if ($officeLock.dependencies.'arc-bot-shell'.commit -ne $manifest.components.arc_worker.commit) {
        throw "Office lock and artifact Arc identity disagree."
    }
    if ($officeLock.dependencies.'lima-runtime'.commit -ne $manifest.components.lima_runtime.commit) {
        throw "Office lock and artifact LIMA identity disagree."
    }
    if ($officeLock.dependencies.'guardian-suite'.commit -ne $manifest.components.guardian.commit) {
        throw "Office lock and artifact Guardian identity disagree."
    }

    & $pythonCommand -m venv $venvRoot
    if ($LASTEXITCODE -ne 0) { throw "Unable to create the preview virtual environment." }
    $venvPython = Join-Path $venvRoot "Scripts\python.exe"
    & $venvPython -m pip install --disable-pip-version-check --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw "Unable to update pip." }
    & $venvPython -m pip install --disable-pip-version-check -r (Join-Path $officeRoot "requirements-lab.txt")
    if ($LASTEXITCODE -ne 0) { throw "Unable to install the exact governed stack." }
    & $venvPython -m pip install --disable-pip-version-check --no-deps $arcRoot
    if ($LASTEXITCODE -ne 0) { throw "Unable to install Arc." }

    & $venvPython (Join-Path $officeRoot "scripts\check-stack-pins.py") --check-installed
    if ($LASTEXITCODE -ne 0) { throw "Office installed-package identity check failed." }
    & $venvPython (Join-Path $arcRoot "scripts\check-stack-pins.py") --check-installed
    if ($LASTEXITCODE -ne 0) { throw "Arc installed-package identity check failed." }

    Copy-Item -LiteralPath $manifestPath -Destination (Join-Path $configRoot "release-manifest.json")
    $installation = [ordered]@{
        schema_version = "lima-office-arc-installation-v1"
        installed_at = [DateTime]::UtcNow.ToString("o")
        install_root = $InstallRoot
        version = $manifest.version
        production_ready = $false
        startup_registered = $false
        model_installed = $false
        network_scope = "localhost_only"
        office_commit = $manifest.components.lima_office.commit
        arc_commit = $manifest.components.arc_worker.commit
        lima_commit = $manifest.components.lima_runtime.commit
        guardian_commit = $manifest.components.guardian.commit
    }
    $installation | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $configRoot "installation.json") -Encoding UTF8
    $installation | ConvertTo-Json -Depth 8
}
catch {
    $failure = [ordered]@{
        schema_version = "lima-office-arc-install-failure-v1"
        failed_at = [DateTime]::UtcNow.ToString("o")
        error_type = $_.Exception.GetType().Name
        message = $_.Exception.Message
    }
    $failure | ConvertTo-Json -Compress | Set-Content -LiteralPath (Join-Path $configRoot "install-failure.json") -Encoding UTF8
    throw
}
