#!/usr/bin/env bash
# Mood - launcher for macOS / Linux
# Creates a local virtual environment on first run, installs
# dependencies, then starts the app. Fully portable: keep this
# script next to main.py and run ./start_mood.sh
set -e

cd "$(dirname "$0")"

# Pick a python
PY="python3"
if ! command -v "$PY" >/dev/null 2>&1; then
    PY="python"
fi
if ! command -v "$PY" >/dev/null 2>&1; then
    echo "Python 3.10+ wird benötigt. Bitte installieren."
    exit 1
fi

# Local venv keeps the app self-contained / portable
VENV=".venv"
if [ ! -d "$VENV" ]; then
    echo "Erstelle virtuelle Umgebung…"
    "$PY" -m venv "$VENV"
fi

# shellcheck disable=SC1091
source "$VENV/bin/activate"

# Install deps only if PySide6 is missing
if ! python -c "import PySide6" >/dev/null 2>&1; then
    echo "Installiere Abhängigkeiten…"
    python -m pip install --upgrade pip -q
    python -m pip install -r requirements.txt -q
fi

exec python main.py
