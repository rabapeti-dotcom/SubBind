@echo off
setlocal EnableExtensions
cd /d "%~dp0"

title Sorozat es film atnevezo - SETUP 0.6.1-TEST

echo ==========================================================
echo   Sorozat es film atnevezo - SETUP
echo   0.6.1-TEST
echo ==========================================================
echo.
echo Projekt: %CD%
echo.

if not exist "requirements.txt" (
    echo HIBA: requirements.txt nem talalhato.
    echo A setup.bat-ot a projekt gyokerebol kell futtatni.
    goto :fail
)

set "PY_CMD="

where py >nul 2>&1
if not errorlevel 1 set "PY_CMD=py -3"

if not defined PY_CMD (
    where python >nul 2>&1
    if not errorlevel 1 set "PY_CMD=python"
)

if not defined PY_CMD (
    echo HIBA: sem a Python Launcher [py], sem a python parancs nem talalhato.
    echo Telepits Python 3-at, majd inditsd ujra ezt a fajlt.
    goto :fail
)

echo Python:
%PY_CMD% --version
if errorlevel 1 (
    echo HIBA: a Python parancs nem futtathato.
    goto :fail
)
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Virtualis kornyezet letrehozasa...
    %PY_CMD% -m venv ".venv"
    if errorlevel 1 (
        echo HIBA: a virtualis kornyezet letrehozasa sikertelen.
        goto :fail
    )
) else (
    echo [1/3] A virtualis kornyezet mar letezik.
)
echo.

echo [2/3] Pip ellenorzese...
".venv\Scripts\python.exe" -m pip --version
if errorlevel 1 (
    echo HIBA: a pip nem mukodik a virtualis kornyezetben.
    goto :fail
)
echo.

echo [3/3] Fuggosegek telepitese...
".venv\Scripts\python.exe" -m pip install -r "requirements.txt"
if errorlevel 1 (
    echo.
    echo HIBA: a fuggosegek telepitese sikertelen.
    echo Ellenorizd az internetkapcsolatot es a requirements.txt fajlt.
    goto :fail
)
echo.

if not exist "TESTEK" mkdir "TESTEK"
if not exist "PATCH" mkdir "PATCH"
if not exist "patches" mkdir "patches"
if not exist "Tesztadat_Generator\TESZT_KORNYEZET" mkdir "Tesztadat_Generator\TESZT_KORNYEZET"
if not exist "backups" mkdir "backups"
if not exist "docs" mkdir "docs"

echo ==========================================================
echo   SETUP SIKERES
echo ==========================================================
echo.
echo Inditas: run_dev.bat
echo Tesztlabor: start_testlab.bat
echo Build: build_exe.bat
echo Patchok: patches\
echo.
pause
exit /b 0

:fail
echo.
echo ==========================================================
echo   SETUP SIKERTELEN
echo ==========================================================
echo.
echo A hiba fenti szovege alapjan javithato.
echo A projekt nem modositotta a forraskodot.
echo.
pause
exit /b 1
