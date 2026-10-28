# Generate data -> preprocess -> train -> evaluate -> SHAP
$Root = Split-Path -Parent $PSScriptRoot
& "$Root\.venv\Scripts\Activate.ps1"
$env:PYTHONPATH = $Root
Set-Location $Root
foreach ($s in @("01_generate_synthetic_data","02_preprocess","03_train_models","04_evaluate_models","05_compute_shap")) {
    Write-Host "Running $s ..." -ForegroundColor Cyan
    python "ml_pipeline\scripts\$s.py"
    if ($LASTEXITCODE -ne 0) { Write-Host "$s failed" -ForegroundColor Red; break }
}