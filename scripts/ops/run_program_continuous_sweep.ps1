param(
    [string]$ProjectRoot = "C:\JPop_Songwriter\AKIRA ENGINE",
    [Parameter(Mandatory = $true)]
    [string]$BatchTagPrefix,
    [int]$BatchCount = 1,
    [int]$BulkPageCount = 3,
    [int]$BulkPageSize = 25,
    [int]$BulkStartOffset = 0,
    [int]$BulkOffsetStep = 75,
    [string]$BulkSort = "PublishDate",
    [switch]$RunTier1EveryBatch
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
    "run-program-continuous-sweep",
    "--project-root", $ProjectRoot,
    "--batch-tag-prefix", $BatchTagPrefix,
    "--batch-count", $BatchCount,
    "--bulk-page-count", $BulkPageCount,
    "--bulk-page-size", $BulkPageSize,
    "--bulk-start-offset", $BulkStartOffset,
    "--bulk-offset-step", $BulkOffsetStep,
    "--bulk-sort", $BulkSort
)

if ($RunTier1EveryBatch) {
    $args += "--run-tier1-every-batch"
}

& $python @args
exit $LASTEXITCODE
