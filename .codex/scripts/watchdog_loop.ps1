$ErrorActionPreference = "Continue"

$interval = if ($env:INTERVAL_SECONDS) { [int]$env:INTERVAL_SECONDS } else { 300 }

while ($true) {
    try {
        & codex continue
    } catch {
        Write-Verbose ("codex continue failed: " + $_.Exception.Message)
    }
    Start-Sleep -Seconds $interval
}
