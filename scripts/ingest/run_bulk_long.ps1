param(
    [string]$ProjectRoot = "C:\JPop_Songwriter\AKIRA ENGINE",
    [string]$RegistryPath = "lyrics/bulk/artist_registry.longrun_dedup135.json",
    [int]$MaxRounds = 6,
    [int]$SleepMinutesBetweenRounds = 15
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-Location $ProjectRoot

$logDir = Join-Path $ProjectRoot "reports\discography\longrun"
$summaryRelative = "reports/discography/longrun/bulk_run_summary.longrun.json"
$summaryPath = Join-Path $ProjectRoot $summaryRelative
$statusPath = Join-Path $logDir "longrun_status.json"
$metaPath = Join-Path $logDir "longrun_meta.json"

New-Item -ItemType Directory -Path $logDir -Force | Out-Null

$meta = [ordered]@{
    project_root = $ProjectRoot
    registry = $RegistryPath
    pid = $PID
    started_at = (Get-Date).ToString("o")
    max_rounds = $MaxRounds
    sleep_minutes_between_rounds = $SleepMinutesBetweenRounds
}
$meta | ConvertTo-Json -Depth 6 | Set-Content -Path $metaPath -Encoding UTF8

for ($round = 1; $round -le $MaxRounds; $round++) {
    $roundStartedAt = (Get-Date).ToString("o")
    Write-Host "[$roundStartedAt] Starting bulk scrape round $round of $MaxRounds"

    & python "bulk_scrape_artists.py" `
        --registry $RegistryPath `
        --project-root . `
        --overwrite `
        --continue-on-error `
        --skip-completed `
        --normalize-manifests `
        --summary-output $summaryRelative

    $exitCode = $LASTEXITCODE
    $results = @()
    $failures = @()

    if (Test-Path $summaryPath) {
        $summary = Get-Content -Path $summaryPath -Raw | ConvertFrom-Json
        if ($summary.results) {
            $results = @($summary.results)
        }
        if ($summary.failures) {
            $failures = @($summary.failures)
        }
    }

    $completedCount = @($results | Where-Object { $_.status -eq "completed" }).Count
    $skippedCount = @($results | Where-Object { $_.status -eq "skipped" }).Count
    $failedCount = @($results | Where-Object { $_.status -eq "failed" }).Count

    $status = [ordered]@{
        project_root = $ProjectRoot
        registry = $RegistryPath
        pid = $PID
        updated_at = (Get-Date).ToString("o")
        round = $round
        max_rounds = $MaxRounds
        exit_code = $exitCode
        total_results = $results.Count
        completed = $completedCount
        skipped = $skippedCount
        failed_results = $failedCount
        failure_count = $failures.Count
        round_started_at = $roundStartedAt
        summary_path = $summaryPath
    }
    $status | ConvertTo-Json -Depth 8 | Set-Content -Path $statusPath -Encoding UTF8

    Write-Host (
        "[{0}] Round {1} finished exit={2} completed={3} skipped={4} failures={5}" -f
        (Get-Date).ToString("o"),
        $round,
        $exitCode,
        $completedCount,
        $skippedCount,
        $failures.Count
    )

    if ($exitCode -eq 0 -and $failures.Count -eq 0) {
        Write-Host "[$((Get-Date).ToString('o'))] Bulk scrape completed without remaining failures."
        break
    }

    if ($round -lt $MaxRounds) {
        Write-Host "[$((Get-Date).ToString('o'))] Sleeping $SleepMinutesBetweenRounds minute(s) before retry."
        Start-Sleep -Seconds ($SleepMinutesBetweenRounds * 60)
    }
}

$finished = [ordered]@{
    project_root = $ProjectRoot
    registry = $RegistryPath
    pid = $PID
    finished_at = (Get-Date).ToString("o")
    summary_path = $summaryPath
    status_path = $statusPath
}
$finished | ConvertTo-Json -Depth 6 | Set-Content -Path $metaPath -Encoding UTF8
