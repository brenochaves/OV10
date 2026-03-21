[CmdletBinding()]
param(
    [string]$TaskName = "OV10 Git Sync Audit",
    [string]$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
    [ValidateRange(5, 720)]
    [int]$IntervalMinutes = 30,
    [ValidateSet("none", "warning", "error")]
    [string]$FailOn = "warning"
)

$resolvedRepositoryRoot = (Resolve-Path $RepositoryRoot).Path
$runnerScript = Join-Path $resolvedRepositoryRoot ".codex\scripts\run_git_sync_audit.ps1"
if (-not (Test-Path $runnerScript)) {
    throw "Missing runner script at $runnerScript"
}

$taskAction = @(
    "pwsh.exe"
    "-NoLogo"
    "-NoProfile"
    "-ExecutionPolicy"
    "Bypass"
    "-File"
    ('""{0}""' -f $runnerScript)
    "-RepositoryRoot"
    ('""{0}""' -f $resolvedRepositoryRoot)
    "-FailOn"
    $FailOn
) -join " "

& schtasks.exe `
    /Create `
    /SC MINUTE `
    /MO $IntervalMinutes `
    /TN $TaskName `
    /TR $taskAction `
    /F

if ($LASTEXITCODE -ne 0) {
    throw "Failed to register scheduled task '$TaskName'."
}

Write-Output "Registered scheduled task '$TaskName' for repository sync audits every $IntervalMinutes minutes."
