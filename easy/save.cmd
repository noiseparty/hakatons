@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0save.ps1" %*
echo.
pause
