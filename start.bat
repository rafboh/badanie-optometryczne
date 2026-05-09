@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title Badanie Optometryczne
echo.
echo  Aplikacja Badania Optometrycznego
echo  ==================================

REM Wykryj Pythona pomijajac stub Microsoft Store
set PY=
for /f "tokens=*" %%i in ('where python 2^>nul ^| findstr /v /i "WindowsApps"') do (
    if "!PY!"=="" set PY=%%i
)
if "!PY!"=="" (
    for /f "tokens=*" %%i in ('where py 2^>nul ^| findstr /v /i "WindowsApps"') do (
        if "!PY!"=="" set PY=%%i
    )
)

if "!PY!"=="" (
    echo  BLAD: Python nie zostal znaleziony.
    echo  Zainstaluj Python ze strony https://www.python.org/
    pause
    exit /b 1
)

echo  Wykryto: !PY!
"!PY!" -m pip install flask -q 2>nul
echo  Uruchamianie serwera...
start "" "http://localhost:5000"
"!PY!" app.py
pause
