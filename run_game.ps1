# Beer Game Launcher (PowerShell)
# This script runs the game using the local Python environment

Write-Host "========================================"  -ForegroundColor Cyan
Write-Host "  Beer Game - Supply Chain Simulation"    -ForegroundColor Cyan
Write-Host "========================================"  -ForegroundColor Cyan
Write-Host ""

# Check if venv exists
if (-not (Test-Path "venv\Scripts\python.exe")) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run setup first or contact support." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Activate and run
& "venv\Scripts\python.exe" "main.py"

# Check for errors
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: The game encountered an error!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
}
