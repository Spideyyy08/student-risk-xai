# Start Uvicorn Backend Development Server
$ErrorActionPreference = "Stop"

$env:PYTHONPATH = "$PSScriptRoot\..;$PSScriptRoot\..\backend"
Write-Host "Starting FastAPI Backend Server on http://127.0.0.1:8000..."
uvicorn app.main:app --reload --port 8000 --app-dir backend
