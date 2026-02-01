# Beer Game Analysis Notebook Launcher (PowerShell)
# This script opens Jupyter Notebook using the local Python environment

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Beer Game - Analysis Notebook"           -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Starting Jupyter Notebook..." -ForegroundColor Green
Write-Host "Your browser will open automatically." -ForegroundColor Yellow
Write-Host ""
Write-Host "To stop the notebook server, press Ctrl+C in this window." -ForegroundColor Yellow
Write-Host ""

# Check if venv exists
if (-not (Test-Path "venv\Scripts\jupyter.exe")) {
    Write-Host "ERROR: Jupyter not found in virtual environment!" -ForegroundColor Red
    Write-Host "Please reinstall packages: venv\Scripts\pip install jupyter" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Start Jupyter Notebook
& "venv\Scripts\jupyter.exe" "notebook" "analysis\BeerGame_Analysis.ipynb"

Read-Host "Press Enter to exit"
