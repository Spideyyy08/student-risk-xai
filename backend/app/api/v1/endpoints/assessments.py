"""
Assessment Data Entry Endpoint.
"""

from typing import Annotated
from datetime import date
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.core.deps import require_roles
from app.core.roles import STAFF_ROLES
from app.core.exceptions import AppException
from app.schemas.academic import AssessmentCreate, DataEntryResponse, PredictionSummary
from app.models.user import User
from app.models.student import Student
from app.models.subject import Subject
from app.models.assessment import Assessment
from app.services.prediction_service import score_and_store_prediction

router = APIRouter(prefix="/assessments", tags=["Data Entry"])


@router.post("", response_model=DataEntryResponse)
def log_assessment(
    payload: AssessmentCreate,
    current_user: Annotated[User, Depends(require_roles(STAFF_ROLES))],
    db: Session = Depends(get_db),
):
    """Log an assessment score and synchronously update the student risk profile."""
    student = db.scalar(
        select(Student).where(
            (Student.student_code == payload.student_id) | (Student.roll == payload.student_id)
        )
    )
    if not student:
        raise AppException("Please select a student.", status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    subject = db.scalar(
        select(Subject).where(
            (Subject.code == payload.subject) | (Subject.short_name == payload.subject) | (Subject.name == payload.subject)
        )
    )
    if not subject:
        raise AppException(f"Subject '{payload.subject}' not found.", status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    if payload.max <= 0:
        raise AppException("Assessment maximum marks must be strictly greater than 0.", status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
    if payload.score > payload.max:
        raise AppException(f"Score ({payload.score}) cannot exceed maximum marks ({payload.max}).", status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    # Kind mapping
    ass_type = payload.assessment.strip()
    if "mid" in ass_type.lower():
        kind = "MIDSEM"
    elif "lab" in ass_type.lower():
        kind = "LABTEST"
    else:
        kind = "QUIZ"

    assess = Assessment(
        student_id=student.id,
        subject_id=subject.id,
        name=payload.assessment,
        kind=kind,
        score=payload.score,
        max_score=payload.max,
        assessed_on=date.today(),
    )
    db.add(assess)
    db.commit()

    pred = score_and_store_prediction(db, student.id, semester_code=subject.semester_code)

    return DataEntryResponse(
        success=True,
        message=f"{payload.assessment} score recorded for {student.name}. Risk profile recomputed.",
        prediction=PredictionSummary(
            risk_level=pred.risk_level,
            probabilities={"low": pred.p_low, "medium": pred.p_medium, "high": pred.p_high},
        ),
    )
