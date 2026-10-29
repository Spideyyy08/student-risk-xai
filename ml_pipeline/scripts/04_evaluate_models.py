"""
Evaluate deployed model on held-out test split.
Outputs comprehensive metrics, confusion matrix plot, fairness audit, and resource benchmarks.
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

from sklearn.model_selection import train_test_split
from ml_pipeline.config import RANDOM_STATE, MODEL_DIR
from ml_pipeline.src.data_loader import load_synthetic_dataset
from ml_pipeline.src.predict import load_model_pipeline
from ml_pipeline.src.evaluate_models import evaluate_pipeline


def main():
    print("Executing comprehensive model evaluation on test split...")
    pipeline = load_model_pipeline()

    meta_path = MODEL_DIR / "metadata.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"Missing metadata.json at {meta_path}")

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    X, y, audit_df = load_synthetic_dataset()
    X_train, X_test, y_train, y_test, audit_train, audit_test = train_test_split(
        X, y, audit_df, test_size=0.20, random_state=RANDOM_STATE, stratify=y
    )

    fit_time = meta.get("fit_time_seconds", 1.0)
    cv_results = meta.get("cv_results", {})

    metrics = evaluate_pipeline(
        pipeline=pipeline,
        X_test=X_test,
        y_test=y_test,
        audit_test=audit_test,
        cv_results=cv_results,
        fit_time_seconds=fit_time,
        train_size=len(X_train),
    )

    print("\n--- MODEL EVALUATION SUMMARY ---")
    print(f"Algorithm Selected:       {meta.get('algorithm')}")
    print(f"Accuracy:                 {metrics['accuracy']:.4f}")
    print(f"Macro Precision:          {metrics['macro_precision']:.4f}")
    print(f"Macro Recall:             {metrics['macro_recall']:.4f}")
    print(f"Macro F1-Score:           {metrics['macro_f1']:.4f}")
    print(f"High-as-Low Error Rate:   {metrics['high_as_low_rate']:.4f} ({metrics['high_as_low_count']}/{metrics['actual_high_count']} students)")
    print("\nPer-Class Breakdown:")
    for cls_name, vals in metrics["per_class"].items():
        print(f"  {cls_name:8s} Precision: {vals['precision']:.4f} | Recall: {vals['recall']:.4f} | F1: {vals['f1_score']:.4f} | Support: {vals['support']}")

    print("\nReports successfully written to artifacts/reports/")


if __name__ == "__main__":
    main()
