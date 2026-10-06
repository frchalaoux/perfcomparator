$ErrorActionPreference = "Stop"

if ($PSVersionTable.PSVersion.Major -lt 5 -or
    ($PSVersionTable.PSVersion.Major -eq 5 -and $PSVersionTable.PSVersion.Minor -lt 1)) {
    throw "This test requires Windows PowerShell 5.1 or PowerShell 7."
}

$originalPath = $env:PATH
$testRoot = Join-Path ([IO.Path]::GetTempPath()) "perfcomparator-uninstaller-test-$([guid]::NewGuid())"
$fakeBin = Join-Path $testRoot "bin"
$fakeToolDirectory = Join-Path $testRoot "tools"
$fakeToolBin = Join-Path $testRoot "tool-bin"
$desktopPath = [Environment]::GetFolderPath("Desktop")
$programsPath = [Environment]::GetFolderPath("Programs")
$shortcutPaths = @(
    (Join-Path $desktopPath "PerfComparator.lnk"),
    (Join-Path $programsPath "PerfComparator.lnk")
) | Select-Object -Unique

try {
    foreach ($shortcutPath in $shortcutPaths) {
        if (Test-Path -LiteralPath $shortcutPath) {
            throw "Refusing to overwrite a pre-existing shortcut: $shortcutPath"
        }
    }
    New-Item -ItemType Directory -Path $fakeBin, $fakeToolDirectory, $fakeToolBin -Force | Out-Null
    $env:FAKE_UV_LOG = Join-Path $testRoot "uv.log"
    $env:FAKE_UV_TOOL_DIR = $fakeToolDirectory
    $env:FAKE_UV_TOOL_BIN = $fakeToolBin

    $pythonwDirectory = Join-Path $fakeToolDirectory "perfcomparator\Scripts"
    New-Item -ItemType Directory -Path $pythonwDirectory -Force | Out-Null
    $pythonwPath = Join-Path $pythonwDirectory "pythonw.exe"
    $perfComparatorPath = Join-Path $fakeToolBin "perfcomparator.exe"
    Set-Content -LiteralPath $pythonwPath -Value "fake" -Encoding ASCII
    Set-Content -LiteralPath $perfComparatorPath -Value "fake" -Encoding ASCII

    $fakeUvScript = @'
@echo off
echo %*>>"%FAKE_UV_LOG%"
if "%~1"=="tool" if "%~2"=="list" (
  echo perfcomparator v0.5.0
  exit /b 0
)
if "%~1"=="tool" if "%~2"=="dir" (
  if "%~3"=="--bin" (echo %FAKE_UV_TOOL_BIN%) else (echo %FAKE_UV_TOOL_DIR%)
  exit /b 0
)
if "%~1"=="tool" if "%~2"=="uninstall" exit /b 0
exit /b 2
'@
    Set-Content -LiteralPath (Join-Path $fakeBin "uv.cmd") -Value $fakeUvScript -Encoding ASCII
    $env:PATH = "$fakeBin;$originalPath"

    $wsh = New-Object -ComObject WScript.Shell
    $shortcutPath = Join-Path $desktopPath "PerfComparator.lnk"
    $shortcut = $wsh.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $pythonwPath
    $shortcut.Arguments = "-m benchmark_mac.desktop_entry"
    $shortcut.Save()

    $repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
    $uninstallerPath = Join-Path $repoRoot "uninstall.ps1"
    & $uninstallerPath -Yes
    if ($LASTEXITCODE -ne 0) {
        throw "Uninstaller returned exit code $LASTEXITCODE."
    }

    if (Test-Path -LiteralPath $shortcutPath) {
        throw "The PerfComparator shortcut was not removed."
    }
    $uvCalls = Get-Content -LiteralPath $env:FAKE_UV_LOG -Raw
    if ($uvCalls -notmatch "tool uninstall perfcomparator") {
        throw "The uninstaller did not request removal of the PerfComparator uv tool."
    }
    Write-Host "Uninstaller smoke test passed under PowerShell $($PSVersionTable.PSVersion)."
}
finally {
    $env:PATH = $originalPath
    Remove-Item Env:FAKE_UV_LOG -ErrorAction SilentlyContinue
    Remove-Item Env:FAKE_UV_TOOL_DIR -ErrorAction SilentlyContinue
    Remove-Item Env:FAKE_UV_TOOL_BIN -ErrorAction SilentlyContinue
    foreach ($shortcutPath in $shortcutPaths) {
        if (Test-Path -LiteralPath $shortcutPath) {
            Remove-Item -LiteralPath $shortcutPath -Force
        }
    }
    if (Test-Path -LiteralPath $testRoot) {
        Remove-Item -LiteralPath $testRoot -Recurse -Force
    }
}
