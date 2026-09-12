[CmdletBinding()]
param(
    [ValidateSet("Start", "Restart", "Stop", "Status", "EnableLogin", "DisableLogin")]
    [string]$Action = "Start",
    [string]$InstallRoot = $PSScriptRoot,
    [ValidateRange(1024,65535)][int]$UiPort = 8766,
    [ValidateSet("Arc", "Office")][string]$Surface = "Arc",
    [switch]$OpenBrowser
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$InstallRoot = [IO.Path]::GetFullPath($InstallRoot).TrimEnd("\")
$installationPath = Join-Path $InstallRoot "config\installation.json"
if (-not (Test-Path -LiteralPath $installationPath)) { throw "Choose an installed Arc lab directory." }
$installation = Get-Content -Raw -LiteralPath $installationPath | ConvertFrom-Json
if ($installation.schema_version -ne "lima-office-arc-installation-v1" -or $installation.production_ready -ne $false) {
    throw "Only a local Arc lab installation is supported."
}
$python = Join-Path $InstallRoot "venv\Scripts\python.exe"
$office = Join-Path $InstallRoot "sources\Lima-Office"
$arc = Join-Path $InstallRoot "sources\Arc-Bot-shell"
$harness = Join-Path $office "scripts\arc-runtime-harness.py"
$data = Join-Path $InstallRoot "data\runtime-harness"
$recordPath = Join-Path $data "lifecycle.json"
$tokenPath = Join-Path $data "lifecycle-token.txt"
$manager = Join-Path $InstallRoot "manage-arc-preview.ps1"
$sha = [Security.Cryptography.SHA256]::Create()
try { $identity = ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($InstallRoot.ToLowerInvariant())))).Replace("-","").Substring(0,16) }
finally { $sha.Dispose() }
$startupLink = Join-Path ([Environment]::GetFolderPath("Startup")) ("Arc Lab " + $identity + ".lnk")
$url = "http://127.0.0.1:$UiPort"
$openUrl = if ($Surface -eq "Office") { "$url/office/" } else { "$url/" }
$mutex = New-Object Threading.Mutex($false, ("Local\ArcLab-" + $identity))
$locked = $false
function Get-Health {
    try { return Invoke-RestMethod -Uri "$url/api/health" -TimeoutSec 2 } catch { return $null }
}
function Get-ManagedProcess {
    if (-not (Test-Path -LiteralPath $recordPath)) { return $null }
    $record = Get-Content -Raw -LiteralPath $recordPath | ConvertFrom-Json
    $process = Get-Process -Id $record.process_id -ErrorAction SilentlyContinue
    if ($null -eq $process) { return $null }
    if ($record.port -ne $UiPort) { throw "Use the configured port: $($record.port)." }
    if ($process.StartTime.ToUniversalTime().ToString("o") -ne $record.started_at -or $process.Path -ne $python) {
        throw "Process identity changed. Refusing to stop or adopt an unrelated process."
    }
    return $process
}
function Stop-Managed {
    $process = Get-ManagedProcess
    if ($null -eq $process) {
        if ($null -ne (Get-Health)) { throw "Port belongs to an unmanaged service. Stop its original launcher first." }
        return
    }
    $token = (Get-Content -Raw -LiteralPath $tokenPath).Trim()
    Invoke-RestMethod -Method Post -Uri "$url/api/lifecycle/stop" -ContentType "application/json" -Body (@{token=$token}|ConvertTo-Json -Compress) -TimeoutSec 5 | Out-Null
    if (-not $process.WaitForExit(30000)) { throw "Graceful stop timed out; no process was force-killed." }
}
try {
    $locked = $mutex.WaitOne(0)
    if (-not $locked) { throw "Another Arc lifecycle command is running. Try again shortly." }
    if ($Action -in @("EnableLogin","DisableLogin")) {
        if (-not (Test-Path -LiteralPath $manager)) { throw "Install the manager inside the Arc lab directory first." }
        if ($Action -eq "EnableLogin") {
            $shell = New-Object -ComObject WScript.Shell
            $shortcut = $shell.CreateShortcut($startupLink)
            $shortcut.TargetPath = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
            $shortcut.Arguments = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + $manager + '" -Action Start -InstallRoot "' + $InstallRoot + '" -UiPort ' + $UiPort + ' -Surface ' + $Surface + ' -OpenBrowser'
            $shortcut.WorkingDirectory = $InstallRoot
            $shortcut.WindowStyle = 7
            $shortcut.Description = "Open the localhost LIMA Office + Arc lab at login; no tasks run automatically."
            $shortcut.Save()
        } elseif (Test-Path -LiteralPath $startupLink) {
            $shell = New-Object -ComObject WScript.Shell
            $shortcut = $shell.CreateShortcut($startupLink)
            if (-not $shortcut.Arguments.Contains('"' + $manager + '"')) { throw "Startup shortcut identity mismatch." }
            Remove-Item -LiteralPath $startupLink
        }
        [pscustomobject]@{login_startup=(Test-Path -LiteralPath $startupLink);shortcut=$startupLink;surface=$Surface;open_url=$openUrl} | ConvertTo-Json
        return
    }
    if ($Action -eq "Status") {
        $health = Get-Health
        [pscustomobject]@{running=($null -ne $health);url=$url;open_url=$openUrl;surface=$Surface;login_startup=(Test-Path -LiteralPath $startupLink)} | ConvertTo-Json
        return
    }
    if ($Action -in @("Stop","Restart")) { Stop-Managed }
    if ($Action -eq "Stop") { Write-Output "Arc stopped. Training data and SOPs retained."; return }
    $existing = Get-ManagedProcess
    if ($null -eq $existing) {
        if ($null -ne (Get-Health)) { throw "Port is occupied by an unmanaged service." }
        foreach ($path in @($python,$harness,$arc)) { if (-not (Test-Path -LiteralPath $path)) { throw "Incomplete installation: $path" } }
        New-Item -ItemType Directory -Force -Path $data | Out-Null
        $bytes = New-Object byte[] 32
        $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
        try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
        $token = ([BitConverter]::ToString($bytes)).Replace("-","").ToLowerInvariant()
        [IO.File]::WriteAllText($tokenPath, $token)
        # Restrict the lifecycle secret to this Windows user. Never export it.
        $acl = New-Object Security.AccessControl.FileSecurity
        $acl.SetAccessRuleProtection($true,$false)
        $sid = [Security.Principal.WindowsIdentity]::GetCurrent().User
        $acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule($sid,"FullControl","Allow")))
        [IO.File]::SetAccessControl($tokenPath, $acl)
        $arguments = @($harness,"--arc-source",$arc,"--session-dir",$data,"--ui-port",[string]$UiPort,
            "--installation-info",$installationPath,"--lifecycle-token-file",$tokenPath,
            "--local-model-enabled","--local-model-supervisor-opt-in","--local-model-arc-opt-in")
        # Paths with embedded quotes/newlines are not accepted as command arguments.
        foreach ($value in $arguments) { if ($value -match '["\r\n]') { throw "Unsupported quote or newline in installation path." } }
        $quoted = ($arguments | ForEach-Object { '"' + $_ + '"' }) -join " "
        $stamp = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssfff")
        $outLog = Join-Path $data ("launcher-" + $stamp + ".out.log")
        $errLog = Join-Path $data ("launcher-" + $stamp + ".err.log")
        $process = Start-Process -FilePath $python -ArgumentList $quoted -WorkingDirectory $InstallRoot -WindowStyle Hidden -RedirectStandardOutput $outLog -RedirectStandardError $errLog -PassThru
        @{process_id=$process.Id;started_at=$process.StartTime.ToUniversalTime().ToString("o");port=$UiPort} |
            ConvertTo-Json | Set-Content -LiteralPath $recordPath -Encoding UTF8
        $deadline = [DateTime]::UtcNow.AddSeconds(45)
        do {
            $process.Refresh()
            if ($process.HasExited) { throw "Arc failed to start. Inspect $errLog" }
            if ($null -ne (Get-Health)) { break }
            Start-Sleep -Milliseconds 500
        } while ([DateTime]::UtcNow -lt $deadline)
        if ($null -eq (Get-Health)) { throw "Arc startup timed out. Inspect $errLog" }
    } elseif ($null -eq (Get-Health)) { throw "Managed Arc is not healthy; use Restart." }
    Write-Output "LIMA Office + Arc ready at $openUrl (training only). Start/Restart/Stop and login controls are in $InstallRoot."
    if ($OpenBrowser) { Start-Process -FilePath $openUrl -WindowStyle Hidden }
} finally {
    if ($locked) { $mutex.ReleaseMutex() }
    $mutex.Dispose()
}
