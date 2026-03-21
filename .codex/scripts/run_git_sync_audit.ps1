[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
    [ValidateSet("none", "warning", "error")]
    [string]$FailOn = "warning",
    [string]$OutputDir = ""
)

$resolvedRepositoryRoot = (Resolve-Path $RepositoryRoot).Path
if ([string]::IsNullOrWhiteSpace($OutputDir)) {
    $OutputDir = Join-Path $resolvedRepositoryRoot "var\git_sync"
}

$venvPython = Join-Path $resolvedRepositoryRoot ".venv312\Scripts\python.exe"
$pythonExe = if (Test-Path $venvPython) { $venvPython } else { "python" }
$auditScript = Join-Path $resolvedRepositoryRoot ".codex\scripts\git_sync_audit.py"

New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

$arguments = @(
    $auditScript,
    "--repo-root",
    $resolvedRepositoryRoot,
    "--fail-on",
    $FailOn,
    "--write-json",
    (Join-Path $OutputDir "git_sync_audit_latest.json"),
    "--write-markdown",
    (Join-Path $OutputDir "git_sync_audit_latest.md"),
    "--append-jsonl",
    (Join-Path $OutputDir "git_sync_audit_history.jsonl")
)

& $pythonExe @arguments
exit $LASTEXITCODE
