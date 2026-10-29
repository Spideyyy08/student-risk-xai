"""
SHAP Explanation and Feature Attribution Endpoints.
"""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.core.deps import get_current_user, require_self_or_staff
from app.schemas.prediction import ExplanationResponse, Factor
from app.models.user import User
from app.models.prediction import Prediction
from app.services.prediction_service import score_and_store_prediction

router = APIRouter(prefix="/explanations", tags=["Explanations"])


@router.get("/{student_identifier}", response_model=ExplanationResponse)
def get_student_explanation(
    student_identifier: str,
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    semester: Optional[str] = Query("sem5"),
    top: int = Query(6, ge=1, le=10),
):
    """
    Get top SHAP feature attribution factors for student risk classification.
    """
    student = require_self_or_staff(student_identifier, current_user, db, request)

    pred = db.scalar(
        select(Prediction)
        .where(
            Prediction.student_id == student.id,
            Prediction.semester_code == semester,
            Prediction.is_latest == True,
        )
    )

    if not pred:
        pred = score_and_store_prediction(db, student.id, semester_code=semester)

    factors_raw = pred.shap or []
    factors = [Factor(**f) for f in factors_raw[:top]]

    return ExplanationResponse(
        base_value=float(pred.base_value),
        factors=factors,
    )
