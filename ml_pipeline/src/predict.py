"""
Model Inference and Scoring Interface.
Loads trained artifacts and computes probability distributions and risk classifications.
Ensures class consistency (0=Low, 1=Medium, 2=High) and safe missing value handling.
"""

from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import functools
import json
import logging
import platform
import numpy as np
import pandas as pd
import joblib
import sklearn
import shap

from ml_pipeline.config import MODEL_DIR, FEATURES, CLASSES
from ml_pipeline.src.label_generation import decide_risk

logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=4)
def load_model_pipeline(model_path: Optional[str] = None):
    """
    Load trained scikit-learn Pipeline artifact specified by metadata.json or explicit path.
    Cached in memory, verifies integer class ordering [0, 1, 2], and sets n_jobs=1 for low latency.
    """
    meta_path = MODEL_DIR / "metadata.json"
    if model_path:
        target_path = Path(model_path)
    elif meta_path.exists():
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            version = meta.get("version", "v1")
            target_path = MODEL_DIR / f"risk_model_{version}.joblib"
            # Compare library versions
            deps = meta.get("dependencies", {})
            curr_sklearn = sklearn.__version__
            curr_shap = shap.__version__
            if deps.get("sklearn") and deps["sklearn"] != curr_sklearn:
                logger.warning(
                    f"scikit-learn version mismatch: model trained on {deps['sklearn']}, current is {curr_sklearn}"
                )
            if deps.get("shap") and deps["shap"] != curr_shap:
                logger.warning(
                    f"shap version mismatch: model trained on {deps['shap']}, current is {curr_shap}"
                )
        except Exception:
            target_path = MODEL_DIR / "risk_model_v1.joblib"
    else:
        target_path = MODEL_DIR / "risk_model_v1.joblib"

    if not target_path.exists():
        raise FileNotFoundError(
            f"Model artifact not found at {target_path}. Run: python ml_pipeline/scripts/03_train_models.py"
        )

    pipeline = joblib.load(target_path)

    # Validate classifier class ordering
    clf = pipeline.named_steps["classifier"]
    if hasattr(clf, "classes_"):
        classes_arr = list(clf.classes_)
        if classes_arr != [0, 1, 2]:
            raise ValueError(
                f"Classifier class ordering mismatch! Expected [0, 1, 2] corresponding to [Low, Medium, High], got {classes_arr}"
            )
        # Fix 9: Set n_jobs = 1 for low single-row latency on Windows
        if hasattr(clf, "n_jobs"):
            clf.n_jobs = 1

    return pipeline


def predict_single_student(
    pipeline,
    feature_dict: Dict[str, Any],
) -> Tuple[str, Dict[str, float], bool]:
    """
    Score a single student feature dictionary.
    Handles missing values via np.nan (imputer), but raises ValueError if > 2 features are missing.
    Class order: 0=Low, 1=Medium, 2=High.
    """
    missing_count = sum(1 for feat in FEATURES if feat not in feature_dict or feature_dict[feat] is None)
    if missing_count > 2:
        raise ValueError(
            f"Too many missing features ({missing_count} missing out of {len(FEATURES)}). Maximum permitted missing is 2."
        )

    row_vals = []
    for feat in FEATURES:
        val = feature_dict.get(feat, None)
        if val is None:
            row_vals.append(np.nan)
        else:
            try:
                row_vals.append(float(val))
            except (ValueError, TypeError):
                row_vals.append(np.nan)

    df = pd.DataFrame([row_vals], columns=FEATURES)
    probs = pipeline.predict_proba(df)[0]
    # probs[0] is Low, probs[1] is Medium, probs[2] is High
    return decide_risk(probs)


def predict_batch_students(
    pipeline,
    features_df: pd.DataFrame,
) -> Tuple[List[str], List[Dict[str, float]], List[bool]]:
    """Score a batch of student rows with integer-encoded class consistency."""
    df = features_df[FEATURES].copy()
    all_probs = pipeline.predict_proba(df)

    risks = []
    norm_probs_list = []
    low_confs = []

    for prob in all_probs:
        risk, norm_probs, low_conf = decide_risk(prob)
        risks.append(risk)
        norm_probs_list.append(norm_probs)
        low_confs.append(low_conf)

    return risks, norm_probs_list, low_confs
