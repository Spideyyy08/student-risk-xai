"""
Prediction and Scoring Service.
Coordinates feature extraction, inference, SHAP explanations, and persistent storage.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd
from fastapi import status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.services.model_registry import model_bundle
from app.services.feature_service import compute_features_for_student_semester
from app.models.prediction import Prediction
from app.models.student import Student
from ml_pipeline.src.predict import predict_single_student
from ml_pipeline.src.explain_shap import explain_instance
from ml_pipeline.config import FEATURES


def score_and_store_prediction(
    db: Session,
    student_id: int,
    semester_code: str = "sem5",
) -> Prediction:
    """
    Score student, persist prediction, and update latest pointer.
    Synchronously recomputes personalized recommendations.
    """
    if not model_bundle.is_loaded:
        loaded = model_bundle.load()
        if not loaded:
            raise AppException(
                "Model artifacts missing. Run python ml_pipeline/scripts/03_train_models.py",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

    # 1. Compute features
    features = compute_features_for_student_semester(db, student_id, semester_code)

    # 2. Score via pipeline
    risk_level, norm_probs, low_conf = predict_single_student(model_bundle.pipeline, features)

    # 3. SHAP explanation
    preprocessor = model_bundle.pipeline.named_steps["preprocessor"]
    row_df = pd.DataFrame([{f: float(features[f]) for f in FEATURES}])
    preprocessed_row = preprocessor.transform(row_df)

    base_val, factors = explain_instance(
        explainer=model_bundle.explainer,
        preprocessed_row=preprocessed_row,
        raw_feature_dict=features,
        top_n=6,
        class_idx=2,  # Class 2 is High Risk
    )

    # 4. Mark older predictions as not latest
    db.execute(
        update(Prediction)
        .where(
            Prediction.student_id == student_id,
            Prediction.semester_code == semester_code,
            Prediction.is_latest == True,
        )
        .values(is_latest=False)
    )

    # 5. Insert new latest prediction
    pred_record = Prediction(
        student_id=student_id,
        semester_code=semester_code,
        model_version=model_bundle.version,
        risk_level=risk_level,
        p_low=float(norm_probs["low"]),
        p_medium=float(norm_probs["medium"]),
        p_high=float(norm_probs["high"]),
        low_confidence=bool(low_conf),
        features=features,
        shap=factors,
        base_value=float(base_val),
        created_at=datetime.now(timezone.utc),
        is_latest=True,
    )
    db.add(pred_record)
    db.flush()

    # 6. Recompute recommendations synchronously
    from app.services.recommendation_service import generate_and_store_recommendations
    generate_and_store_recommendations(
        db=db,
        student_id=student_id,
        semester_code=semester_code,
        features=features,
        factors=factors,
        prediction_id=pred_record.id,
    )

    db.commit()
    db.refresh(pred_record)
    return pred_record
