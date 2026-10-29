"""
Student Roster and Detailed Profile Endpoints.
Implements pagination, cohort filtering, multi-field searching, and role access control.
"""

from typing import Annotated, Optional, List
import math
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc, asc

from app.db.session import get_db
from app.core.deps import get_current_user, require_roles, require_self_or_staff
from app.core.roles import UserRole, STAFF_ROLES
from app.core.exceptions import AppException
from app.schemas.student import StudentOut, StudentListResponse, PastSGPAItem
from app.models.user import User
from app.models.student import Student
from app.models.semester import Semester
from app.models.semester_result import SemesterResult
from app.models.prediction import Prediction
from app.services.feature_service import compute_features_for_student_semester
from app.services.prediction_service import score_and_store_prediction
from ml_pipeline.src.feature_engineering import compute_key_factor

router = APIRouter(prefix="/students", tags=["Students"])


def build_student_out(
    db: Session,
    student: Student,
    semester_code: str = "sem5",
    sem_label: Optional[str] = None,
) -> StudentOut:
    """Format single student into exact frozen contract representation."""
    if not sem_label:
        sem_obj = db.scalar(select(Semester).where(Semester.code == semester_code))
        sem_label = sem_obj.label if sem_obj else f"Semester 5 (AY 2026-27)"

    pred = db.scalar(
        select(Prediction)
        .where(
            Prediction.student_id == student.id,
            Prediction.semester_code == semester_code,
            Prediction.is_latest == True,
        )
    )

    if not pred:
        pred = score_and_store_prediction(db, student.id, semester_code=semester_code)

    feats = pred.features or {}
    probs = {"low": pred.p_low, "medium": pred.p_medium, "high": pred.p_high}
    updated_str = pred.created_at.strftime("%Y-%m-%d")

    # Past SGPAs
    results = db.scalars(
        select(SemesterResult).where(SemesterResult.student_id == student.id)
    ).all()

    def sem_num(c: str) -> int:
        try:
            return int(c.lower().replace("sem", ""))
        except Exception:
            return 0

    target_num = sem_num(semester_code)
    prior_results = [r for r in sorted(results, key=lambda x: sem_num(x.semester_code)) if sem_num(r.semester_code) < target_num]

    past_sgpa = []
    for r in prior_results[-2:]:
        num = sem_num(r.semester_code)
        past_sgpa.append(PastSGPAItem(semester=f"Sem {num}", sgpa=round(float(r.sgpa), 2)))

    kf = compute_key_factor(pred.shap or [], pred.risk_level)

    return StudentOut(
        id=student.student_code,
        roll=student.roll,
        name=student.name,
        division=student.division,
        semester=sem_label,
        risk_level=pred.risk_level,
        probabilities=probs,
        updated_at=updated_str,
        attendance_pct=int(round(float(feats.get("attendance_pct", 75)))),
        quiz_avg=int(round(float(feats.get("quiz_avg", 65)))),
        assignment_pct=int(round(float(feats.get("assignment_pct", 70)))),
        internal_marks=int(round(float(feats.get("internal_marks", 18)))),
        practical_marks=int(round(float(feats.get("practical_marks", 18)))),
        backlogs=int(round(float(feats.get("backlogs", 0)))),
        key_factor=kf,
        past_sgpa=past_sgpa,
    )


@router.get("", response_model=StudentListResponse)
def list_students(
    request: Request,
    current_user: Annotated[User, Depends(require_roles(STAFF_ROLES))],
    db: Session = Depends(get_db),
    division: Optional[str] = Query(None),
    risk: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=200),
    semester: Optional[str] = Query("sem5"),
    sort: Optional[str] = Query(None),
    order: Optional[str] = Query("asc"),
):
    """
    Search and paginate students with cohort filters and server-side sorting.
    STUDENT role receives 403 Forbidden.
    """
    sem_obj = db.scalar(select(Semester).where(Semester.code == semester))
    sem_label = sem_obj.label if sem_obj else "Semester 5 (AY 2026-27)"

    # Base query joined with latest predictions for sorting/filtering
    query = (
        select(Student, Prediction)
        .outerjoin(
            Prediction,
            (Prediction.student_id == Student.id)
            & (Prediction.semester_code == semester)
            & (Prediction.is_latest == True),
        )
        .where(Student.is_active == True)
    )

    if division and division.upper() != "ALL":
        query = query.where(Student.division == division.strip())

    if risk and risk.upper() != "ALL":
        query = query.where(func.upper(Prediction.risk_level) == risk.strip().upper())

    if q and q.strip():
        term = f"%{q.strip().lower()}%"
        query = query.where(
            (func.lower(Student.name).like(term))
            | (func.lower(Student.roll).like(term))
            | (func.lower(Student.student_code).like(term))
        )

    # Determine sorting
    # Default rule: if risk=HIGH and no sort specified -> p_high desc; else roll asc
    effective_sort = sort
    effective_order = order.lower() if order else "asc"

    if not effective_sort:
        if risk and risk.upper() == "HIGH":
            effective_sort = "p_high"
            effective_order = "desc"
        else:
            effective_sort = "roll"
            effective_order = "asc"

    sort_col = Student.roll
    if effective_sort == "name":
        sort_col = Student.name
    elif effective_sort == "risk":
        sort_col = Prediction.risk_level
    elif effective_sort == "p_high":
        sort_col = Prediction.p_high
    elif effective_sort == "roll":
        sort_col = Student.roll

    if effective_order == "desc":
        query = query.order_by(desc(sort_col))
    else:
        query = query.order_by(asc(sort_col))

    all_pairs = db.execute(query).all()
    total = len(all_pairs)
    total_pages = max(1, math.ceil(total / page_size))
    offset = (page - 1) * page_size
    paged_pairs = all_pairs[offset : offset + page_size]

    items = []
    for st, _ in paged_pairs:
        items.append(build_student_out(db, st, semester_code=semester, sem_label=sem_label))

    return StudentListResponse(
        items=items,
        total=total,
        page=page,
        total_pages=total_pages,
        page_size=page_size,
        semester=semester,
    )


@router.get("/{student_identifier}", response_model=StudentOut)
def get_student_detail(
    student_identifier: str,
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    semester: Optional[str] = Query("sem5"),
):
    """
    Retrieve single student profile.
    Students can only view their own profile; faculty can view any.
    Accepts student_code (e.g. STU101) or roll (e.g. 221101).
    """
    student = require_self_or_staff(student_identifier, current_user, db, request)
    return build_student_out(db, student, semester_code=semester)
