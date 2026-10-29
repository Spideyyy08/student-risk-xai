"""
What-If Academic Simulation Service.
Runs hypothetical parameter counterfactuals with 30s in-memory feature caching.
Zero database mutations.
"""

import time
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import status

from app.core.exceptions import AppException
from app.services.model_registry import model_bundle
from app.services.feature_service import compute_features_for_student_semester
from app.models.student import Student
from app.models.prediction import Prediction
from ml_pipeline.src.predict import predict_single_student
from ml_pipeline.src.explain_shap import explain_instance
from ml_pipeline.config import FEATURES, SIMULATOR_OVERRIDABLE_FEATURES

# In-memory baseline feature cache: (student_id, semester_code) -> (timestamp, features_dict)
_BASELINE_CACHE: Dict[tuple, tuple] = {}
CACHE_TTL_SECONDS = 30.0


def get_cached_baseline_features(db: Session, student_id: int, semester_code: str) -> Dict[str, float]:
    """Retrieve baseline features, checking 30-second TTL in-memory cache."""
    now = time.time()
    cache_key = (student_id, semester_code)
    if cache_key in _BASELINE_CACHE:
        ts, feats = _BASELINE_CACHE[cache_key]
        if now - ts < CACHE_TTL_SECONDS:
            return dict(feats)

    feats = compute_features_for_student_semester(db, student_id, semester_code)
    _BASELINE_CACHE[cache_key] = (now, dict(feats))
    return feats


def run_what_if_simulation(
    db: Session,
    student_identifier: str,
    overrides: Dict[str, Any],
    semester_code: str = "sem5",
) -> Dict[str, Any]:
    """
    Execute non-mutating what-if simulation against loaded model bundle.
    """
    if not model_bundle.is_loaded:
        if not model_bundle.load():
            raise AppException("Prediction model is not loaded.", status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

    # 1. Resolve student
    student = db.scalar(
        select(Student).where(
            (Student.student_code == student_identifier) | (Student.roll == student_identifier)
        )
    )
    if not student:
        raise AppException(f"Student '{student_identifier}' not found.", status_code=status.HTTP_404_NOT_FOUND)

    # 2. Get baseline features and current prediction
    baseline_features = get_cached_baseline_features(db, student.id, semester_code)

    curr_pred = db.scalar(
        select(Prediction)
        .where(
            Prediction.student_id == student.id,
            Prediction.semester_code == semester_code,
            Prediction.is_latest == True,
        )
    )

    if curr_pred:
        curr_risk = curr_pred.risk_level
        curr_probs = {"low": curr_pred.p_low, "medium": curr_pred.p_medium, "high": curr_pred.p_high}
    else:
        # Compute baseline on the fly
        curr_risk, curr_probs, _ = predict_single_student(model_bundle.pipeline, baseline_features)

    # 3. Apply simulator overrides (only allowed overridable features)
    simulated_features = dict(baseline_features)
    for k, v in overrides.items():
        if k in SIMULATOR_OVERRIDABLE_FEATURES and v is not None:
            simulated_features[k] = float(v)

    # 4. Predict simulated risk
    sim_risk, sim_probs, _ = predict_single_student(model_bundle.pipeline, simulated_features)

    # 5. Explain simulated state via Tree SHAP
    preprocessor = model_bundle.pipeline.named_steps["preprocessor"]
    row_df = pd.DataFrame([{f: float(simulated_features[f]) for f in FEATURES}])
    sim_preprocessed = preprocessor.transform(row_df)

    _, sim_factors = explain_instance(
        explainer=model_bundle.explainer,
        preprocessed_row=sim_preprocessed,
        raw_feature_dict=simulated_features,
        top_n=6,
        class_idx=2,  # High risk
    )

    return {
        "current": {
            "student_id": student.student_code,
            "name": student.name,
            "roll": student.roll,
            "risk_level": curr_risk,
            "probabilities": curr_probs,
            "attendance_pct": int(round(baseline_features.get("attendance_pct", 0.0))),
            "quiz_avg": int(round(baseline_features.get("quiz_avg", 0.0))),
            "assignment_pct": int(round(baseline_features.get("assignment_pct", 0.0))),
            "internal_marks": int(round(baseline_features.get("internal_marks", 0.0))),
            "practical_marks": int(round(baseline_features.get("practical_marks", 0.0))),
            "backlogs": int(round(baseline_features.get("backlogs", 0.0))),
        },
        "simulated": {
            "risk_level": sim_risk,
            "probabilities": sim_probs,
            "factors": sim_factors,
        },
    }
