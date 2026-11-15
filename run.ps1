# InsightFlow - Autonomous Multi-Agent AI System Launcher
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  InsightFlow - Multi-Agent AI Data Intelligence Platform   " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

if (-not (Test-Path ".\venv\Scripts\python.exe")) {
    Write-Host "[ERROR] Virtual environment not found in .\venv" -ForegroundColor Red
    Write-Host "Please create it: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

Write-Host "[1/2] Opening browser at http://localhost:8000 ..." -ForegroundColor Green
Start-Process "http://localhost:8000"

Write-Host "[2/2] Starting Uvicorn Server on http://localhost:8000 ..." -ForegroundColor Green
& ".\venv\Scripts\python.exe" -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload

