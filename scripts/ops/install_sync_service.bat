@echo off
echo ==============================================
echo Installing AKIRA GitHub Auto Sync Service
echo ==============================================

set SCRIPT_PATH=%~dp0github_auto_sync.py
set VBS_WRAPPER=%~dp0run_sync_silently.vbs

echo Set WshShell = CreateObject("WScript.Shell") > "%VBS_WRAPPER%"
echo WshShell.Run "python """ ^& "%SCRIPT_PATH%" ^& """", 0, False >> "%VBS_WRAPPER%"

echo Silently wrapper created at: %VBS_WRAPPER%

echo Registering Windows Task Scheduler...
schtasks /create /tn "AKIRA_GitHub_Auto_Sync" /tr "wscript.exe \"%VBS_WRAPPER%\"" /sc hourly /mo 1 /f

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ==============================================
    echo Installation Complete! 
    echo The sync script will now run in the background every 1 hour.
    echo Task Name: AKIRA_GitHub_Auto_Sync
    echo ==============================================
) else (
    echo.
    echo [ERROR] Failed to register task. Please ensure you run this script as Administrator.
)
pause
