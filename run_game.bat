@echo off
REM Beer Game Launcher
REM This script runs the game using the local Python environment

echo ========================================
echo   Beer Game - Supply Chain Simulation
echo ========================================
echo.

REM Activate the virtual environment
call venv\Scripts\activate.bat

REM Run the game
python main.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo ERROR: The game encountered an error!
    pause
)
