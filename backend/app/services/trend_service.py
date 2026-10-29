"""
Analytics and Trend Visualization Service.
Generates 6-month longitudinal trends, past SGPA histories, and subject breakdown statuses.
"""

from typing import Dict, Any, List
from collections import defaultdict
import numpy as np
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from app.models.student import Student
from app.models.subject import Subject
from app.models.attendance import AttendanceRecord
from app.models.assessment import Assessment
from app.models.assignment import Assignment
from app.models.semester_result import SemesterResult


def get_student_subject_breakdown(
    db: Session,
    student_id: int,
    semester_code: str = "sem5",
) -> List[Dict[str, Any]]:
    """Subject-wise academic breakdown with status indicators."""
    subjects = db.scalars(select(Subject).where(Subject.semester_code == semester_code)).all()
    if not subjects:
        subjects = db.scalars(select(Subject)).all()

    breakdown = []
    for s in subjects:
        # Latest attendance
        latest_att = db.scalars(
            select(AttendanceRecord.attendance_pct)
            .where(
                AttendanceRecord.student_id == student_id,
                AttendanceRecord.subject_id == s.id,
            )
            .order_by(desc(AttendanceRecord.record_date))
            .limit(1)
        ).first()
        att_val = int(round(float(latest_att))) if latest_att is not None else 75

        # Quizzes
        quizzes = db.scalars(
            select(Assessment).where(
                Assessment.student_id == student_id,
                Assessment.subject_id == s.id,
                Assessment.kind == "QUIZ",
            )
        ).all()
        q_pcts = [(q.score / q.max_score) * 100.0 for q in quizzes if q.max_score > 0]
        quiz_val = int(round(sum(q_pcts) / len(q_pcts))) if q_pcts else 65

        # Mid-sem
        midsem = db.scalars(
            select(Assessment).where(
                Assessment.student_id == student_id,
                Assessment.subject_id == s.id,
                Assessment.kind == "MIDSEM",
            )
        ).first()
        internal_val = int(round((midsem.score / midsem.max_score) * 30.0)) if (midsem and midsem.max_score > 0) else 18

        # Assignments
        assigns = db.scalars(
            select(Assignment).where(
                Assignment.student_id == student_id,
                Assignment.subject_id == s.id,
            )
        ).all()
        if assigns:
            a_scores = [
                0.70 * (100.0 if a.status == "Submitted on time" else (60.0 if a.status == "Submitted late" else 0.0))
                + 0.30 * ((a.score / 10.0) * 100.0)
                for a in assigns
            ]
            assign_val = int(round(sum(a_scores) / len(a_scores)))
        else:
            assign_val = 70

        # Status determination:
        # Critical if att<60 or quiz<50 or internal<14; Attention if att<75 or quiz<65 or internal<18; else Satisfactory
        if att_val < 60 or quiz_val < 50 or internal_val < 14:
            stat = "Critical"
        elif att_val < 75 or quiz_val < 65 or internal_val < 18:
            stat = "Attention"
        else:
            stat = "Satisfactory"

        breakdown.append({
            "subject_code": s.code,
            "subject_name": s.name,
            "subject_short": s.short_name,
            "attendance_pct": att_val,
            "quiz_avg": quiz_val,
            "quiz_max": 100,
            "assignment_pct": assign_val,
            "internal_marks": internal_val,
            "internal_max": 30,
            "status": stat,
        })

    return breakdown


def get_student_trends(
    db: Session,
    student_id: int,
    semester_code: str = "sem5",
) -> Dict[str, Any]:
    """Generate 6-month timeline data and past 2 semester SGPAs."""
    subjects = db.scalars(select(Subject).where(Subject.semester_code == semester_code)).all()
    subject_ids = [s.id for s in subjects]

    # Attendance snapshots by month
    att_records = db.scalars(
        select(AttendanceRecord)
        .where(
            AttendanceRecord.student_id == student_id,
            AttendanceRecord.subject_id.in_(subject_ids) if subject_ids else True,
        )
        .order_by(AttendanceRecord.record_date)
    ).all()

    att_by_month = defaultdict(list)
    month_names_order = []
    for r in att_records:
        m_str = r.record_date.strftime("%b %Y")
        if m_str not in month_names_order:
            month_names_order.append(m_str)
        att_by_month[m_str].append(float(r.attendance_pct))

    # Quizzes by month
    quizzes = db.scalars(
        select(Assessment)
        .where(
            Assessment.student_id == student_id,
            Assessment.subject_id.in_(subject_ids) if subject_ids else True,
            Assessment.kind == "QUIZ",
        )
        .order_by(Assessment.assessed_on)
    ).all()

    quiz_by_month = defaultdict(list)
    for q in quizzes:
        m_str = q.assessed_on.strftime("%b %Y")
        if m_str not in month_names_order:
            month_names_order.append(m_str)
        if q.max_score > 0:
            quiz_by_month[m_str].append(float((q.score / q.max_score) * 100.0))

    if semester_code == "sem4":
        default_months = ["Dec 2025", "Jan 2026", "Feb 2026", "Mar 2026", "Apr 2026", "May 2026"]
    else:
        default_months = ["May 2026", "Jun 2026", "Jul 2026", "Aug 2026", "Sep 2026", "Oct 2026"]

    months = month_names_order[-6:] if len(month_names_order) >= 6 else default_months

    att_series = []
    quiz_series = []
    for m in months:
        if m in att_by_month and att_by_month[m]:
            att_series.append(int(round(np.mean(att_by_month[m]))))
        else:
            att_series.append(75)

        if m in quiz_by_month and quiz_by_month[m]:
            quiz_series.append(int(round(np.mean(quiz_by_month[m]))))
        else:
            quiz_series.append(65)

    # Past 2 completed semesters
    def sem_num(c: str) -> int:
        try:
            return int(c.lower().replace("sem", ""))
        except Exception:
            return 0

    target_num = sem_num(semester_code)
    results = db.scalars(
        select(SemesterResult).where(SemesterResult.student_id == student_id)
    ).all()
    prior_results = [r for r in sorted(results, key=lambda x: sem_num(x.semester_code)) if sem_num(r.semester_code) < target_num]

    past_sgpa = []
    for r in prior_results[-2:]:
        num = sem_num(r.semester_code)
        past_sgpa.append({
            "semester": f"Sem {num}",
            "sgpa": round(float(r.sgpa), 2),
        })

    return {
        "months": months,
        "attendance": att_series,
        "quiz_scores": quiz_series,
        "past_sgpa": past_sgpa,
    }
