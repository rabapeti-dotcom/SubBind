@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Sorozat es film atnevezo - 0.6.1-TEST

if not exist ".venv\Scripts\python.exe" (
    echo A virtualis kornyezet nincs telepitve.
    echo Eloszor futtasd a setup.bat fajlt.
    pause
    exit /b 1
)

set "SERIESRENAMER_DEV=1"
".venv\Scripts\python.exe" "src\main.py"
set "ERR=%ERRORLEVEL%"

if not "%ERR%"=="0" (
    echo.
    echo A program hibaval allt le. Hibakod: %ERR%
    pause
)

exit /b %ERR%
