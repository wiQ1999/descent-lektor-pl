@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0skrypty\lektor.ps1" -Uninstall
echo.
pause
