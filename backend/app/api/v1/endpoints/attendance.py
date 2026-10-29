"""
Attendance Data Entry Endpoint.
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
from app.schemas.academic import AttendanceCreate, DataEntryResponse, PredictionSummary
from app.models.user import User
from app.models.student import Student
from app.models.subject import Subject
from app.models.attendance import AttendanceRecord
from app.services.prediction_service import score_and_store_prediction

router = APIRouter(prefix="/attendance", tags=["Data Entry"])


@router.post("", response_model=DataEntryResponse)
def log_attendance(
    payload: AttendanceCreate,
    current_user: Annotated[User, Depends(require_roles(STAFF_ROLES))],
    db: Session = Depends(get_db),
):
    """Log an attendance snapshot and synchronously update the student risk profile."""
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

    try:
        rec_date = date.fromisoformat(payload.date)
    except Exception:
        raise AppException("Invalid date format. Expected YYYY-MM-DD.", status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    att = AttendanceRecord(
        student_id=student.id,
        subject_id=subject.id,
        record_date=rec_date,
        attendance_pct=payload.attendance_pct,
        classes_held=20,
        classes_attended=int(round(payload.attendance_pct * 0.20)),
    )
    db.add(att)
    db.commit()

    # Recompute prediction
    pred = score_and_store_prediction(db, student.id, semester_code=subject.semester_code)

    return DataEntryResponse(
        success=True,
        message=f"Attendance record logged for {student.name}. Risk profile recomputed.",
        prediction=PredictionSummary(
            risk_level=pred.risk_level,
            probabilities={"low": pred.p_low, "medium": pred.p_medium, "high": pred.p_high},
        ),
    )
