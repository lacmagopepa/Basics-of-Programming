@echo off
REM Beer Game Analysis Notebook Launcher
REM This script opens Jupyter Notebook using the local Python environment

echo ==========================================
echo   Beer Game - Analysis Notebook
echo ==========================================
echo.
echo Starting Jupyter Notebook...
echo Your browser will open automatically.
echo.
echo To stop the notebook server, press Ctrl+C in this window.
echo.

REM Activate the virtual environment
call venv\Scripts\activate.bat

REM Start Jupyter Notebook and open the analysis notebook
jupyter notebook analysis\BeerGame_Analysis.ipynb

pause
