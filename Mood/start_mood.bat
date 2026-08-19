@echo off
title Mood
cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo Python fehlt. Bitte Python 3.10+ installieren.
    pause
    exit /b 1
)

pip show PySide6 >nul 2>&1
if errorlevel 1 (
    pip install PySide6 opencv-python-headless Pillow pillow-heif imageio imageio-ffmpeg send2trash cryptography -q
)
pip show cryptography >nul 2>&1
if errorlevel 1 (
    pip install cryptography -q
)

pythonw main.py 2>nul
if errorlevel 1 (
    python main.py
    if errorlevel 1 pause
)
