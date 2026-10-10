@echo off
title Self-Evolving AI Supply Chain Network
color 0B

echo ===============================================================================
echo   SELF-EVOLVING AI AGENT SUPPLY CHAIN NETWORK - MISSION CONTROL LAUNCHER
echo ===============================================================================
echo.
echo [*] Checking Python environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.10+ and try again.
    pause
    exit /b 1
)

echo [*] Launching Mission Control Web Application on http://127.0.0.1:8000 ...
echo [*] Opening default web browser in 3 seconds...

start "" http://127.0.0.1:8000

echo.
echo [*] Starting FastAPI & LangGraph backend engine...
python -m uvicorn web.server:app --host 127.0.0.1 --port 8000 --reload

pause
