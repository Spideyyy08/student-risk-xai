# Run ML Training and Evaluation Pipeline
$ErrorActionPreference = "Stop"

Write-Host "=========================================================="
Write-Host "Step 1: Generate Synthetic Dataset (3,000 students)"
Write-Host "=========================================================="
python ml_pipeline/scripts/01_generate_synthetic_data.py

Write-Host "`n=========================================================="
Write-Host "Step 2: Preprocess & Validate Feature Distributions"
Write-Host "=========================================================="
python ml_pipeline/scripts/02_preprocess.py

Write-Host "`n=========================================================="
Write-Host "Step 3: Train Candidate Models and Select Best Pipeline"
Write-Host "=========================================================="
python ml_pipeline/scripts/03_train_models.py --source csv

Write-Host "`n=========================================================="
Write-Host "Step 4: Evaluate Model Performance, Errors & Fairness"
Write-Host "=========================================================="
python ml_pipeline/scripts/04_evaluate_models.py

Write-Host "`n=========================================================="
Write-Host "Step 5: Compute SHAP Explanations, Summary & Stability"
Write-Host "=========================================================="
python ml_pipeline/scripts/05_compute_shap.py

Write-Host "`n[SUCCESS] Complete ML Pipeline finished successfully."
