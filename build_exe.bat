@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title SubBind - BUILD

if not exist ".venv\Scripts\python.exe" (
    echo Eloszor futtasd a setup.bat fajlt.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -m pip install pyinstaller
if errorlevel 1 goto :err

".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --name "SubBind" --windowed --paths "src" "src\main.py"
if errorlevel 1 goto :err

echo.
echo BUILD KESZ.
echo Kimenet: dist\SubBind\SubBind.exe
echo Adatok futtataskor: a program melletti data\ mappa.
pause
exit /b 0

:err
echo.
echo BUILD HIBA.
pause
exit /b 1
