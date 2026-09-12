@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0manage-arc-preview.ps1" -InstallRoot "%~dp0." -Action Stop -Surface Office
if errorlevel 1 pause
