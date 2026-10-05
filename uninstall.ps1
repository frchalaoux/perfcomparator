param(
    [switch]$Yes
)

# Compatible avec Windows PowerShell 5.1 et PowerShell 7.
$ErrorActionPreference = "Stop"

if (Get-Command uv -ErrorAction SilentlyContinue) {
    $uvCommand = (Get-Command uv).Source
}
else {
    $uvPath = Join-Path $HOME ".local\bin\uv.exe"
    if (-not (Test-Path -LiteralPath $uvPath)) {
        throw "uv est introuvable ; aucune modification n'a été effectuée."
    }
    $uvCommand = $uvPath
}

$previousErrorActionPreference = $ErrorActionPreference
try {
    $ErrorActionPreference = "Continue"
    $toolList = @(& $uvCommand tool list 2>&1 | ForEach-Object { "$($_)" })
    $toolListExitCode = $LASTEXITCODE
    if ($toolListExitCode -ne 0) {
        throw "uv n'a pas pu inventorier les outils installés (code $toolListExitCode)."
    }
    $toolDirectory = ((& $uvCommand tool dir 2>&1 | ForEach-Object { "$($_)" }) -join "").Trim()
    $toolDirectoryExitCode = $LASTEXITCODE
    if ($toolDirectoryExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($toolDirectory)) {
        throw "uv n'a pas pu trouver le dossier des outils installés."
    }
    $toolBinDirectory = ((& $uvCommand tool dir --bin 2>&1 | ForEach-Object { "$($_)" }) -join "").Trim()
    $toolBinExitCode = $LASTEXITCODE
    if ($toolBinExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($toolBinDirectory)) {
        throw "uv n'a pas pu trouver le dossier des commandes installées."
    }
}
finally {
    $ErrorActionPreference = $previousErrorActionPreference
}

if (-not $Yes) {
    $answer = Read-Host "Désinstaller PerfComparator pour l'utilisateur $env:USERNAME ? (o/N)"
    if ($answer -notin @("o", "O", "oui", "Oui", "OUI", "y", "Y", "yes", "Yes", "YES")) {
        Write-Host "Désinstallation annulée."
        return
    }
}

if ($toolList | Where-Object { $_ -match '^perfcomparator v' }) {
    Write-Host "Désinstallation de PerfComparator..."
    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        & $uvCommand tool uninstall perfcomparator 2>&1 | ForEach-Object { Write-Host $_ }
        $uninstallExitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    if ($uninstallExitCode -ne 0) {
        throw "uv n'a pas pu désinstaller PerfComparator (code $uninstallExitCode)."
    }
}
else {
    Write-Host "PerfComparator n'est pas enregistré comme outil uv ; nettoyage du raccourci uniquement."
}

$perfComparatorCommand = Join-Path $toolBinDirectory "perfcomparator.exe"
$pythonwPath = Join-Path $toolDirectory "perfcomparator\Scripts\pythonw.exe"
$desktopPath = [Environment]::GetFolderPath("Desktop")
$programsPath = [Environment]::GetFolderPath("Programs")
$shortcutDirectories = @($desktopPath, $programsPath) |
    Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
    Select-Object -Unique
$wsh = $null
try {
    $wsh = New-Object -ComObject WScript.Shell
}
catch {
    Write-Warning "Windows Script Host indisponible ; les raccourcis éventuels sont conservés."
}

foreach ($directory in $shortcutDirectories) {
    $shortcutPath = Join-Path $directory "PerfComparator.lnk"
    if (-not (Test-Path -LiteralPath $shortcutPath -PathType Leaf)) {
        continue
    }
    if ($null -eq $wsh) {
        continue
    }
    try {
        $shortcut = $wsh.CreateShortcut($shortcutPath)
        $commandTargetMatches = [string]::Equals(
            $shortcut.TargetPath,
            $perfComparatorCommand,
            [StringComparison]::OrdinalIgnoreCase
        )
        $pythonwTargetMatches = [string]::Equals(
            $shortcut.TargetPath,
            $pythonwPath,
            [StringComparison]::OrdinalIgnoreCase
        )
        $isProductShortcut = (
            ($commandTargetMatches -and $shortcut.Arguments -eq "desktop") -or
            ($pythonwTargetMatches -and $shortcut.Arguments -eq "-m benchmark_mac.desktop_entry")
        )
        if ($isProductShortcut) {
            Remove-Item -LiteralPath $shortcutPath -Force
            Write-Host "Raccourci supprimé : $shortcutPath"
        }
    }
    catch {
        Write-Warning "Impossible de vérifier le raccourci ; il est conservé : $shortcutPath"
    }
}

Write-Host "PerfComparator est désinstallé."
Write-Host "uv, Python géré par uv, rapports et journaux ont été conservés."
