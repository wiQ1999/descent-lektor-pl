@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0skrypty\lektor.ps1" -Install
echo.
pause
