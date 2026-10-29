"""
Subjects Reference Endpoint.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.subject import Subject

router = APIRouter(prefix="/subjects", tags=["Subjects"])


@router.get("")
def list_subjects(
    db: Session = Depends(get_db),
    semester: Optional[str] = Query("sem5"),
):
    """List subjects offered in specified academic semester."""
    subjects = db.scalars(select(Subject).where(Subject.semester_code == semester)).all()
    if not subjects:
        subjects = db.scalars(select(Subject)).all()

    return [
        {
            "code": s.code,
            "name": s.name,
            "short_name": s.short_name,
            "semester_code": s.semester_code,
            "max_quiz": s.max_quiz,
            "max_internal": s.max_internal,
        }
        for s in subjects
    ]
