param(
    [Parameter(Mandatory = $true)][string]$InstallerDirectory
)

$ErrorActionPreference = "Stop"
$testRoot = Join-Path ([IO.Path]::GetTempPath()) "perfcomparator-pair-smoke-$([guid]::NewGuid())"
$env:UV_TOOL_DIR = Join-Path $testRoot "uv-tools"
$env:UV_TOOL_BIN_DIR = Join-Path $testRoot "uv-bin"
$env:PERFCOMPARATOR_STATE_DIR = Join-Path $testRoot "state"
$env:PERFCOMPARATOR_INSTALL_LOG_DIR = Join-Path $testRoot "logs"
New-Item -ItemType Directory -Path $env:PERFCOMPARATOR_STATE_DIR -Force | Out-Null
New-Item -ItemType Directory -Path $env:PERFCOMPARATOR_INSTALL_LOG_DIR -Force | Out-Null

function Invoke-Tool {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [switch]$ExpectFailure
    )

    $previousPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        $output = @(& $Path @Arguments 2>&1 | ForEach-Object { "$($_)" })
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousPreference
    }
    if ($ExpectFailure) {
        if ($exitCode -eq 0) { throw "$Path $($Arguments -join ' ') unexpectedly succeeded." }
    }
    elseif ($exitCode -ne 0) {
        throw "$Path $($Arguments -join ' ') failed ($exitCode): $($output -join "`n")"
    }
    $output
}

$installerPath = Join-Path $InstallerDirectory "install.ps1"
try {
    & $installerPath
    if ($LASTEXITCODE -ne 0) { throw "The packaged installer failed: $LASTEXITCODE" }
}
catch {
    Write-Host "The packaged installer failed. Installation log follows:"
    Get-ChildItem -LiteralPath $env:PERFCOMPARATOR_INSTALL_LOG_DIR -Filter "install-*.log" -File |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1 |
        ForEach-Object { Get-Content -LiteralPath $_.FullName }
    throw
}
$pce = Join-Path $env:UV_TOOL_BIN_DIR "perfcomparator.exe"
$pcweb = Join-Path $env:UV_TOOL_BIN_DIR "perfcomparatorweb.exe"

Invoke-Tool $pce @("web", "start", "--no-open-browser") | Write-Host
$webState = Get-Content -LiteralPath (Join-Path $env:PERFCOMPARATOR_STATE_DIR "web.json") -Raw |
    ConvertFrom-Json
$page = Invoke-WebRequest -Uri "$($webState.url)/" -UseBasicParsing -TimeoutSec 10
if ($page.StatusCode -ne 200 -or $page.Content -notmatch "Moteur PCE") {
    throw "The packaged PCWEB page did not show the PCE status."
}
Invoke-Tool $pce @("engine", "stop") -ExpectFailure | Out-Null
Invoke-Tool $pce @("web", "stop") | Write-Host

Invoke-Tool $pce @("engine", "start") | Write-Host
Invoke-Tool $pcweb @("start", "--no-open-browser") | Write-Host
Invoke-Tool $pcweb @("status") | Write-Host
Invoke-Tool $pce @("engine", "stop") -ExpectFailure | Out-Null
Invoke-Tool $pcweb @("stop") | Write-Host
Invoke-Tool $pce @("engine", "stop") | Write-Host

Write-Host "Installed PCE/PCWEB lifecycle smoke test passed."
