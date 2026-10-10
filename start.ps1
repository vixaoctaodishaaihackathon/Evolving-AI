# Self-Evolving AI Supply Chain Network - PowerShell Launcher
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "  SELF-EVOLVING AI AGENT SUPPLY CHAIN NETWORK - MISSION CONTROL LAUNCHER" -ForegroundColor Cyan
Write-Host "===============================================================================" -ForegroundColor Cyan

# Check Python
try {
    $pyVersion = python --version 2>&1
    Write-Host "[*] Python Environment: $pyVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python is not installed or not in PATH!" -ForegroundColor Red
    exit 1
}

# Open browser
Write-Host "[*] Opening browser to http://127.0.0.1:8000 ..." -ForegroundColor Yellow
Start-Process "http://127.0.0.1:8000"

# Launch Server
Write-Host "[*] Starting FastAPI / LangGraph Server..." -ForegroundColor Green
python -m uvicorn web.server:app --host 127.0.0.1 --port 8000 --reload
