# Run Pytest Test Suite
$ErrorActionPreference = "Stop"

$env:PYTHONPATH = "$PSScriptRoot\..;$PSScriptRoot\..\backend"
Write-Host "Executing backend and ML pipeline unit test suite..."
pytest -q backend/tests
