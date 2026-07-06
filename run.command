#!/bin/bash
# Double-click this file in Finder to launch the Chip Bonding Visualization app.
# On first run it creates the virtual environment and installs dependencies.

cd "$(dirname "$0")" || exit 1

if [ ! -x ".venv/bin/python" ]; then
    echo "First run: setting up the virtual environment..."
    python3 -m venv .venv || { echo "Failed to create venv. Is python3 installed?"; exit 1; }
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt || { echo "Failed to install dependencies."; exit 1; }
fi

exec .venv/bin/python main.py
