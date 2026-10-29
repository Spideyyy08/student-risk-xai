"""
Single source of truth for feature definitions, metadata, formatting, and details.
Imported by ML training, seed script, API feature service, and what-if simulator.
"""

from typing import Dict, Any, List
from ml_pipeline.config import FEATURES, FEATURE_RANGES, SIMULATOR_OVERRIDABLE_FEATURES

FEATURE_META: Dict[str, Dict[str, Any]] = {
    "attendance_pct": {
        "name": "attendance_pct",
        "label": "Overall Attendance",
        "unit": "%",
        "min": 0.0,
        "max": 100.0,
        "format": lambda val: f"{int(round(float(val)))}%",
        "detail": lambda val: (
            f"Attendance {int(round(float(val)))}% is severely below the 65% mandatory threshold"
            if float(val) < 65.0
            else (
                f"Attendance {int(round(float(val)))}% is borderline (below 75% target)"
                if float(val) < 75.0
                else f"Strong attendance rate at {int(round(float(val)))}%"
            )
        ),
    },
    "quiz_avg": {
        "name": "quiz_avg",
        "label": "Quiz Average",
        "unit": "%",
        "min": 0.0,
        "max": 100.0,
        "format": lambda val: f"{int(round(float(val)))}%",
        "detail": lambda val: (
            f"Low quiz average {int(round(float(val)))}% indicates concept gaps"
            if float(val) < 55.0
            else (
                f"Moderate quiz performance at {int(round(float(val)))}%"
                if float(val) < 70.0
                else f"Consistent quiz performance at {int(round(float(val)))}%"
            )
        ),
    },
    "assignment_pct": {
        "name": "assignment_pct",
        "label": "Assignment Completion",
        "unit": "%",
        "min": 0.0,
        "max": 100.0,
        "format": lambda val: f"{int(round(float(val)))}%",
        "detail": lambda val: (
            f"Assignment submission rate {int(round(float(val)))}% is critically low with missing deliverables"
            if float(val) < 65.0
            else (
                f"Assignment submission rate {int(round(float(val)))}% indicates pending tasks"
                if float(val) < 80.0
                else f"High assignment adherence at {int(round(float(val)))}%"
            )
        ),
    },
    "internal_marks": {
        "name": "internal_marks",
        "label": "Internal Marks (Mid-Sem)",
        "unit": "/30",
        "min": 0.0,
        "max": 30.0,
        "format": lambda val: f"{int(round(float(val)))}/30",
        "detail": lambda val: (
            f"Mid-sem score {int(round(float(val)))}/30 is below passing threshold (14/30)"
            if float(val) < 14.0
            else (
                f"Mid-sem score {int(round(float(val)))}/30 is average"
                if float(val) < 20.0
                else f"Solid mid-term assessment result ({int(round(float(val)))}/30)"
            )
        ),
    },
    "practical_marks": {
        "name": "practical_marks",
        "label": "Practical Marks (Lab Test)",
        "unit": "/30",
        "min": 0.0,
        "max": 30.0,
        "format": lambda val: f"{int(round(float(val)))}/30",
        "detail": lambda val: (
            f"Laboratory assessment {int(round(float(val)))}/30 needs remedial work"
            if float(val) < 16.0
            else (
                f"Practical score {int(round(float(val)))}/30 is satisfactory"
                if float(val) < 22.0
                else f"Strong hands-on lab competence ({int(round(float(val)))}/30)"
            )
        ),
    },
    "backlogs": {
        "name": "backlogs",
        "label": "Active Backlogs",
        "unit": "courses",
        "min": 0.0,
        "max": 6.0,
        "format": lambda val: f"{int(round(float(val)))} backlog(s)" if int(round(float(val))) != 1 else "1 backlog",
        "detail": lambda val: (
            f"Accumulated {int(round(float(val)))} active backlog course(s) from previous term"
            if int(round(float(val))) > 0
            else "Zero standing backlogs, on-track academic progress"
        ),
    },
    "prev_sgpa": {
        "name": "prev_sgpa",
        "label": "Previous SGPA",
        "unit": "/10",
        "min": 0.0,
        "max": 10.0,
        "format": lambda val: f"{float(val):.2f}",
        "detail": lambda val: (
            f"Past semester SGPA was low at {float(val):.2f}"
            if float(val) < 6.0
            else (
                f"Past semester SGPA was moderate at {float(val):.2f}"
                if float(val) < 7.5
                else f"Good prior academic record with SGPA {float(val):.2f}"
            )
        ),
    },
    "sgpa_delta": {
        "name": "sgpa_delta",
        "label": "SGPA Change",
        "unit": "pts",
        "min": -5.0,
        "max": 5.0,
        "format": lambda val: f"{'+' if float(val) >= 0 else ''}{float(val):.2f}",
        "detail": lambda val: (
            f"SGPA dropped by {abs(float(val)):.2f} points between past semesters"
            if float(val) < -0.3
            else (
                f"SGPA remained steady ({'+' if float(val) >= 0 else ''}{float(val):.2f} points)"
                if float(val) <= 0.3
                else f"SGPA increased by {float(val):.2f} points over previous terms"
            )
        ),
    },
    "attendance_trend": {
        "name": "attendance_trend",
        "label": "Attendance Trend",
        "unit": "pts/mo",
        "min": -30.0,
        "max": 30.0,
        "format": lambda val: f"{'+' if float(val) >= 0 else ''}{float(val):.1f} pts/mo",
        "detail": lambda val: (
            f"Attendance declining at {abs(float(val)):.1f} points per month"
            if float(val) < -2.0
            else (
                f"Attendance stable ({'+' if float(val) >= 0 else ''}{float(val):.1f} pts/month)"
                if float(val) <= 2.0
                else f"Attendance improving by {float(val):.1f} points per month"
            )
        ),
    },
    "quiz_trend": {
        "name": "quiz_trend",
        "label": "Quiz Score Trend",
        "unit": "pts/mo",
        "min": -30.0,
        "max": 30.0,
        "format": lambda val: f"{'+' if float(val) >= 0 else ''}{float(val):.1f} pts/mo",
        "detail": lambda val: (
            f"Quiz scores downward trend ({abs(float(val)):.1f} pts/month)"
            if float(val) < -2.0
            else (
                f"Quiz performance steady ({'+' if float(val) >= 0 else ''}{float(val):.1f} pts/month)"
                if float(val) <= 2.0
                else f"Quiz performance upward trend (+{float(val):.1f} pts/month)"
            )
        ),
    },
}


def format_feature_value(feature_name: str, val: Any) -> str:
    """Format numeric feature value for API display."""
    if feature_name in FEATURE_META:
        try:
            return FEATURE_META[feature_name]["format"](val)
        except Exception:
            return str(val)
    return str(val)


def get_feature_detail(feature_name: str, val: Any, shap_value: float = 0.0) -> str:
    """
    Generate human-readable explanation detail from value.
    The text is chosen by value thresholds; SHAP sign determines ranking/color in the UI.
    """
    if feature_name in FEATURE_META:
        try:
            return FEATURE_META[feature_name]["detail"](val)
        except Exception:
            return f"{FEATURE_META[feature_name]['label']}: {val}"
    return f"{feature_name}: {val}"


def compute_key_factor(factors: List[Dict[str, Any]], risk_level: str) -> str:
    """
    Derive the key_factor summary string.
    Returns just the concise detail sentence without redundant label/value prefix.
    """
    if not factors:
        return "Normal overall academic progression"

    if risk_level in ("High", "Medium"):
        risk_raising = [f for f in factors if float(f.get("shap", 0.0)) > 0]
        if risk_raising:
            top = max(risk_raising, key=lambda f: float(f.get("shap", 0.0)))
            return str(top.get("detail", f"{top.get('label')} {top.get('value')}"))

    protective = [f for f in factors if float(f.get("shap", 0.0)) < 0]
    if protective:
        top = min(protective, key=lambda f: float(f.get("shap", 0.0)))
        return str(top.get("detail", f"{top.get('label')} {top.get('value')}"))

    return str(factors[0].get("detail", f"{factors[0].get('label')} {factors[0].get('value')}"))
