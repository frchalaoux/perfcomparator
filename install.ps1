# Compatible avec Windows PowerShell 5.1 et PowerShell 7.
# Python n'a pas besoin d'être déjà installé : uv gère la version reproductible.
$ErrorActionPreference = "Stop"

$logDirectory = if ($env:PERFCOMPARATOR_INSTALL_LOG_DIR) {
    $env:PERFCOMPARATOR_INSTALL_LOG_DIR
}
elseif ($env:LOCALAPPDATA) {
    Join-Path $env:LOCALAPPDATA "PerfComparator\logs"
}
else {
    Join-Path ([IO.Path]::GetTempPath()) "PerfComparator\logs"
}
New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
$logName = "install-{0}-{1}.log" -f (Get-Date -Format "yyyyMMdd-HHmmss"), ([guid]::NewGuid().ToString("N"))
$script:installLogPath = Join-Path $logDirectory $logName
$script:installLogWriter = [System.IO.StreamWriter]::new(
    $script:installLogPath,
    $false,
    [System.Text.UTF8Encoding]::new($false)
)
$script:installLogWriter.AutoFlush = $true

function Write-InstallLog {
    param(
        [Parameter(Mandatory = $true)][string]$Level,
        [Parameter(Mandatory = $true)][string]$Message
    )

    $line = "{0} [{1}] {2}" -f (Get-Date -Format "yyyy-MM-ddTHH:mm:ss.fffK"), $Level, $Message
    $script:installLogWriter.WriteLine($line)
    $script:installLogWriter.Flush()
    ([System.IO.FileStream]$script:installLogWriter.BaseStream).Flush($true)
}

function Invoke-LoggedNativeCommand {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [string[]]$ArgumentList = @(),
        [switch]$PassOutput
    )

    $displayArguments = ($ArgumentList | ForEach-Object {
        if ($_ -match '[\s"]') { '"' + ($_ -replace '"', '\\"') + '"' } else { $_ }
    }) -join " "
    Write-InstallLog "COMMAND" ("Starting: {0} {1}" -f $FilePath, $displayArguments)
    $previousErrorActionPreference = $ErrorActionPreference
    $capturedOutput = @()
    try {
        # Windows PowerShell 5.1 treats native stderr as PowerShell errors when
        # ErrorActionPreference is Stop. Merge streams and record each line.
        $ErrorActionPreference = "Continue"
        $capturedOutput = @(& $FilePath @ArgumentList 2>&1 | ForEach-Object {
            $line = "$($_)"
            Write-InstallLog "OUTPUT" $line
            if ($PassOutput) { Write-Host $line }
            $line
        })
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }

    Write-InstallLog "EXIT" ("Exit code: {0} ({1})" -f $exitCode, $FilePath)
    [pscustomobject]@{ Output = [string[]]$capturedOutput; ExitCode = $exitCode }
}

trap {
    try { Write-InstallLog "FATAL" $_.ToString() } catch { }
    try { $script:installLogWriter.Dispose() } catch { }
    throw
}

Write-InstallLog "INFO" ("Installer started. PowerShell={0}; OS={1}; User={2}" -f $PSVersionTable.PSVersion, [Environment]::OSVersion.VersionString, $env:USERNAME)
Write-Host "Journal d'installation : $script:installLogPath"

$releaseVersion = if ($env:PERFCOMPARATOR_VERSION) {
    $env:PERFCOMPARATOR_VERSION
}
elseif ($env:BENCHMARK_MAC_VERSION) {
    $env:BENCHMARK_MAC_VERSION
}
else {
    "v0.5.0"
}
$pythonVersion = "3.14.4"
$sourceUrl = if ($env:PERFCOMPARATOR_SOURCE) {
    $env:PERFCOMPARATOR_SOURCE
}
elseif ($env:BENCHMARK_MAC_SOURCE) {
    $env:BENCHMARK_MAC_SOURCE
}
elseif ($PSScriptRoot -and (Test-Path -LiteralPath (Join-Path $PSScriptRoot "source-url.txt"))) {
    (Get-Content -LiteralPath (Join-Path $PSScriptRoot "source-url.txt") -Raw).Trim()
}
else {
    "https://github.com/frchalaoux/perfcomparator/archive/refs/tags/$releaseVersion.tar.gz"
}
$webSourceUrl = if ($env:PERFCOMPARATOR_WEB_SOURCE) {
    $env:PERFCOMPARATOR_WEB_SOURCE
}
elseif ($PSScriptRoot -and (Test-Path -LiteralPath (Join-Path $PSScriptRoot "web-source-url.txt"))) {
    (Get-Content -LiteralPath (Join-Path $PSScriptRoot "web-source-url.txt") -Raw).Trim()
}
else {
    "https://github.com/frchalaoux/perfcomparator-web/archive/5bc8079682135b154872096bbee2aff506b49554.tar.gz"
}
$webSourceVersion = if ($env:PERFCOMPARATOR_WEB_VERSION) {
    $env:PERFCOMPARATOR_WEB_VERSION
}
elseif ($PSScriptRoot -and (Test-Path -LiteralPath (Join-Path $PSScriptRoot "web-source-version.txt"))) {
    (Get-Content -LiteralPath (Join-Path $PSScriptRoot "web-source-version.txt") -Raw).Trim()
}
else {
    "0.1.0"
}

if ($PSScriptRoot -and (Test-Path (Join-Path $PSScriptRoot "pyproject.toml"))) {
    $sourceUrl = $PSScriptRoot
}
Write-InstallLog "INFO" ("Requested version={0}; Python={1}; source={2}; UV_TOOL_DIR={3}; UV_TOOL_BIN_DIR={4}" -f $releaseVersion, $pythonVersion, $sourceUrl, $env:UV_TOOL_DIR, $env:UV_TOOL_BIN_DIR)

function Install-CurrentUv {
    $installerPath = Join-Path ([IO.Path]::GetTempPath()) "uv-installer-$([guid]::NewGuid()).ps1"
    try {
        Write-InstallLog "STEP" "Downloading the official uv installer."
        Invoke-WebRequest -UseBasicParsing https://astral.sh/uv/install.ps1 -OutFile $installerPath
        Write-InstallLog "INFO" ("Downloaded uv installer to {0}" -f $installerPath)
        $powerShellExecutable = Join-Path $PSHOME "powershell.exe"
        if (-not (Test-Path $powerShellExecutable)) {
            $powerShellExecutable = Join-Path $PSHOME "pwsh.exe"
        }
        if (-not (Test-Path $powerShellExecutable)) {
            throw "Impossible de trouver l'exécutable PowerShell utilisé pour installer uv."
        }
        $result = Invoke-LoggedNativeCommand -FilePath $powerShellExecutable -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $installerPath) -PassOutput
        if ($result.ExitCode -ne 0) {
            throw "L'installateur officiel de uv a échoué (code $($result.ExitCode))."
        }
    }
    finally {
        Remove-Item -LiteralPath $installerPath -Force -ErrorAction SilentlyContinue
    }
}

function Get-UvToolList {
    param([switch]$AllowNonZeroExitCode)

    # Keep uv's output in the log, including its benign empty-list warning.
    $result = Invoke-LoggedNativeCommand -FilePath $uvCommand -ArgumentList @("tool", "list")
    $output = $result.Output
    $exitCode = $result.ExitCode

    if ($exitCode -ne 0 -and -not $AllowNonZeroExitCode) {
        throw "uv n'a pas pu inventorier les outils installés (code $exitCode)."
    }

    @($output | Where-Object { $_ -notmatch "No tools installed" })
}

if (Get-Command uv -ErrorAction SilentlyContinue) {
    $uvCommand = "uv"
    Write-InstallLog "INFO" ("Found uv on PATH: {0}" -f (Get-Command uv).Source)
}
else {
    Write-InstallLog "STEP" "uv was not found on PATH; installing it."
    Write-Host "Installation de uv..."
    Install-CurrentUv
    $uvPath = Join-Path $HOME ".local\bin\uv.exe"
    if (-not (Test-Path $uvPath)) {
        throw "uv est introuvable apres son installation."
    }
    $uvCommand = $uvPath
}

Write-Host "Installation de CPython $pythonVersion gere par uv..."
$result = Invoke-LoggedNativeCommand -FilePath $uvCommand -ArgumentList @("python", "install", $pythonVersion) -PassOutput
if ($result.ExitCode -ne 0) {
    Write-Host "La version actuelle de uv ne trouve pas CPython $pythonVersion."
    Write-Host "Mise a niveau de uv depuis l'installateur officiel, puis nouvelle tentative..."
    Install-CurrentUv
    $updatedUvPath = Join-Path $HOME ".local\bin\uv.exe"
    if (-not (Test-Path $updatedUvPath)) {
        throw "La version mise a niveau de uv est introuvable dans $updatedUvPath."
    }
    $uvCommand = $updatedUvPath
    $result = Invoke-LoggedNativeCommand -FilePath $uvCommand -ArgumentList @("python", "install", $pythonVersion) -PassOutput
    if ($result.ExitCode -ne 0) {
        throw "L'installation de Python $pythonVersion a encore échoué après la mise à niveau de uv (code $($result.ExitCode))."
    }
}

$result = Invoke-LoggedNativeCommand -FilePath $uvCommand -ArgumentList @("tool", "dir")
if ($result.ExitCode -ne 0) {
    throw "Impossible de trouver le dossier des outils uv (code $($result.ExitCode))."
}
$toolDirectory = ($result.Output -join "").Trim()
Write-InstallLog "INFO" ("uv tool directory: {0}" -f $toolDirectory)

# uv ne peut pas désinstaller un outil dont le reçu TOML est corrompu. Capture
# son avertissement puis met de côté uniquement les environnements concernés.
$toolListOutput = @(Get-UvToolList -AllowNonZeroExitCode)

$malformedTools = foreach ($line in $toolListOutput) {
    if ($line -match "Ignoring malformed tool [``'‘](.+?)[``'’]") {
        $Matches[1]
    }
}
foreach ($toolName in $malformedTools) {
    if ($toolName -match '^(perfcomparator|benchmark-mac)([-_.].*)?$') {
        $malformedToolDirectory = Join-Path $toolDirectory $toolName
        if (Test-Path -LiteralPath $malformedToolDirectory) {
            $recoveryDirectory = Join-Path ([IO.Path]::GetTempPath()) (
                "PerfComparator-uv-recovery-$toolName-$([guid]::NewGuid())"
            )
            Write-Warning "Reçu uv invalide détecté ; environnement déplacé vers $recoveryDirectory"
            Write-InstallLog "STEP" ("Moving malformed uv tool {0} to {1}" -f $malformedToolDirectory, $recoveryDirectory)
            Move-Item -LiteralPath $malformedToolDirectory -Destination $recoveryDirectory
            Write-InstallLog "INFO" "Malformed uv tool moved successfully."
        }
    }
}

$toolList = @(Get-UvToolList)
$legacyToolInstalled = $toolList -match "^benchmark-mac v"

if ($legacyToolInstalled) {
    Write-Host "Nettoyage de l'ancien enregistrement benchmark-mac..."
    $result = Invoke-LoggedNativeCommand -FilePath $uvCommand -ArgumentList @("tool", "uninstall", "benchmark-mac") -PassOutput
    if ($result.ExitCode -ne 0) {
        throw "Le nettoyage de l'ancien enregistrement benchmark-mac a échoué (code $($result.ExitCode))."
    }
}
Write-Host "Installation de PerfComparator $releaseVersion..."
$installArguments = @("tool", "install", "--managed-python", "--python", $pythonVersion)
if ($webSourceUrl) {
    $installArguments += @("--with-executables-from", "perfcomparatorweb @ $webSourceUrl")
}
$installArguments += @("--force", "--reinstall", $sourceUrl)
$result = Invoke-LoggedNativeCommand -FilePath $uvCommand -ArgumentList $installArguments -PassOutput
if ($result.ExitCode -ne 0) {
    throw "L'installation de PerfComparator a échoué (code $($result.ExitCode))."
}
if ($webSourceVersion) {
    Write-Host "Version PCWEB installée : $webSourceVersion"
}

$result = Invoke-LoggedNativeCommand -FilePath $uvCommand -ArgumentList @("tool", "dir", "--bin")
if ($result.ExitCode -ne 0) {
    throw "Impossible de trouver le dossier des commandes uv (code $($result.ExitCode))."
}
$toolBinDirectory = ($result.Output -join "").Trim()
$perfComparatorCommand = Join-Path $toolBinDirectory "perfcomparator.exe"
if (-not (Test-Path -LiteralPath $perfComparatorCommand)) {
    throw "La commande PerfComparator attendue est introuvable : $perfComparatorCommand"
}
Write-InstallLog "INFO" ("Installed executable verified: {0}" -f $perfComparatorCommand)
Write-Host "Commande PerfComparator installée : $perfComparatorCommand"

Write-Host ""
$shortcutCreated = $false
try {
    $desktopPath = [Environment]::GetFolderPath("Desktop")
    $shortcutDirectory = $desktopPath
    if ([string]::IsNullOrWhiteSpace($desktopPath)) {
        throw "Le dossier Bureau n'est pas disponible dans cette session."
    }
    if ($desktopPath -match '^\\\\') {
        # Parallels may redirect the Windows Desktop to a macOS shared folder
        # (for example, \\Mac\Home\Desktop). Saving a .lnk there can destabilize
        # the VM, so put the shortcut in the user's local Windows Start Menu.
        $programsPath = [Environment]::GetFolderPath("Programs")
        if ([string]::IsNullOrWhiteSpace($programsPath) -or $programsPath -match '^\\\\') {
            throw "Le Bureau Windows est un chemin réseau et le menu Démarrer local est introuvable."
        }
        $shortcutDirectory = $programsPath
        if (-not (Test-Path -LiteralPath $shortcutDirectory -PathType Container)) {
            New-Item -ItemType Directory -Path $shortcutDirectory -Force | Out-Null
        }
        Write-Warning "Bureau Windows partagé détecté ; le raccourci sera placé dans le menu Démarrer local."
        Write-InstallLog "INFO" ("Desktop is a UNC path ({0}); using local Start Menu: {1}" -f $desktopPath, $programsPath)
    }
    $shortcutPath = Join-Path $shortcutDirectory "PerfComparator.lnk"
    $pythonwPath = Join-Path $toolDirectory "perfcomparator\Scripts\pythonw.exe"
    $shortcutTarget = $perfComparatorCommand
    $shortcutArguments = "desktop"
    if (Test-Path $pythonwPath) {
        $shortcutTarget = $pythonwPath
        $shortcutArguments = "-m perfcomparator.desktop_entry"
    }

    Write-InstallLog "STEP" ("Creating shortcut at {0}; target={1}; arguments={2}" -f $shortcutPath, $shortcutTarget, $shortcutArguments)
    $shell = New-Object -ComObject WScript.Shell
    Write-InstallLog "INFO" "Windows Script Host shortcut object created."
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $shortcutTarget
    $shortcut.Arguments = $shortcutArguments
    $shortcut.WorkingDirectory = $HOME
    $shortcut.IconLocation = "$shortcutTarget,0"
    Write-InstallLog "STEP" "Saving desktop shortcut."
    $shortcut.Save()
    Write-InstallLog "INFO" "Desktop shortcut saved successfully."
    Write-Host "Raccourci créé : $shortcutPath"
    $shortcutCreated = $true
}
catch {
    Write-Warning "L'installation CLI a réussi, mais le raccourci graphique n'a pas pu être créé : $($_.Exception.Message)"
    Write-InstallLog "WARNING" ("Graphical shortcut not created; CLI remains available. {0}" -f $_.Exception.Message)
}

Write-Host "PerfComparator $releaseVersion est installé."
if ($shortcutCreated) {
    Write-Host "Pour lancer l'interface Web : utilisez le raccourci créé ou perfcomparator web"
}
else {
    Write-Host "La ligne de commande reste disponible : perfcomparator --version"
}
Write-Host "Pour configurer une contribution GitHub : perfcomparator setup-contribution"
Write-InstallLog "INFO" "Installer completed successfully."
$script:installLogWriter.Dispose()
