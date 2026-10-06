@echo off
setlocal
if exist "%~dp0release-version.txt" set /p PERFCOMPARATOR_VERSION=<"%~dp0release-version.txt"
where pwsh.exe >nul 2>&1
if not errorlevel 1 (
    echo Utilisation de PowerShell 7...
    pwsh.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
) else (
    echo PowerShell 7 absent ; utilisation de Windows PowerShell 5.1...
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
)
if errorlevel 1 (
    echo.
    echo L'installation a echoue. Copiez le message ci-dessus pour obtenir de l'aide.
    pause
    exit /b 1
)
echo.
echo Installation terminee.
echo Pour lancer l'interface : utilisez l'icone du Bureau ou perfcomparator desktop
echo Pour configurer une contribution GitHub : perfcomparator setup-contribution
pause
exit /b 0
