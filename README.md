# Explainable AI-Based Student Academic Risk Prediction and Personalized Early Intervention System

Vishwakarma Institute of Technology - Computer Engineering - Group SEDA-A8

Predicts Low / Medium / High academic risk, explains it with SHAP, recommends study actions,
and lets teachers run what-if simulations. Early-support tool, not a punitive system.

## Quick start (Windows PowerShell)

```powershell
.\.venv\Scripts\Activate.ps1          # activate virtual environment
.\scripts\run_db.ps1                  # start MySQL in Docker (host port 3307)
.\scripts\run_ml_pipeline.ps1         # generate data + train + SHAP
.\scripts\run_backend.ps1             # API + frontend at http://127.0.0.1:8000
```

API docs: http://127.0.0.1:8000/docs

## Layout

| Folder | Purpose |
|---|---|
| backend/ | FastAPI app (API, services, ORM models, tests) |
| ml_pipeline/ | Training, evaluation, prediction, SHAP scripts (independent of the API) |
| frontend/ | Vanilla HTML / CSS / JS dashboard + What-If simulator (Chart.js) |
| database/ | MySQL init scripts mounted into the Docker container |
| data/ | raw / interim / processed / synthetic datasets (git-ignored contents) |
| docs/ | Architecture, API spec, ethics, test evidence |
| scripts/ | PowerShell helper scripts |

## Team
Samrudhi Ambekar, Swarali Patil, Manav Talpade, Aryan Yadav - Guide: Ms. Jyoti Yadav