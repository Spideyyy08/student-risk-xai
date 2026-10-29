"""
Class Analytics, Longitudinal Trends, and Subject Breakdown Endpoints.
"""

from typing import Annotated, Optional, List, Dict, Any
from collections import defaultdict
import numpy as np
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.db.session import get_db
from app.core.deps import get_current_user, require_roles, require_self_or_staff
from app.core.roles import UserRole, STAFF_ROLES
from app.schemas.academic import SubjectPerformanceOut, TrendResponse
from app.models.user import User
from app.models.student import Student
from app.models.prediction import Prediction
from app.services.trend_service import get_student_subject_breakdown, get_student_trends
from ml_pipeline.src.feature_engineering import FEATURE_META

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/class-summary")
def get_class_summary(
    current_user: Annotated[User, Depends(require_roles(STAFF_ROLES))],
    db: Session = Depends(get_db),
    division: Optional[str] = Query("ALL"),
    semester: Optional[str] = Query("sem5"),
):
    """
    Generate aggregate risk metrics and global top SHAP factors for cohort overview.
    Restricted to ADMIN and TEACHER roles.
    """
    div_filter = division.strip() if division else "ALL"

    query = (
        select(Student, Prediction)
        .join(
            Prediction,
            (Prediction.student_id == Student.id)
            & (Prediction.semester_code == semester)
            & (Prediction.is_latest == True),
        )
        .where(Student.is_active == True)
    )

    if div_filter != "ALL":
        query = query.where(Student.division == div_filter)

    results = db.execute(query).all()

    total = len(results)
    high_count = sum(1 for _, p in results if p.risk_level == "High")
    med_count = sum(1 for _, p in results if p.risk_level == "Medium")
    low_count = sum(1 for _, p in results if p.risk_level == "Low")

    high_pct = round((high_count / total) * 100.0, 1) if total > 0 else 0.0
    med_pct = round((med_count / total) * 100.0, 1) if total > 0 else 0.0
    low_pct = round((low_count / total) * 100.0, 1) if total > 0 else 0.0

    # by_division breakdown (only include divisions matching filter)
    div_data = defaultdict(lambda: {"total": 0, "high": 0, "medium": 0, "low": 0})
    for st, p in results:
        d = st.division
        div_data[d]["total"] += 1
        if p.risk_level == "High":
            div_data[d]["high"] += 1
        elif p.risk_level == "Medium":
            div_data[d]["medium"] += 1
        else:
            div_data[d]["low"] += 1

    by_division = []
    for d_name in sorted(div_data.keys()):
        stats = div_data[d_name]
        by_division.append({
            "division": d_name,
            "total": stats["total"],
            "high": stats["high"],
            "medium": stats["medium"],
            "low": stats["low"],
        })

    # Top factors across cohort (mean absolute SHAP and sign of mean)
    feat_shaps = defaultdict(list)
    for _, p in results:
        factors = p.shap or []
        for f in factors:
            fname = f.get("feature")
            val = float(f.get("shap", 0.0))
            if fname:
                feat_shaps[fname].append(val)

    factor_metrics = []
    for fname, vals in feat_shaps.items():
        if vals:
            mean_abs = float(np.mean(np.abs(vals)))
            mean_val = float(np.mean(vals))
            label = FEATURE_META.get(fname, {}).get("label", fname)
            if mean_val > 0.01:
                direction = "risk_raising"
            elif mean_val < -0.01:
                direction = "risk_lowering"
            else:
                direction = "risk_neutral"

            factor_metrics.append({
                "factor": label,
                "mean_abs": mean_abs,
                "direction": direction,
            })

    factor_metrics.sort(key=lambda x: x["mean_abs"], reverse=True)
    top_5 = factor_metrics[:5]
    total_abs = sum(f["mean_abs"] for f in top_5) or 1.0

    top_factors = [
        {
            "factor": f["factor"],
            "importance": round(f["mean_abs"] / total_abs, 4),
            "direction": f["direction"],
        }
        for f in top_5
    ]

    return {
        "total": total,
        "high": high_count,
        "high_pct": high_pct,
        "medium": med_count,
        "medium_pct": med_pct,
        "low": low_count,
        "low_pct": low_pct,
        "by_division": by_division,
        "top_factors": top_factors,
        "semester": semester,
        "division": div_filter,
    }


@router.get("/{student_identifier}/subjects", response_model=List[SubjectPerformanceOut])
def get_student_subjects(
    student_identifier: str,
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    semester: Optional[str] = Query("sem5"),
):
    """Subject-wise status and grade breakdown."""
    student = require_self_or_staff(student_identifier, current_user, db, request)
    breakdown = get_student_subject_breakdown(db, student.id, semester_code=semester)
    return [SubjectPerformanceOut(**item) for item in breakdown]


@router.get("/{student_identifier}/trends", response_model=TrendResponse)
def get_trends(
    student_identifier: str,
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    semester: Optional[str] = Query("sem5"),
):
    """6-month longitudinal attendance, quiz, and past SGPA progression."""
    student = require_self_or_staff(student_identifier, current_user, db, request)
    trend_data = get_student_trends(db, student.id, semester_code=semester)
    return TrendResponse(**trend_data)
