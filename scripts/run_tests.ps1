$Root = Split-Path -Parent $PSScriptRoot
& "$Root\.venv\Scripts\Activate.ps1"
$env:PYTHONPATH = $Root
Set-Location $Root
pytest -v