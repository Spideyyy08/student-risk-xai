"""
Prediction Inference and Batch Cohort Re-scoring Endpoints.
"""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.core.deps import get_current_user, require_roles, require_self_or_staff
from app.core.roles import UserRole, STAFF_ROLES
from app.schemas.prediction import PredictionResponse
from app.schemas.recommendation import GenericSuccessResponse
from app.models.user import User
from app.models.student import Student
from app.models.prediction import Prediction
from app.services.prediction_service import score_and_store_prediction

router = APIRouter(prefix="/predictions", tags=["Predictions"])


@router.get("/{student_identifier}", response_model=PredictionResponse)
def get_student_prediction(
    student_identifier: str,
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    semester: Optional[str] = Query("sem5"),
):
    """
    Get latest prediction for student; computes on-demand if none stored.
    Enforces student self-access check.
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

    return PredictionResponse(
        student_id=student.student_code,
        risk_level=pred.risk_level,
        probabilities={"low": pred.p_low, "medium": pred.p_medium, "high": pred.p_high},
        updated_at=pred.created_at.strftime("%Y-%m-%d"),
        model_version=pred.model_version,
        low_confidence=pred.low_confidence,
        is_estimate=True,
    )


@router.post("/run", response_model=GenericSuccessResponse)
def run_cohort_predictions(
    current_user: Annotated[User, Depends(require_roles(STAFF_ROLES))],
    db: Session = Depends(get_db),
    semester: Optional[str] = Query("sem5"),
):
    """
    Recompute predictions and recommendations for the entire active student cohort.
    Restricted to ADMIN and TEACHER roles.
    """
    students = db.scalars(select(Student).where(Student.is_active == True)).all()
    count = 0
    for st in students:
        score_and_store_prediction(db, st.id, semester_code=semester)
        count += 1

    return GenericSuccessResponse(
        success=True,
        message=f"Successfully recomputed predictions for all {count} active students in {semester}.",
    )
