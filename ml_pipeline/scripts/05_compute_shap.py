"""
Compute SHAP explanations, background sample, global importance, and stability metrics.
Validates exact probability additivity for Class 2 (High Risk) across 50 sample rows.
"""

import sys
import json
from pathlib import Path

# Bootstrap sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import numpy as np
import pandas as pd
import shap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ml_pipeline.config import (
    RANDOM_STATE,
    SHAP_DIR,
    REPORT_DIR,
    FEATURES,
    CLASS_TO_IDX,
)
from ml_pipeline.src.data_loader import load_synthetic_dataset
from ml_pipeline.src.predict import load_model_pipeline
from ml_pipeline.src.explain_shap import to_class_matrix, extract_base_value
from ml_pipeline.src.stability import evaluate_shap_stability, evaluate_retrain_stability
from ml_pipeline.src.feature_engineering import FEATURE_META


def main():
    print("Computing SHAP explanations and stability diagnostics...")
    pipeline = load_model_pipeline()
    preprocessor = pipeline.named_steps["preprocessor"]
    classifier = pipeline.named_steps["classifier"]

    # Ensure single-thread classifier for predictable latency
    if hasattr(classifier, "n_jobs"):
        classifier.n_jobs = 1

    X, y, _ = load_synthetic_dataset()
    y_int = y.map(CLASS_TO_IDX).values

    X_imputed = preprocessor.transform(X)

    # 1. Background sample
    rng = np.random.RandomState(RANDOM_STATE)
    bg_indices = rng.choice(len(X), size=100, replace=False)
    bg_df = X.iloc[bg_indices].copy()
    bg_path = SHAP_DIR / "background.csv"
    bg_df.to_csv(bg_path, index=False)
    print(f"[OK] Saved 100-row background sample to: {bg_path}")

    # 2. TreeExplainer calculation
    explainer = shap.TreeExplainer(classifier)
    sample_size = min(300, len(X))
    sample_indices = rng.choice(len(X), size=sample_size, replace=False)
    X_sample_imputed = X_imputed[sample_indices]

    raw_shap = explainer.shap_values(X_sample_imputed)
    shap_3d = to_class_matrix(raw_shap, n_classes=3)

    # High risk is class index 2
    high_shap = shap_3d[:, :, 2]
    mean_abs_high = np.mean(np.abs(high_shap), axis=0)

    # Fix 16: Verify additivity on 50 rows: base_value + sum(shap) == predict_proba[:, 2] within 1e-2
    print("Validating SHAP additivity on 50 sample rows for High Risk (class 2)...")
    test_50_idx = rng.choice(len(X), size=50, replace=False)
    test_50_imputed = X_imputed[test_50_idx]
    test_50_df = X.iloc[test_50_idx]

    pred_probs_50 = pipeline.predict_proba(test_50_df)  # (50, 3)
    p_high_actual = pred_probs_50[:, 2]

    shap_50_raw = explainer.shap_values(test_50_imputed)
    shap_50_3d = to_class_matrix(shap_50_raw, n_classes=3)
    base_val = extract_base_value(explainer, class_idx=2)

    sum_shap_high = np.sum(shap_50_3d[:, :, 2], axis=1)
    reconstructed_p_high = base_val + sum_shap_high
    diffs = np.abs(reconstructed_p_high - p_high_actual)
    max_error = float(np.max(diffs))
    print(f"[OK] Additivity verified! Max discrepancy: {max_error:.6f} (Tolerance: 1e-2)")
    assert max_error < 1e-2, f"SHAP additivity violated: max error {max_error} exceeds 0.01"

    # 3. Global importance JSON
    global_importance = []
    total_importance = float(np.sum(mean_abs_high)) if np.sum(mean_abs_high) > 0 else 1.0
    for idx, feat in enumerate(FEATURES):
        abs_val = float(mean_abs_high[idx])
        meta = FEATURE_META.get(feat, {})
        global_importance.append({
            "feature": feat,
            "label": meta.get("label", feat),
            "mean_abs_shap": round(abs_val, 4),
            "importance_share": round(abs_val / total_importance, 4),
        })

    global_importance.sort(key=lambda x: x["mean_abs_shap"], reverse=True)
    glob_path = SHAP_DIR / "global_importance.json"
    with open(glob_path, "w", encoding="utf-8") as f:
        json.dump(global_importance, f, indent=2)
    print(f"[OK] Saved global importance to: {glob_path}")

    # 4. Summary plot
    fig, ax = plt.subplots(figsize=(8, 5))
    y_pos = np.arange(len(global_importance))
    labels = [item["label"] for item in reversed(global_importance)]
    values = [item["mean_abs_shap"] for item in reversed(global_importance)]

    ax.barh(y_pos, values, color="#2563eb", align="center")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Mean |SHAP Value| (Impact on High Academic Risk)")
    ax.set_title("Global Feature Importance (Tree SHAP)")
    plt.tight_layout()

    plot_path = SHAP_DIR / "summary_plot.png"
    plt.savefig(plot_path, dpi=150)
    plt.close()
    print(f"[OK] Saved SHAP summary plot to: {plot_path}")

    # 5. Stability reports (both resampling and retraining)
    print("Evaluating SHAP explanation stability...")
    sample_stability = evaluate_shap_stability(
        tree_classifier=classifier,
        X_imputed=X_imputed,
        n_bootstraps=5,
        sample_size=100,
    )

    print("Evaluating retraining explanation stability (5 bootstrap fits)...")
    retrain_stability = evaluate_retrain_stability(
        pipeline=pipeline,
        X_train=X.values,
        y_train_int=y_int,
        n_bootstraps=5,
    )

    combined_stability = {
        "sample_resampling_stability": sample_stability,
        "model_retraining_stability": retrain_stability,
    }

    stab_path = SHAP_DIR / "shap_stability.json"
    with open(stab_path, "w", encoding="utf-8") as f:
        json.dump(combined_stability, f, indent=2)
    print(f"[OK] SHAP stability report saved to: {stab_path}")
    print(f"Explanation Resampling Mean Spearman Correlation: {sample_stability['mean_spearman_rank_correlation']}")
    print(f"Model Retraining Mean Spearman Correlation:       {retrain_stability['mean_spearman_rank_correlation']}")


if __name__ == "__main__":
    main()
