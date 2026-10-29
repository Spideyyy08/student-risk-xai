"""
Feature Engineering and Derivation Service.
Single source of truth for converting normalized database records into model feature vectors.
Strictly implements Section 7 derivations.
"""

from typing import Dict, Any, List, Optional
from datetime import date
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
from ml_pipeline.config import FEATURES, FEATURE_RANGES


def compute_features_for_student_semester(
    db: Session,
    student_id: int,
    semester_code: str = "sem5",
) -> Dict[str, float]:
    """
    Derive the 10 machine learning features for a student in a specific semester.
    All outputs cast to native Python float.
    """
    # 1. Fetch subjects for target semester
    subjects = db.scalars(
        select(Subject).where(Subject.semester_code == semester_code)
    ).all()
    subject_ids = [s.id for s in subjects]

    if not subject_ids:
        # Fallback to all subjects if semester mismatch
        subjects = db.scalars(select(Subject)).all()
        subject_ids = [s.id for s in subjects]

    # 2. Overall Attendance: mean over subjects of the latest attendance_pct
    subject_att_list: List[float] = []
    for sid in subject_ids:
        latest_att = db.scalars(
            select(AttendanceRecord.attendance_pct)
            .where(
                AttendanceRecord.student_id == student_id,
                AttendanceRecord.subject_id == sid,
            )
            .order_by(desc(AttendanceRecord.record_date))
            .limit(1)
        ).first()
        if latest_att is not None:
            subject_att_list.append(float(latest_att))

    overall_att = float(np.mean(subject_att_list)) if subject_att_list else 75.0

    # 3. Quiz Average: mean over subjects of the mean of QUIZ assessments as (score/max * 100)
    subject_quiz_means: List[float] = []
    for sid in subject_ids:
        quizzes = db.scalars(
            select(Assessment)
            .where(
                Assessment.student_id == student_id,
                Assessment.subject_id == sid,
                Assessment.kind == "QUIZ",
            )
        ).all()
        if quizzes:
            q_pcts = [float((q.score / q.max_score) * 100.0) for q in quizzes if q.max_score > 0]
            if q_pcts:
                subject_quiz_means.append(float(np.mean(q_pcts)))

    overall_quiz = float(np.mean(subject_quiz_means)) if subject_quiz_means else 65.0

    # 4. Assignment Completion: on time=100, late=60, missing=0, blended 70/30 with (score/10 * 100)
    assignments = db.scalars(
        select(Assignment)
        .where(
            Assignment.student_id == student_id,
            Assignment.subject_id.in_(subject_ids) if subject_ids else True,
        )
    ).all()

    assign_scores: List[float] = []
    if assignments:
        for a in assignments:
            status_score = 100.0 if a.status == "Submitted on time" else (60.0 if a.status == "Submitted late" else 0.0)
            mark_score = float((a.score / 10.0) * 100.0)
            blended = 0.70 * status_score + 0.30 * mark_score
            assign_scores.append(blended)
    overall_assign = float(np.mean(assign_scores)) if assign_scores else 70.0

    # 5. Internal Marks (0-30): mean over subjects of MIDSEM score scaled to 30
    midsems = db.scalars(
        select(Assessment)
        .where(
            Assessment.student_id == student_id,
            Assessment.subject_id.in_(subject_ids) if subject_ids else True,
            Assessment.kind == "MIDSEM",
        )
    ).all()
    midsem_scores = [float((m.score / m.max_score) * 30.0) for m in midsems if m.max_score > 0]
    overall_internal = float(np.mean(midsem_scores)) if midsem_scores else 18.0

    # 6. Practical Marks (0-30): mean of LABTEST scores scaled to 30
    labtests = db.scalars(
        select(Assessment)
        .where(
            Assessment.student_id == student_id,
            Assessment.subject_id.in_(subject_ids) if subject_ids else True,
            Assessment.kind == "LABTEST",
        )
    ).all()
    labtest_scores = [float((l.score / l.max_score) * 30.0) for l in labtests if l.max_score > 0]
    overall_practical = float(np.mean(labtest_scores)) if labtest_scores else 18.0

    # 7. Backlogs, Prev SGPA, SGPA Delta from semester_results
    # Find all prior semester results for this student sorted
    results = db.scalars(
        select(SemesterResult)
        .where(SemesterResult.student_id == student_id)
    ).all()

    # Map semester codes to order: sem1 < sem2 < sem3 < sem4 < sem5
    def sem_num(code: str) -> int:
        try:
            return int(code.lower().replace("sem", ""))
        except Exception:
            return 0

    sorted_results = sorted(results, key=lambda r: sem_num(r.semester_code))
    target_num = sem_num(semester_code)
    prior_results = [r for r in sorted_results if sem_num(r.semester_code) < target_num]

    if prior_results:
        last_sem = prior_results[-1]
        backlogs = float(last_sem.backlogs_count)
        prev_sgpa = float(last_sem.sgpa)
        if len(prior_results) >= 2:
            second_last = prior_results[-2]
            sgpa_delta = float(last_sem.sgpa - second_last.sgpa)
        else:
            sgpa_delta = 0.0
    else:
        backlogs = 0.0
        prev_sgpa = 7.0
        sgpa_delta = 0.0

    # 8. Trends: least-squares slope over the last 6 months
    # Query all attendance records for student in this semester
    all_att_records = db.scalars(
        select(AttendanceRecord)
        .where(
            AttendanceRecord.student_id == student_id,
            AttendanceRecord.subject_id.in_(subject_ids) if subject_ids else True,
        )
        .order_by(AttendanceRecord.record_date)
    ).all()

    # Group by month string (YYYY-MM), take last snapshot per subject then average
    att_by_month_subj = defaultdict(dict)
    for rec in all_att_records:
        m_key = rec.record_date.strftime("%Y-%m")
        att_by_month_subj[m_key][rec.subject_id] = float(rec.attendance_pct)

    att_monthly_means = []
    for m_key in sorted(att_by_month_subj.keys()):
        vals = list(att_by_month_subj[m_key].values())
        if vals:
            att_monthly_means.append(float(np.mean(vals)))

    if len(att_monthly_means) >= 2:
        recent_att = att_monthly_means[-6:]
        x = np.arange(len(recent_att))
        slope, _ = np.polyfit(x, recent_att, deg=1)
        attendance_trend = float(slope)
    else:
        attendance_trend = 0.0

    # Quiz trend: group QUIZ assessments by month
    all_quizzes = db.scalars(
        select(Assessment)
        .where(
            Assessment.student_id == student_id,
            Assessment.subject_id.in_(subject_ids) if subject_ids else True,
            Assessment.kind == "QUIZ",
        )
        .order_by(Assessment.assessed_on)
    ).all()

    quiz_by_month = defaultdict(list)
    for q in all_quizzes:
        m_key = q.assessed_on.strftime("%Y-%m")
        if q.max_score > 0:
            quiz_by_month[m_key].append(float((q.score / q.max_score) * 100.0))

    quiz_monthly_means = []
    for m_key in sorted(quiz_by_month.keys()):
        vals = quiz_by_month[m_key]
        if vals:
            quiz_monthly_means.append(float(np.mean(vals)))

    if len(quiz_monthly_means) >= 2:
        recent_quiz = quiz_monthly_means[-6:]
        x = np.arange(len(recent_quiz))
        slope, _ = np.polyfit(x, recent_quiz, deg=1)
        quiz_trend = float(slope)
    else:
        quiz_trend = 0.0

    features = {
        "attendance_pct": round(float(np.clip(overall_att, 0.0, 100.0)), 2),
        "quiz_avg": round(float(np.clip(overall_quiz, 0.0, 100.0)), 2),
        "assignment_pct": round(float(np.clip(overall_assign, 0.0, 100.0)), 2),
        "internal_marks": round(float(np.clip(overall_internal, 0.0, 30.0)), 2),
        "practical_marks": round(float(np.clip(overall_practical, 0.0, 30.0)), 2),
        "backlogs": float(np.clip(backlogs, 0, 6)),
        "prev_sgpa": round(float(np.clip(prev_sgpa, 0.0, 10.0)), 2),
        "sgpa_delta": round(float(np.clip(sgpa_delta, -5.0, 5.0)), 2),
        "attendance_trend": round(float(np.clip(attendance_trend, -30.0, 30.0)), 2),
        "quiz_trend": round(float(np.clip(quiz_trend, -30.0, 30.0)), 2),
    }

    return features
