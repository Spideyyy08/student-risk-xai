"""
Assignment Data Entry Endpoint.
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
from app.schemas.academic import AssignmentCreate, DataEntryResponse, PredictionSummary
from app.models.user import User
from app.models.student import Student
from app.models.subject import Subject
from app.models.assignment import Assignment
from app.services.prediction_service import score_and_store_prediction

router = APIRouter(prefix="/assignments", tags=["Data Entry"])


@router.post("", response_model=DataEntryResponse)
def log_assignment(
    payload: AssignmentCreate,
    current_user: Annotated[User, Depends(require_roles(STAFF_ROLES))],
    db: Session = Depends(get_db),
):
    """Log an assignment submission and synchronously update the student risk profile."""
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

    assign = Assignment(
        student_id=student.id,
        subject_id=subject.id,
        title=payload.title,
        status=payload.status,
        score=float(payload.score),
        submitted_on=date.today(),
    )
    db.add(assign)
    db.commit()

    pred = score_and_store_prediction(db, student.id, semester_code=subject.semester_code)

    return DataEntryResponse(
        success=True,
        message=f"Assignment submission '{payload.title}' logged for {student.name}. Risk profile recomputed.",
        prediction=PredictionSummary(
            risk_level=pred.risk_level,
            probabilities={"low": pred.p_low, "medium": pred.p_medium, "high": pred.p_high},
        ),
    )
