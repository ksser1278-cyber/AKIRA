param(
    [string]$ProjectRoot = "C:\JPop_Songwriter\AKIRA ENGINE",
    [Parameter(Mandatory = $true)]
    [string]$BatchTag,
    [int]$BulkPageCount = 3,
    [int]$BulkPageSize = 25,
    [int]$BulkStartOffset = 0,
    [string]$BulkSort = "PublishDate",
    [switch]$SkipTier1Cycle
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

$python = Resolve-Python
Set-Location $ProjectRoot

$args = @(
    "akira.py",
    "dataset",
    "run-program-continuous-cycle",
    "--project-root", $ProjectRoot,
    "--batch-tag", $BatchTag,
    "--bulk-page-count", $BulkPageCount,
    "--bulk-page-size", $BulkPageSize,
    "--bulk-start-offset", $BulkStartOffset,
    "--bulk-sort", $BulkSort
)

if ($SkipTier1Cycle) {
    $args += "--skip-tier1-cycle"
}

& $python @args
exit $LASTEXITCODE
