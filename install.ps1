# Compatible avec Windows PowerShell 5.1 et PowerShell 7.
# Python n'a pas besoin d'être déjà installé : uv gère la version reproductible.
$ErrorActionPreference = "Stop"

$releaseVersion = if ($env:PERFCOMPARATOR_VERSION) {
    $env:PERFCOMPARATOR_VERSION
}
elseif ($env:BENCHMARK_MAC_VERSION) {
    $env:BENCHMARK_MAC_VERSION
}
else {
    "v0.5.0.dev0"
}
$pythonVersion = "3.14.4"
$sourceUrl = if ($env:PERFCOMPARATOR_SOURCE) {
    $env:PERFCOMPARATOR_SOURCE
}
elseif ($env:BENCHMARK_MAC_SOURCE) {
    $env:BENCHMARK_MAC_SOURCE
}
else {
    "https://github.com/frchalaoux/perfcomparator/archive/refs/tags/$releaseVersion.tar.gz"
}

if ($PSScriptRoot -and (Test-Path (Join-Path $PSScriptRoot "pyproject.toml"))) {
    $sourceUrl = $PSScriptRoot
}

function Install-CurrentUv {
    $installerPath = Join-Path ([IO.Path]::GetTempPath()) "uv-installer-$([guid]::NewGuid()).ps1"
    try {
        Invoke-WebRequest -UseBasicParsing https://astral.sh/uv/install.ps1 -OutFile $installerPath
        $powerShellExecutable = Join-Path $PSHOME "powershell.exe"
        if (-not (Test-Path $powerShellExecutable)) {
            $powerShellExecutable = Join-Path $PSHOME "pwsh.exe"
        }
        if (-not (Test-Path $powerShellExecutable)) {
            throw "Impossible de trouver l'exécutable PowerShell utilisé pour installer uv."
        }
        & $powerShellExecutable -NoProfile -ExecutionPolicy Bypass -File $installerPath
        if ($LASTEXITCODE -ne 0) {
            throw "L'installateur officiel de uv a échoué (code $LASTEXITCODE)."
        }
    }
    finally {
        Remove-Item -LiteralPath $installerPath -Force -ErrorAction SilentlyContinue
    }
}

function Get-UvToolList {
    param([switch]$AllowNonZeroExitCode)

    $previousErrorActionPreference = $ErrorActionPreference
    try {
        # Windows PowerShell 5.1 turns native stderr into a terminating error
        # when ErrorActionPreference is Stop. uv uses stderr for its benign
        # "No tools installed" message, so capture it explicitly and inspect
        # the native exit code ourselves.
        $ErrorActionPreference = "Continue"
        $output = @(& $uvCommand tool list 2>&1 | ForEach-Object { "$($_)" })
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }

    if ($exitCode -ne 0 -and -not $AllowNonZeroExitCode) {
        throw "uv n'a pas pu inventorier les outils installés (code $exitCode)."
    }

    @($output | Where-Object { $_ -notmatch "No tools installed" })
}

if (Get-Command uv -ErrorAction SilentlyContinue) {
    $uvCommand = "uv"
}
else {
    Write-Host "Installation de uv..."
    Install-CurrentUv
    $uvPath = Join-Path $HOME ".local\bin\uv.exe"
    if (-not (Test-Path $uvPath)) {
        throw "uv est introuvable apres son installation."
    }
    $uvCommand = $uvPath
}

Write-Host "Installation de CPython $pythonVersion gere par uv..."
& $uvCommand python install $pythonVersion
if ($LASTEXITCODE -ne 0) {
    Write-Host "La version actuelle de uv ne trouve pas CPython $pythonVersion."
    Write-Host "Mise a niveau de uv depuis l'installateur officiel, puis nouvelle tentative..."
    Install-CurrentUv
    $updatedUvPath = Join-Path $HOME ".local\bin\uv.exe"
    if (-not (Test-Path $updatedUvPath)) {
        throw "La version mise a niveau de uv est introuvable dans $updatedUvPath."
    }
    $uvCommand = $updatedUvPath
    & $uvCommand python install $pythonVersion
    if ($LASTEXITCODE -ne 0) {
        throw "L'installation de Python $pythonVersion a encore échoué après la mise à niveau de uv (code $LASTEXITCODE)."
    }
}

$toolDirectory = & $uvCommand tool dir
if ($LASTEXITCODE -ne 0) {
    throw "Impossible de trouver le dossier des outils uv (code $LASTEXITCODE)."
}

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
            Move-Item -LiteralPath $malformedToolDirectory -Destination $recoveryDirectory
        }
    }
}

$toolList = @(Get-UvToolList)
$legacyToolInstalled = $toolList -match "^benchmark-mac v"

if ($legacyToolInstalled) {
    Write-Host "Nettoyage de l'ancien enregistrement benchmark-mac..."
    & $uvCommand tool uninstall benchmark-mac
    if ($LASTEXITCODE -ne 0) {
        throw "Le nettoyage de l'ancien enregistrement benchmark-mac a échoué (code $LASTEXITCODE)."
    }
}
Write-Host "Installation de PerfComparator $releaseVersion..."
& $uvCommand tool install --managed-python --python $pythonVersion --force --reinstall $sourceUrl
if ($LASTEXITCODE -ne 0) {
    throw "L'installation de PerfComparator a échoué (code $LASTEXITCODE)."
}

$toolBinDirectory = & $uvCommand tool dir --bin
$perfComparatorCommand = Join-Path $toolBinDirectory "perfcomparator.exe"
if (-not (Test-Path -LiteralPath $perfComparatorCommand)) {
    throw "La commande PerfComparator attendue est introuvable : $perfComparatorCommand"
}
Write-Host "Commande PerfComparator installée : $perfComparatorCommand"

Write-Host ""
$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "PerfComparator.lnk"
$pythonwPath = Join-Path $toolDirectory "perfcomparator\Scripts\pythonw.exe"
$shortcutTarget = $perfComparatorCommand
$shortcutArguments = "desktop"
if (Test-Path $pythonwPath) {
    $shortcutTarget = $pythonwPath
    $shortcutArguments = "-m benchmark_mac.desktop_entry"
}

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $shortcutTarget
$shortcut.Arguments = $shortcutArguments
$shortcut.WorkingDirectory = $HOME
$shortcut.IconLocation = "$shortcutTarget,0"
$shortcut.Save()
Write-Host "Icône créée sur le Bureau : $shortcutPath"

Write-Host "PerfComparator $releaseVersion est installé."
Write-Host "Pour lancer l'interface : utilisez l'icône du Bureau ou perfcomparator desktop"
Write-Host "Pour configurer une contribution GitHub : perfcomparator setup-contribution"
