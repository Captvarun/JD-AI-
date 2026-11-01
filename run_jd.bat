@echo off
title JD - Personal AI Desktop Assistant
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    start "" ".venv\Scripts\pythonw.exe" main.py
) else (
    echo Error: Virtual environment not found. Please run pip install -r requirements.txt.
    pause
)
