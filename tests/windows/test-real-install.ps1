$ErrorActionPreference = "Stop"

$uvExecutable = (Get-Command uv -ErrorAction Stop).Source
if (-not $uvExecutable) {
    throw "Could not resolve uv's executable path."
}

$toolDirectory = (& $uvExecutable tool dir | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or -not $toolDirectory) {
    throw "Could not locate uv's tool directory."
}

$toolEnvironment = Join-Path $toolDirectory "perfcomparator"
$pythonPath = Join-Path $toolEnvironment "Scripts\python.exe"
$configPath = Join-Path $toolEnvironment "pyvenv.cfg"
if (-not (Test-Path -LiteralPath $pythonPath -PathType Leaf)) {
    throw "The installed Python interpreter is missing: $pythonPath"
}
if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) {
    throw "The Python virtual-environment configuration is missing: $configPath"
}

$configContent = [IO.File]::ReadAllText($configPath)
if ($configContent -notmatch "(?m)^home\s*=\s*\S") {
    throw "The Python virtual-environment configuration has no valid home entry: $configPath"
}

Write-Host "Checking Tkinter in $pythonPath..."
& $pythonPath -c "import sys, tkinter; print('Python', sys.version.split()[0], '| Tk', tkinter.TkVersion)"
if ($LASTEXITCODE -ne 0) {
    throw "Tkinter could not be imported by the installed Python (code $LASTEXITCODE)."
}

$toolBinDirectory = (& $uvExecutable tool dir --bin | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or -not $toolBinDirectory) {
    throw "Could not locate uv's tool executable directory."
}
$perfComparatorCommand = Join-Path $toolBinDirectory "perfcomparator.exe"
if (-not (Test-Path -LiteralPath $perfComparatorCommand -PathType Leaf)) {
    throw "The PerfComparator command is missing: $perfComparatorCommand"
}

Write-Host "Checking the installed command without launching the GUI..."
$versionOutput = @(& $perfComparatorCommand --version 2>&1 | ForEach-Object { "$($_)" })
$versionExitCode = $LASTEXITCODE
if ($versionExitCode -ne 0) {
    throw "perfcomparator --version failed (code $versionExitCode): $($versionOutput -join ' ')"
}
if (($versionOutput -join "`n") -notmatch "0\.5\.0\.dev0") {
    throw "Unexpected installed version: $($versionOutput -join ' ')"
}

Write-Host "Real Windows installer smoke test passed. Tkinter imports; GUI was not launched."
