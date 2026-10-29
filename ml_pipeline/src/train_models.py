"""
Model Training and Selection Engine.
Performs 5-fold cross-validation with integer-encoded classes [0=Low, 1=Medium, 2=High],
selects the best tree model, and saves versioned artifacts with strict metadata.
"""

import sys
import time
import platform
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd
import joblib
import sklearn
import shap
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline

from ml_pipeline.config import (
    RANDOM_STATE,
    CLASSES,
    CLASS_TO_IDX,
    IDX_TO_CLASS,
    FEATURES,
    FEATURE_RANGES,
    MODEL_DIR,
)
from ml_pipeline.src.preprocessing import create_preprocessor

logger = logging.getLogger(__name__)


def build_candidate_pipelines() -> Dict[str, Pipeline]:
    """Create the 3 candidate model pipelines with single-thread estimators for safe CV."""
    lr_pipe = Pipeline([
        ("preprocessor", create_preprocessor(scale=True)),
        ("classifier", LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=RANDOM_STATE,
        )),
    ])

    dt_pipe = Pipeline([
        ("preprocessor", create_preprocessor(scale=False)),
        ("classifier", DecisionTreeClassifier(
            max_depth=6,
            min_samples_leaf=20,
            class_weight="balanced",
            random_state=RANDOM_STATE,
        )),
    ])

    rf_pipe = Pipeline([
        ("preprocessor", create_preprocessor(scale=False)),
        ("classifier", RandomForestClassifier(
            n_estimators=300,
            max_depth=10,
            min_samples_leaf=5,
            class_weight="balanced_subsample",
            n_jobs=1,
            random_state=RANDOM_STATE,
        )),
    ])

    return {
        "LogisticRegression": lr_pipe,
        "DecisionTree": dt_pipe,
        "RandomForest": rf_pipe,
    }


def train_and_select_model(
    X: pd.DataFrame,
    y: pd.Series,
    version: str = "v1",
) -> Tuple[Pipeline, str, Dict[str, Any]]:
    """
    Evaluates candidate models via 5-fold Stratified CV using integer target labels [0, 1, 2],
    selects best tree model, fits on training split, and saves artifacts with metadata.
    """
    # Fix 1: Map string labels to integer classes (0=Low, 1=Medium, 2=High)
    if y.dtype == object or isinstance(y.iloc[0], str):
        y_int = y.map(CLASS_TO_IDX).astype(int)
    else:
        y_int = y.astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_int, test_size=0.20, random_state=RANDOM_STATE, stratify=y_int
    )

    candidates = build_candidate_pipelines()
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)

    cv_results: Dict[str, Dict[str, Any]] = {}
    print("Evaluating candidate models with 5-fold Stratified Cross-Validation (classes: 0=Low, 1=Medium, 2=High)...")

    for name, pipe in candidates.items():
        t0 = time.perf_counter()
        scores = cross_val_score(pipe, X_train, y_train, cv=cv, scoring="f1_macro", n_jobs=-1)
        elapsed = time.perf_counter() - t0
        mean_score = float(np.mean(scores))
        std_score = float(np.std(scores))
        cv_results[name] = {
            "mean_f1_macro": round(mean_score, 4),
            "std_f1_macro": round(std_score, 4),
            "train_time_sec": round(elapsed, 3),
        }
        print(f"  {name:20s} Macro-F1: {mean_score:.4f} (+/- {std_score:.4f})  [Time: {elapsed:.2f}s]")

    dt_score = cv_results["DecisionTree"]["mean_f1_macro"]
    rf_score = cv_results["RandomForest"]["mean_f1_macro"]

    if rf_score >= dt_score or abs(rf_score - dt_score) <= 0.01:
        best_name = "RandomForest"
        best_score = rf_score
    else:
        best_name = "DecisionTree"
        best_score = dt_score

    # Fix 8: Check and warn on signal leakage or underfitting
    if best_score > 0.95:
        print(f"[WARNING] 5-fold CV Macro-F1 ({best_score:.4f}) is above 0.95. Features may be leaking label information!")
    elif best_score < 0.70:
        print(f"[WARNING] 5-fold CV Macro-F1 ({best_score:.4f}) is below 0.70. Underfitting detected!")

    print(f"\nSelected deployable tree model: {best_name}")

    best_pipe = candidates[best_name]
    fit_t0 = time.perf_counter()
    best_pipe.fit(X_train, y_train)
    fit_time = time.perf_counter() - fit_t0

    # Ensure n_jobs=1 on fitted model for Windows thread performance
    clf = best_pipe.named_steps["classifier"]
    if hasattr(clf, "n_jobs"):
        clf.n_jobs = 1

    # Verify classes are exactly [0, 1, 2]
    classes_list = list(clf.classes_)
    assert classes_list == [0, 1, 2], f"Expected classes [0, 1, 2], got {classes_list}"

    model_filename = f"risk_model_{version}.joblib"
    model_path = MODEL_DIR / model_filename
    joblib.dump(best_pipe, model_path)
    print(f"Saved trained pipeline to: {model_path}")

    metadata = {
        "version": version,
        "algorithm": best_name,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "classes": CLASSES,
        "class_order": [0, 1, 2],
        "class_mapping": CLASS_TO_IDX,
        "feature_names": FEATURES,
        "feature_ranges": {k: {"min": float(v["min"]), "max": float(v["max"])} for k, v in FEATURE_RANGES.items()},
        "cv_results": cv_results,
        "fit_time_seconds": round(fit_time, 3),
        "train_rows": len(X_train),
        "test_rows": len(X_test),
        "dependencies": {
            "python": platform.python_version(),
            "sklearn": sklearn.__version__,
            "shap": shap.__version__,
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "joblib": joblib.__version__,
        },
    }

    meta_path = MODEL_DIR / "metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved model metadata to: {meta_path}")

    return best_pipe, best_name, {
        "X_train": X_train,
        "X_test": X_test,
        "y_train": y_train,
        "y_test": y_test,
        "cv_results": cv_results,
        "metadata": metadata,
    }
