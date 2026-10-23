@echo off
title Foodshare Tracker - Automated Test Suite
echo ===================================================
echo       Running Foodshare Tracker Test Suite
echo ===================================================
echo.

cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

echo Executing unit test suite (pytest)...
echo.
python -m pytest -v tests/test_food_bank.py

echo.
echo ===================================================
if errorlevel 1 (
    echo [RESULT] Some tests failed. Please review the output above.
) else (
    echo [RESULT] All tests completed and passed successfully!
)
echo ===================================================
echo.
pause
