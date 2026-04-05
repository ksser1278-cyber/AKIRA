param(
    [string]$ProjectRoot = "C:\JPop_Songwriter\AKIRA ENGINE",
    [int]$BudgetMinutes = 55,
    [int]$BulkPageCount = 3,
    [int]$BulkPageSize = 25,
    [string]$BulkSort = "PublishDate",
    [int]$EstimatedBatchSeconds = 20
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-Python {
    $candidates = @(
        "python",
        "C:\Users\hangi\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\python.exe",
        "C:\Users\hangi\AppData\Local\Google\Cloud SDK\google-cloud-sdk\platform\bundledpython\python.exe"
    )

    foreach ($candidate in $candidates) {
        try {
            if ($candidate -eq "python") {
                $cmd = Get-Command python -ErrorAction Stop
                return $cmd.Source
            }

            if (Test-Path $candidate) {
                return $candidate
            }
        } catch {
            continue
        }
    }

    throw "No usable Python interpreter found. Checked: $($candidates -join ', ')"
}

function Get-LatestCycleState([string]$PlanningRoot) {
    $latest = Get-ChildItem $PlanningRoot -Filter "program_continuous_cycle_*.json" |
        Sort-Object LastWriteTime |
        Select-Object -Last 1

    if (-not $latest) {
        return @{
            NextOffset = 0
            NextTag = "{0}_x_01" -f (Get-Date -Format "yyyyMMdd")
        }
    }

    $payload = Get-Content $latest.FullName -Raw | ConvertFrom-Json
    $pageCount = [int]$payload.bulk_inputs.page_count
    $pageSize = [int]$payload.bulk_inputs.page_size
    $startOffset = [int]$payload.bulk_inputs.start_offset
    $nextOffset = $startOffset + ($pageCount * $pageSize)
    $batchTag = [string]$payload.batch_tag

    if ($batchTag -match "^(.*_)(\d+)$") {
        $prefix = $matches[1]
        $current = [int]$matches[2]
        $width = $matches[2].Length
        $nextTag = "{0}{1}" -f $prefix, ($current + 1).ToString(("D{0}" -f $width))
    } else {
        $nextTag = "{0}_x_01" -f (Get-Date -Format "yyyyMMdd")
    }

    return @{
        NextOffset = $nextOffset
        NextTag = $nextTag
    }
}

function Get-NextTag([string]$CurrentTag) {
    if ($CurrentTag -match "^(.*_)(\d+)$") {
        $prefix = $matches[1]
        $current = [int]$matches[2]
        $width = $matches[2].Length
        return "{0}{1}" -f $prefix, ($current + 1).ToString(("D{0}" -f $width))
    }

    return "{0}_x_01" -f (Get-Date -Format "yyyyMMdd")
}

$python = Resolve-Python
$planningRoot = Join-Path $ProjectRoot "reports\planning"
$startedAt = Get-Date
$budgetSeconds = $BudgetMinutes * 60
$state = Get-LatestCycleState -PlanningRoot $planningRoot
$currentOffset = [int]$state.NextOffset
$currentTag = [string]$state.NextTag
$completedTags = @()

Set-Location $ProjectRoot

while ($true) {
    $elapsedSeconds = [int]((Get-Date) - $startedAt).TotalSeconds
    $remainingSeconds = $budgetSeconds - $elapsedSeconds
    if ($remainingSeconds -le 0) {
        break
    }

    $runTier1 = $remainingSeconds -le ($EstimatedBatchSeconds * 2)
    $args = @(
        "akira.py",
        "dataset",
        "run-program-continuous-cycle",
        "--project-root", $ProjectRoot,
        "--batch-tag", $currentTag,
        "--bulk-page-count", $BulkPageCount,
        "--bulk-page-size", $BulkPageSize,
        "--bulk-start-offset", $currentOffset,
        "--bulk-sort", $BulkSort
    )

    if (-not $runTier1) {
        $args += "--skip-tier1-cycle"
    }

    & $python @args
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }

    $completedTags += $currentTag

    if ($runTier1) {
        break
    }

    $currentOffset += ($BulkPageCount * $BulkPageSize)
    $currentTag = Get-NextTag -CurrentTag $currentTag
}

$summary = [ordered]@{
    project_root = $ProjectRoot
    started_at = $startedAt.ToString("o")
    finished_at = (Get-Date).ToString("o")
    budget_minutes = $BudgetMinutes
    bulk_page_count = $BulkPageCount
    bulk_page_size = $BulkPageSize
    estimated_batch_seconds = $EstimatedBatchSeconds
    completed_batches = $completedTags.Count
    completed_tags = $completedTags
}

$summaryPath = Join-Path $planningRoot ("program_continuous_hourly_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".json")
$summary | ConvertTo-Json -Depth 6 | Set-Content -Path $summaryPath -Encoding UTF8
Write-Host "Program continuous hourly summary: $summaryPath"
Write-Host "Completed batches: $($completedTags.Count)"
