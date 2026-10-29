"""
Teacher Intervention Logging Endpoints.
"""

from typing import Annotated, Optional, List
from datetime import datetime, date
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.db.session import get_db
from app.core.deps import get_current_user, require_roles
from app.core.roles import UserRole, STAFF_ROLES
from app.core.exceptions import AppException, ForbiddenException
from app.schemas.intervention import InterventionCreate, InterventionOut, InterventionCreateResponse
from app.models.user import User
from app.models.student import Student
from app.models.intervention import Intervention

router = APIRouter(prefix="/interventions", tags=["Interventions"])


@router.get("", response_model=List[InterventionOut])
def list_interventions(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    student_id: Optional[str] = Query(None),
):
    """
    List logged interventions.
    Students can only view their own logged interventions.
    """
    query = (
        select(Intervention, Student)
        .join(Student, Intervention.student_id == Student.id)
        .order_by(desc(Intervention.intervention_date), desc(Intervention.id))
    )

    if current_user.role == UserRole.STUDENT.value or current_user.role == "STUDENT":
        # Force student's own records
        query = query.where(Student.id == current_user.student_id)
    elif student_id:
        target = student_id.strip()
        query = query.where((Student.student_code == target) | (Student.roll == target))

    results = db.execute(query).all()

    items = []
    for inv, st in results:
        items.append(
            InterventionOut(
                id=inv.id,
                student_id=st.student_code,
                student_name=st.name,
                division=st.division,
                semester=inv.semester_code,  # exact code: sem4 or sem5
                type=inv.type,
                date=inv.intervention_date.strftime("%Y-%m-%d"),
                status=inv.status,
                notes=inv.notes or "",
            )
        )
    return items


@router.post("", response_model=InterventionCreateResponse)
def create_intervention(
    payload: InterventionCreate,
    current_user: Annotated[User, Depends(require_roles(STAFF_ROLES))],
    db: Session = Depends(get_db),
):
    """
    Log new support intervention for a student.
    Restricted to ADMIN and TEACHER roles.
    """
    student = db.scalar(
        select(Student).where(
            (Student.student_code == payload.student_id) | (Student.roll == payload.student_id)
        )
    )
    if not student:
        raise AppException(f"Student '{payload.student_id}' not found.", status_code=status.HTTP_404_NOT_FOUND)

    try:
        inv_date = date.fromisoformat(payload.date)
    except Exception:
        raise AppException("Invalid date format. Expected YYYY-MM-DD.", status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    sem_code = payload.semester or "sem5"

    inv = Intervention(
        student_id=student.id,
        semester_code=sem_code,
        type=payload.type,
        status=payload.status,
        intervention_date=inv_date,
        notes=payload.notes or "",
        created_by=current_user.id,
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)

    out_item = InterventionOut(
        id=inv.id,
        student_id=student.student_code,
        student_name=student.name,
        division=student.division,
        semester=inv.semester_code,
        type=inv.type,
        date=inv.intervention_date.strftime("%Y-%m-%d"),
        status=inv.status,
        notes=inv.notes or "",
    )

    return InterventionCreateResponse(success=True, item=out_item)
