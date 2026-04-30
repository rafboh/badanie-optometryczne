@echo off
chcp 65001 >nul
title Badanie Optometryczne
echo.
echo  Aplikacja Badania Optometrycznego
echo  ==================================
python -m pip install flask -q 2>nul
echo  Uruchamianie serwera...
start "" "chrome" "http://localhost:5000"
python app.py
pause
