@echo off
title InsightFlow - Autonomous Multi-Agent AI System
echo ============================================================
echo   InsightFlow - Multi-Agent AI Data Intelligence Platform
echo ============================================================
echo.

cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found in .\venv.
    echo Please create it first: python -m venv venv
    pause
    exit /b 1
)

echo [1/2] Launching Enterprise FastAPI Web Application...
start "" "http://localhost:8000"

echo [2/2] Starting Uvicorn Server on http://localhost:8000 ...
.\venv\Scripts\python.exe -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload

pause
