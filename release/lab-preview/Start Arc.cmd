@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0manage-arc-preview.ps1" -InstallRoot "%~dp0." -Action Start -OpenBrowser
if errorlevel 1 pause
