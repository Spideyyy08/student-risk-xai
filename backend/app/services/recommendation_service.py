"""
Recommendation Rule Engine Service.
Evaluates academic rules, personalizes actions by subject weaknesses,
orders recommendations by priority and SHAP relevance, and preserves user assigned status.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.recommendation import Recommendation
from app.models.subject import Subject
from app.models.assessment import Assessment


SUBJECT_REMEDIAL_ACTIONS = {
    "DSA": {
        "name": "Data Structures & Algorithms",
        "action": "Complete 5 easy, 5 medium and 5 hard sorting and graph problems",
    },
    "DBMS": {
        "name": "Database Management Systems",
        "action": "Practice normalization and complex SQL join queries on LeetCode/HackerRank",
    },
    "DM": {
        "name": "Discrete Mathematics",
        "action": "Solve 15 problems on propositional logic and combinatorics sets",
    },
    "COA": {
        "name": "Computer Organization & Architecture",
        "action": "Review pipelining hazards and cache memory mapping numerical problems",
    },
    "PYTHON": {
        "name": "Python Programming",
        "action": "Complete OOP and file handling practical exercises",
    },
}


def load_rules() -> List[Dict[str, Any]]:
    path = Path(settings.RULES_FILE_PATH)
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_weakest_subject(db: Session, student_id: int, semester_code: str) -> Optional[Dict[str, Any]]:
    """Find the subject where the student's quiz average is lowest and below 55%."""
    subjects = db.scalars(select(Subject).where(Subject.semester_code == semester_code)).all()
    if not subjects:
        subjects = db.scalars(select(Subject)).all()

    weakest = None
    lowest_avg = 100.0

    for s in subjects:
        quizzes = db.scalars(
            select(Assessment).where(
                Assessment.student_id == student_id,
                Assessment.subject_id == s.id,
                Assessment.kind == "QUIZ",
            )
        ).all()
        if quizzes:
            pcts = [(q.score / q.max_score) * 100.0 for q in quizzes if q.max_score > 0]
            if pcts:
                mean_q = sum(pcts) / len(pcts)
                if mean_q < 55.0 and mean_q < lowest_avg:
                    lowest_avg = mean_q
                    weakest = {
                        "subject_code": s.code,
                        "subject_short": s.short_name,
                        "subject_name": s.name,
                        "quiz_avg": int(round(mean_q)),
                    }

    return weakest


def generate_and_store_recommendations(
    db: Session,
    student_id: int,
    semester_code: str,
    features: Dict[str, float],
    factors: List[Dict[str, Any]],
    prediction_id: Optional[int] = None,
) -> List[Recommendation]:
    """
    Evaluate deterministic rules, merge with existing 'assigned' flags,
    and persist in database.
    """
    rules = load_rules()

    # Pre-map factor SHAP values for sorting relevance
    shap_map = {f["feature"]: abs(float(f.get("shap", 0.0))) for f in factors}

    # Query existing recommendations to preserve 'assigned' state
    existing = db.scalars(
        select(Recommendation).where(
            Recommendation.student_id == student_id,
            Recommendation.semester_code == semester_code,
        )
    ).all()
    assigned_status = {r.rule_id: r.assigned for r in existing}

    candidates = []

    # 1. Subject-specific Quiz Rule for weakest subject
    weakest = find_weakest_subject(db, student_id, semester_code)
    if weakest:
        short = weakest["subject_short"].upper()
        remedial = SUBJECT_REMEDIAL_ACTIONS.get(short, {
            "name": weakest["subject_name"],
            "action": f"Review core concepts and problem sets for {weakest['subject_name']}",
        })
        candidates.append({
            "rule_id": f"RULE_WEAK_SUBJECT_{short}",
            "priority": "High",
            "subject": weakest["subject_name"],
            "action": remedial["action"],
            "reason": f"Quiz average is only {weakest['quiz_avg']}% in {weakest['subject_name']}, indicating concept gaps.",
            "shap_relevance": shap_map.get("quiz_avg", 0.1),
        })

    # 2. General Rules
    for r in rules:
        feat = r.get("feature")
        cond = r.get("condition_type")
        val = features.get(feat, 0.0)
        matched = False

        if cond == "max" and val < r.get("threshold", 0.0):
            matched = True
        elif cond == "min" and val >= r.get("threshold", 0.0):
            matched = True
        elif cond == "range" and r.get("min_threshold", 0.0) <= val < r.get("max_threshold", 100.0):
            matched = True
        elif cond == "equals" and feat == "risk_level":
            # Enrichment rules checked if no High priority rules triggered
            pass

        if matched:
            reason = r["reason"].format(
                attendance_pct=int(round(features.get("attendance_pct", 0.0))),
                internal_marks=int(round(features.get("internal_marks", 0.0))),
                practical_marks=int(round(features.get("practical_marks", 0.0))),
                backlogs=int(round(features.get("backlogs", 0.0))),
                assignment_pct=int(round(features.get("assignment_pct", 0.0))),
                attendance_trend=abs(round(features.get("attendance_trend", 0.0), 1)),
                quiz_trend=abs(round(features.get("quiz_trend", 0.0), 1)),
                sgpa_delta_abs=abs(round(features.get("sgpa_delta", 0.0), 2)),
            )
            candidates.append({
                "rule_id": r["id"],
                "priority": r["priority"],
                "subject": r.get("subject"),
                "action": r["action"],
                "reason": reason,
                "shap_relevance": shap_map.get(feat, 0.0),
            })

    # If low risk (few/no high priority candidates), add enrichment rules
    if not any(c["priority"] == "High" for c in candidates):
        for r in rules:
            if r.get("feature") == "risk_level" and r.get("value") == "Low":
                candidates.append({
                    "rule_id": r["id"],
                    "priority": r["priority"],
                    "subject": r.get("subject"),
                    "action": r["action"],
                    "reason": r["reason"],
                    "shap_relevance": 0.05,
                })

    # Priority ranking helper: High=0, Medium=1, Low=2
    prio_order = {"High": 0, "Medium": 1, "Low": 2}
    candidates.sort(key=lambda c: (prio_order.get(c["priority"], 99), -c["shap_relevance"]))

    # Cap at top 6
    top_candidates = candidates[:6]

    # Delete non-selected older unassigned recommendations
    keep_rule_ids = [c["rule_id"] for c in top_candidates]
    for ex in existing:
        if ex.rule_id not in keep_rule_ids and not ex.assigned:
            db.delete(ex)

    result_objs = []
    for c in top_candidates:
        existing_rec = next((e for e in existing if e.rule_id == c["rule_id"]), None)
        if existing_rec:
            existing_rec.priority = c["priority"]
            existing_rec.subject = c["subject"]
            existing_rec.action = c["action"]
            existing_rec.reason = c["reason"]
            existing_rec.prediction_id = prediction_id
            result_objs.append(existing_rec)
        else:
            new_rec = Recommendation(
                student_id=student_id,
                semester_code=semester_code,
                rule_id=c["rule_id"],
                priority=c["priority"],
                subject=c["subject"],
                action=c["action"],
                reason=c["reason"],
                assigned=assigned_status.get(c["rule_id"], False),
                prediction_id=prediction_id,
            )
            db.add(new_rec)
            result_objs.append(new_rec)

    db.flush()
    return result_objs
