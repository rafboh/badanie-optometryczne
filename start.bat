@echo off
chcp 65001 >nul
title Badanie Optometryczne
echo.
echo  Aplikacja Badania Optometrycznego
echo  ==================================

REM Wykryj dost�pn� komend� Pythona
set PY=
python --version >nul 2>&1
if %errorlevel% == 0 (
    set PY=python
) else (
    py --version >nul 2>&1
    if %errorlevel% == 0 (
        set PY=py
    )
)

if "%PY%"=="" (
    echo  BLAD: Python nie zostal znaleziony.
    echo  Zainstaluj Python ze strony https://www.python.org/
    pause
    exit /b 1
)

echo  Wykryto: %PY%
%PY% -m pip install flask -q 2>nul
echo  Uruchamianie serwera...
start "" "http://localhost:5000"
%PY% app.py
pause
