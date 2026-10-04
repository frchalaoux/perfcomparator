$ErrorActionPreference = "Stop"

if ($PSVersionTable.PSVersion.Major -lt 5 -or
    ($PSVersionTable.PSVersion.Major -eq 5 -and $PSVersionTable.PSVersion.Minor -lt 1)) {
    throw "This test requires Windows PowerShell 5.1 or PowerShell 7."
}

$originalPath = $env:PATH
$originalTemp = $env:TEMP
$originalTmp = $env:TMP
$testRoot = Join-Path ([IO.Path]::GetTempPath()) "perfcomparator-installer-test-$([guid]::NewGuid())"
$fakeBin = Join-Path $testRoot "bin"
$fakeToolDirectory = Join-Path $testRoot "tools"
$fakeToolBin = Join-Path $testRoot "tool-bin"
$recoveryTemp = Join-Path $testRoot "recovery"
$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "PerfComparator.lnk"
$shortcutExisted = Test-Path -LiteralPath $shortcutPath

try {
    New-Item -ItemType Directory -Path $fakeBin, $fakeToolDirectory, $fakeToolBin, $recoveryTemp -Force | Out-Null
    $env:TEMP = $recoveryTemp
    $env:TMP = $recoveryTemp

    $malformedToolName = "perfcomparator-broken-ci"
    $malformedToolDirectory = Join-Path $fakeToolDirectory $malformedToolName
    New-Item -ItemType Directory -Path $malformedToolDirectory -Force | Out-Null
    Set-Content -LiteralPath (Join-Path $malformedToolDirectory "uv-receipt.toml") -Value "invalid =" -Encoding ASCII

    $fakePythonwDirectory = Join-Path $fakeToolDirectory "perfcomparator\Scripts"
    New-Item -ItemType Directory -Path $fakePythonwDirectory -Force | Out-Null
    Set-Content -LiteralPath (Join-Path $fakePythonwDirectory "pythonw.exe") -Value "fake" -Encoding ASCII
    Set-Content -LiteralPath (Join-Path $fakeToolBin "perfcomparator.exe") -Value "fake" -Encoding ASCII

    $env:FAKE_UV_TOOL_DIR = $fakeToolDirectory
    $env:FAKE_UV_BIN = $fakeToolBin
    $env:FAKE_UV_LOG = Join-Path $testRoot "uv.log"
    $env:FAKE_UV_LIST_MARKER = Join-Path $testRoot "uv-list-seen"
    $fakeUvScript = @'
@echo off
echo %*>>"%FAKE_UV_LOG%"
if "%~1"=="python" if "%~2"=="install" exit /b 0
if "%~1"=="tool" if "%~2"=="dir" (
  if "%~3"=="--bin" (echo %FAKE_UV_BIN%) else (echo %FAKE_UV_TOOL_DIR%)
  exit /b 0
)
if "%~1"=="tool" if "%~2"=="list" (
  if not exist "%FAKE_UV_LIST_MARKER%" (
    echo seen>"%FAKE_UV_LIST_MARKER%"
    echo warning: Ignoring malformed tool `perfcomparator-broken-ci` 1>&2
  ) else (
    echo No tools installed 1>&2
  )
  exit /b 0
)
if "%~1"=="tool" if "%~2"=="install" exit /b 0
exit /b 9
'@
    Set-Content -LiteralPath (Join-Path $fakeBin "uv.cmd") -Value $fakeUvScript -Encoding ASCII
    $env:PATH = "$fakeBin;$originalPath"

    if (-not (Test-Path -LiteralPath $desktopPath)) {
        New-Item -ItemType Directory -Path $desktopPath -Force | Out-Null
    }

    $repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
    $installerPath = Join-Path $repoRoot "install.ps1"
    if (-not (Test-Path -LiteralPath $installerPath)) {
        throw "Installer not found: $installerPath"
    }

    & $installerPath
    if ($LASTEXITCODE -ne 0) {
        throw "Installer returned exit code $LASTEXITCODE."
    }

    if (Test-Path -LiteralPath $malformedToolDirectory) {
        throw "Malformed uv tool directory was not moved out of uv's tools directory."
    }
    $recoveryCopies = @(Get-ChildItem -LiteralPath $recoveryTemp -Directory -Filter "PerfComparator-uv-recovery-$malformedToolName-*")
    if ($recoveryCopies.Count -ne 1) {
        throw "Expected one recoverable backup of the malformed uv tool; found $($recoveryCopies.Count)."
    }

    if (-not (Test-Path -LiteralPath $shortcutPath)) {
        throw "The desktop shortcut was not created."
    }
    $uvCalls = Get-Content -LiteralPath $env:FAKE_UV_LOG -Raw
    $toolListCallCount = @($uvCalls -split "`r?`n" | Where-Object { $_ -eq "tool list" }).Count
    if ($toolListCallCount -ne 2) {
        throw "Expected two uv tool-list calls, including the empty-list case; found $toolListCallCount."
    }
    if ($uvCalls -notmatch "tool install --managed-python --python 3\.14\.4 --force --reinstall") {
        throw "The installer did not request the expected uv tool installation."
    }
    if ($uvCalls -match "setup-contribution|desktop") {
        throw "The installer unexpectedly launched the application or contribution setup."
    }

    Write-Host "Installer smoke test passed under PowerShell $($PSVersionTable.PSVersion)."
}
finally {
    $env:PATH = $originalPath
    $env:TEMP = $originalTemp
    $env:TMP = $originalTmp
    Remove-Item Env:FAKE_UV_TOOL_DIR -ErrorAction SilentlyContinue
    Remove-Item Env:FAKE_UV_BIN -ErrorAction SilentlyContinue
    Remove-Item Env:FAKE_UV_LOG -ErrorAction SilentlyContinue
    Remove-Item Env:FAKE_UV_LIST_MARKER -ErrorAction SilentlyContinue
    if (-not $shortcutExisted -and (Test-Path -LiteralPath $shortcutPath)) {
        Remove-Item -LiteralPath $shortcutPath -Force
    }
    if (Test-Path -LiteralPath $testRoot) {
        Remove-Item -LiteralPath $testRoot -Recurse -Force
    }
}
