"""
Personalized Recommendation Endpoints.
"""

from typing import Annotated, Optional, List
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.core.deps import get_current_user, require_self_or_staff, require_roles
from app.core.roles import UserRole, STAFF_ROLES
from app.core.exceptions import AppException
from app.schemas.recommendation import RecommendationOut, RecommendationUpdate, GenericSuccessResponse
from app.models.user import User
from app.models.recommendation import Recommendation
from app.services.prediction_service import score_and_store_prediction

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("/{student_identifier}", response_model=List[RecommendationOut])
def get_student_recommendations(
    student_identifier: str,
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    semester: Optional[str] = Query("sem5"),
):
    """
    Get top personalized recommendations for student.
    Enforces student self-access check.
    """
    student = require_self_or_staff(student_identifier, current_user, db, request)

    recs = db.scalars(
        select(Recommendation)
        .where(
            Recommendation.student_id == student.id,
            Recommendation.semester_code == semester,
        )
    ).all()

    if not recs:
        # Generate on demand
        score_and_store_prediction(db, student.id, semester_code=semester)
        recs = db.scalars(
            select(Recommendation)
            .where(
                Recommendation.student_id == student.id,
                Recommendation.semester_code == semester,
            )
        ).all()

    prio_order = {"High": 0, "Medium": 1, "Low": 2}
    sorted_recs = sorted(recs, key=lambda r: prio_order.get(r.priority, 99))[:6]

    return [
        RecommendationOut(
            id=r.id,
            priority=r.priority,
            action=r.action,
            reason=r.reason,
            subject=r.subject,
            assigned=r.assigned,
        )
        for r in sorted_recs
    ]


@router.patch("/{student_identifier}/{rec_id}", response_model=GenericSuccessResponse)
def update_recommendation_status(
    student_identifier: str,
    rec_id: int,
    payload: RecommendationUpdate,
    request: Request,
    current_user: Annotated[User, Depends(require_roles(STAFF_ROLES))],
    db: Session = Depends(get_db),
):
    """
    Mark recommendation as assigned or unassigned.
    Restricted to faculty (ADMIN/TEACHER).
    """
    rec = db.scalar(select(Recommendation).where(Recommendation.id == rec_id))
    if not rec:
        raise AppException(f"Recommendation with ID {rec_id} not found.", status_code=status.HTTP_404_NOT_FOUND)

    rec.assigned = payload.assigned
    db.commit()
    return GenericSuccessResponse(success=True, message=f"Recommendation assigned status updated to {payload.assigned}.")
