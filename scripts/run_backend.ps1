# Start the API (and the frontend it serves) on http://127.0.0.1:8000
$Root = Split-Path -Parent $PSScriptRoot
& "$Root\.venv\Scripts\Activate.ps1"
$env:PYTHONPATH = $Root
Set-Location "$Root\backend"
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000