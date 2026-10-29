"""
Model Evaluation and Fairness Reporting.
Computes comprehensive metrics for both plain argmax and decide_risk rules,
confusion matrix, High-as-Low error rates, fairness audits (null on zero denominator),
and single-row latency benchmarks with n_jobs=1.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
)
from sklearn.pipeline import Pipeline

from ml_pipeline.config import CLASSES, REPORT_DIR, FEATURES, IDX_TO_CLASS, CLASS_TO_IDX
from ml_pipeline.src.label_generation import decide_risk


def evaluate_pipeline(
    pipeline: Pipeline,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    audit_test: pd.DataFrame,
    cv_results: Dict[str, Any],
    fit_time_seconds: float,
    train_size: int,
) -> Dict[str, Any]:
    """
    Run full evaluation on held-out test split.
    y_test may be integer (0,1,2) or string ('Low','Medium','High').
    Evaluates both 'argmax' and 'decide_risk' rules.
    """
    if y_test.dtype == object or isinstance(y_test.iloc[0], str):
        y_true_str = np.array(y_test)
        y_true_int = np.array([CLASS_TO_IDX[s] for s in y_true_str])
    else:
        y_true_int = np.array(y_test)
        y_true_str = np.array([IDX_TO_CLASS[i] for i in y_true_int])

    y_prob = pipeline.predict_proba(X_test)  # col 0: Low, col 1: Medium, col 2: High

    # Rule 1: Plain Argmax
    argmax_pred_int = np.argmax(y_prob, axis=1)
    argmax_pred_str = np.array([IDX_TO_CLASS[i] for i in argmax_pred_int])

    # Rule 2: decide_risk (early intervention sensitive, p_high >= 0.40)
    decide_pred_str = []
    for prob in y_prob:
        risk, _, _ = decide_risk(prob)
        decide_pred_str.append(risk)
    decide_pred_str = np.array(decide_pred_str)

    def calc_metrics(y_pred):
        acc = float(accuracy_score(y_true_str, y_pred))
        p_m, r_m, f1_m, _ = precision_recall_fscore_support(y_true_str, y_pred, average="macro", zero_division=0)
        p_c, r_c, f1_c, sup_c = precision_recall_fscore_support(y_true_str, y_pred, labels=CLASSES, zero_division=0)

        cm = confusion_matrix(y_true_str, y_pred, labels=CLASSES)
        cm_list = [[int(cell) for cell in row] for row in cm]

        actual_high = int(np.sum(y_true_str == "High"))
        high_as_low = int(np.sum((y_true_str == "High") & (y_pred == "Low")))
        hal_rate = float(high_as_low / actual_high) if actual_high > 0 else 0.0

        per_cls = {}
        for idx, c in enumerate(CLASSES):
            per_cls[c] = {
                "precision": round(float(p_c[idx]), 4),
                "recall": round(float(r_c[idx]), 4),
                "f1_score": round(float(f1_c[idx]), 4),
                "support": int(sup_c[idx]),
            }

        return {
            "accuracy": round(acc, 4),
            "macro_precision": round(float(p_m), 4),
            "macro_recall": round(float(r_m), 4),
            "macro_f1": round(float(f1_m), 4),
            "high_as_low_count": high_as_low,
            "actual_high_count": actual_high,
            "high_as_low_rate": round(hal_rate, 4),
            "per_class": per_cls,
            "confusion_matrix": cm_list,
        }

    metrics_decide = calc_metrics(decide_pred_str)
    metrics_argmax = calc_metrics(argmax_pred_str)

    combined_metrics = {
        "decide_risk_rule": metrics_decide,
        "argmax_rule": metrics_argmax,
        # Default top-level fields reference deployed decide_risk rule
        "accuracy": metrics_decide["accuracy"],
        "macro_precision": metrics_decide["macro_precision"],
        "macro_recall": metrics_decide["macro_recall"],
        "macro_f1": metrics_decide["macro_f1"],
        "high_as_low_count": metrics_decide["high_as_low_count"],
        "actual_high_count": metrics_decide["actual_high_count"],
        "high_as_low_rate": metrics_decide["high_as_low_rate"],
        "per_class": metrics_decide["per_class"],
        "confusion_matrix": metrics_decide["confusion_matrix"],
        "classes": CLASSES,
    }

    metrics_path = REPORT_DIR / "metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(combined_metrics, f, indent=2)

    # Comparison CSV
    comparison_rows = []
    for model_name, res in cv_results.items():
        comparison_rows.append({
            "Model": model_name,
            "CV_Macro_F1": res["mean_f1_macro"],
            "CV_F1_Std": res["std_f1_macro"],
            "CV_Train_Time_Sec": res["train_time_sec"],
        })
    comp_df = pd.DataFrame(comparison_rows)
    comp_path = REPORT_DIR / "model_comparison.csv"
    comp_df.to_csv(comp_path, index=False)

    # Confusion matrix plot (for deployed decide_risk)
    cm = np.array(metrics_decide["confusion_matrix"])
    fig, ax = plt.subplots(figsize=(6, 5))
    cax = ax.matshow(cm, cmap=plt.cm.Blues, alpha=0.8)
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(x=j, y=i, s=str(cm[i, j]), va="center", ha="center", size="large")
    fig.colorbar(cax)
    ax.set_xticks([0, 1, 2])
    ax.set_yticks([0, 1, 2])
    ax.set_xticklabels(CLASSES)
    ax.set_yticklabels(CLASSES)
    ax.set_xlabel("Predicted Label (decide_risk)")
    ax.set_ylabel("True Label")
    ax.set_title("Confusion Matrix - Student Risk Classification")
    plt.tight_layout()
    cm_plot_path = REPORT_DIR / "confusion_matrix.png"
    plt.savefig(cm_plot_path, dpi=150)
    plt.close()

    # Fairness report: high_class_recall is None if actual High count is 0
    fairness_data: Dict[str, Any] = {"by_division": {}, "by_gender": {}}
    eval_df = audit_test.copy()
    eval_df["y_true"] = y_true_str
    eval_df["y_pred"] = decide_pred_str

    if "division" in eval_df.columns:
        for div, group in eval_df.groupby("division"):
            div_acc = float(accuracy_score(group["y_true"], group["y_pred"]))
            div_high_true = int(np.sum(group["y_true"] == "High"))
            div_high_pred = int(np.sum((group["y_true"] == "High") & (group["y_pred"] == "High")))
            div_recall = round(float(div_high_pred / div_high_true), 4) if div_high_true > 0 else None
            fairness_data["by_division"][str(div)] = {
                "total_students": len(group),
                "accuracy": round(div_acc, 4),
                "high_class_recall": div_recall,
                "high_class_count": div_high_true,
            }

    if "gender" in eval_df.columns:
        for g, group in eval_df.groupby("gender"):
            g_acc = float(accuracy_score(group["y_true"], group["y_pred"]))
            g_high_true = int(np.sum(group["y_true"] == "High"))
            g_high_pred = int(np.sum((group["y_true"] == "High") & (group["y_pred"] == "High")))
            g_recall = round(float(g_high_pred / g_high_true), 4) if g_high_true > 0 else None
            fairness_data["by_gender"][str(g)] = {
                "total_students": len(group),
                "accuracy": round(g_acc, 4),
                "high_class_recall": g_recall,
                "high_class_count": g_high_true,
            }

    fairness_path = REPORT_DIR / "fairness_report.json"
    with open(fairness_path, "w", encoding="utf-8") as f:
        json.dump(fairness_data, f, indent=2)

    # Latency benchmark
    latencies = []
    sample_row = X_test.iloc[0:1]
    for _ in range(10):
        pipeline.predict_proba(sample_row)

    for i in range(min(200, len(X_test))):
        row = X_test.iloc[i : i + 1]
        t0 = time.perf_counter()
        pipeline.predict_proba(row)
        lat = (time.perf_counter() - t0) * 1000.0
        latencies.append(lat)

    mean_lat = float(np.mean(latencies))
    p95_lat = float(np.percentile(latencies, 95))

    resource_data = {
        "dataset_rows_train": int(train_size),
        "dataset_rows_test": int(len(X_test)),
        "train_time_seconds": round(float(fit_time_seconds), 3),
        "single_row_prediction_latency_ms": {
            "mean": round(mean_lat, 2),
            "p95": round(p95_lat, 2),
            "min": round(float(np.min(latencies)), 2),
            "max": round(float(np.max(latencies)), 2),
        },
    }

    res_path = REPORT_DIR / "resource_usage.json"
    with open(res_path, "w", encoding="utf-8") as f:
        json.dump(resource_data, f, indent=2)

    return combined_metrics
