@echo off
title Foodshare Tracker - Launch Application
echo ===================================================
echo       Starting Foodshare Tracker System...
echo ===================================================
echo.

cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

echo Launching Streamlit web application via main.py...
echo.
python -m streamlit run main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Application terminated or failed to launch.
    pause
)
