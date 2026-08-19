@echo off
title Mood
cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo Python fehlt. Bitte Python 3.10+ installieren.
    pause
    exit /b 1
)

REM Install everything from requirements.txt if PySide6 is missing
python -c "import PySide6" >nul 2>&1
if errorlevel 1 (
    echo Installiere Abhaengigkeiten...
    python -m pip install --upgrade pip -q
    python -m pip install -r requirements.txt -q
)

pythonw main.py 2>nul
if errorlevel 1 (
    python main.py
    if errorlevel 1 pause
)
