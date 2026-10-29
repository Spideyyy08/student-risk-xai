"""
ML Pipeline Configuration.
Single source of truth for constants, paths, and thresholds.
Windows-safe, deterministic, dialect-neutral.
"""

from pathlib import Path
from typing import List, Dict, Any

RANDOM_STATE: int = 42

# Root directory resolution
PIPELINE_ROOT: Path = Path(__file__).resolve().parent
PROJECT_ROOT: Path = PIPELINE_ROOT.parent

DATA_DIR: Path = PROJECT_ROOT / "data"
SYNTHETIC_DATA_DIR: Path = DATA_DIR / "synthetic"
EXTERNAL_DATA_DIR: Path = DATA_DIR / "external"
RULES_DIR: Path = DATA_DIR / "rules"

ARTIFACT_DIR: Path = PIPELINE_ROOT / "artifacts"
MODEL_DIR: Path = ARTIFACT_DIR / "models"
SHAP_DIR: Path = ARTIFACT_DIR / "shap"
REPORT_DIR: Path = ARTIFACT_DIR / "reports"

# Ensure runtime directories exist
for d in [DATA_DIR, SYNTHETIC_DATA_DIR, EXTERNAL_DATA_DIR, RULES_DIR,
          ARTIFACT_DIR, MODEL_DIR, SHAP_DIR, REPORT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Risk classes and mapping
CLASSES: List[str] = ["Low", "Medium", "High"]
CLASS_TO_IDX: Dict[str, int] = {c: i for i, c in enumerate(CLASSES)}
IDX_TO_CLASS: Dict[int, str] = {i: c for i, c in enumerate(CLASSES)}

# High risk probability threshold for early intervention sensitivity
HIGH_RISK_PROB_THRESHOLD: float = 0.40
LOW_CONFIDENCE_THRESHOLD: float = 0.45

# Feature order (must remain strictly consistent between training, serving, and simulator)
FEATURES: List[str] = [
    "attendance_pct",
    "quiz_avg",
    "assignment_pct",
    "internal_marks",
    "practical_marks",
    "backlogs",
    "prev_sgpa",
    "sgpa_delta",
    "attendance_trend",
    "quiz_trend",
]

# Features that what-if simulator is permitted to override
SIMULATOR_OVERRIDABLE_FEATURES: List[str] = [
    "attendance_pct",
    "quiz_avg",
    "assignment_pct",
    "internal_marks",
    "practical_marks",
    "backlogs",
]

FEATURE_RANGES: Dict[str, Dict[str, float]] = {
    "attendance_pct": {"min": 0.0, "max": 100.0},
    "quiz_avg": {"min": 0.0, "max": 100.0},
    "assignment_pct": {"min": 0.0, "max": 100.0},
    "internal_marks": {"min": 0.0, "max": 30.0},
    "practical_marks": {"min": 0.0, "max": 30.0},
    "backlogs": {"min": 0.0, "max": 6.0},
    "prev_sgpa": {"min": 0.0, "max": 10.0},
    "sgpa_delta": {"min": -5.0, "max": 5.0},
    "attendance_trend": {"min": -30.0, "max": 30.0},
    "quiz_trend": {"min": -30.0, "max": 30.0},
}
