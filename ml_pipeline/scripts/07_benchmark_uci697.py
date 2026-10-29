"""
Benchmark on Real-world UCI 697 Dataset (Student Dropout & Academic Success).
Applies academic-only feature filtering, integer-encoded classes (0=Low, 1=Medium, 2=High),
confusion matrix visualization, and Tree SHAP attribution.
"""

import sys
import json
import subprocess
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
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

from ml_pipeline.config import EXTERNAL_DATA_DIR, REPORT_DIR, RANDOM_STATE, CLASS_TO_IDX, IDX_TO_CLASS, CLASSES
from ml_pipeline.src.explain_shap import to_class_matrix


def run_uci697_benchmark():
    csv_path = EXTERNAL_DATA_DIR / "uci697_dropout_success.csv"
    if not csv_path.exists():
        print(f"Dataset not found at {csv_path}. Running 00_download_public_datasets.py...")
        subprocess.run([sys.executable, str(SCRIPT_DIR / "00_download_public_datasets.py")], check=True)

    df = pd.read_csv(csv_path)
    print(f"Loaded UCI 697 dataset: {len(df)} rows.")

    target_col = "Target"
    if target_col not in df.columns:
        raise ValueError("Missing 'Target' column in UCI 697 dataset.")

    # Target proxy mapping: Dropout -> High Risk, Enrolled -> Medium Risk, Graduate -> Low Risk
    mapping = {
        "Dropout": "High",
        "Enrolled": "Medium",
        "Graduate": "Low",
    }
    y_str = df[target_col].astype(str).map(mapping)
    valid_mask = y_str.notna()
    y_str = y_str[valid_mask]
    y_int = y_str.map(CLASS_TO_IDX).values.astype(int)  # 0=Low, 1=Medium, 2=High

    df_valid = df.loc[valid_mask].copy()

    # Fix 14: Filter strictly to academic, performance, and enrollment features
    # Exclude demographic/protected attributes (gender, marital status, nationality, parents' data)
    candidate_academic_cols = [
        "Curricular_units_1st_sem_credited", "Curricular_units_1st_sem_enrolled",
        "Curricular_units_1st_sem_evaluations", "Curricular_units_1st_sem_approved",
        "Curricular_units_1st_sem_grade", "Curricular_units_1st_sem_without_evaluations",
        "Curricular_units_2nd_sem_credited", "Curricular_units_2nd_sem_enrolled",
        "Curricular_units_2nd_sem_evaluations", "Curricular_units_2nd_sem_approved",
        "Curricular_units_2nd_sem_grade", "Curricular_units_2nd_sem_without_evaluations",
        "Admission_grade", "Previous_qualification_grade",
        "Age_at_enrollment", "Tuition_fees_up_to_date", "Scholarship_holder", "Debtor",
    ]

    # Normalize column names to match potential spaces or underscores
    col_mapping = {c.replace(" ", "_").replace("'", ""): c for c in df_valid.columns}
    selected_cols = []
    for cand in candidate_academic_cols:
        if cand in df_valid.columns:
            selected_cols.append(cand)
        elif cand in col_mapping:
            selected_cols.append(col_mapping[cand])

    if not selected_cols:
        # Fallback to any numeric columns that do not contain protected terms
        protected = ["gender", "sex", "marital", "nacionality", "nationality", "mother", "father"]
        selected_cols = [
            c for c in df_valid.select_dtypes(include=[np.number]).columns
            if not any(p in c.lower() for p in protected)
        ]

    print(f"Selected {len(selected_cols)} academic/enrolment features for benchmark:")
    for col in selected_cols[:6]:
        print(f"  - {col}")
    if len(selected_cols) > 6:
        print(f"  ... and {len(selected_cols) - 6} more.")

    X = df_valid[selected_cols].copy()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_int, test_size=0.20, random_state=RANDOM_STATE, stratify=y_int
    )

    models = {
        "LogisticRegression": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=2000, class_weight="balanced", random_state=RANDOM_STATE)),
        ]),
        "DecisionTree": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("clf", DecisionTreeClassifier(max_depth=6, min_samples_leaf=20, class_weight="balanced", random_state=RANDOM_STATE)),
        ]),
        "RandomForest": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("clf", RandomForestClassifier(n_estimators=200, max_depth=10, min_samples_leaf=5, class_weight="balanced_subsample", n_jobs=1, random_state=RANDOM_STATE)),
        ]),
    }

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    cv_scores = {}
    print("\nRunning 5-fold Cross Validation on UCI 697...")
    for name, pipe in models.items():
        scores = cross_val_score(pipe, X_train, y_train, cv=cv, scoring="f1_macro", n_jobs=-1)
        cv_scores[name] = {
            "mean_f1_macro": round(float(np.mean(scores)), 4),
            "std_f1_macro": round(float(np.std(scores)), 4),
        }
        print(f"  {name:20s} Macro-F1: {cv_scores[name]['mean_f1_macro']:.4f} (+/- {cv_scores[name]['std_f1_macro']:.4f})")

    # Fit best tree model (RandomForest)
    best_pipe = models["RandomForest"]
    best_pipe.fit(X_train, y_train)

    y_pred = best_pipe.predict(X_test)
    acc = float(accuracy_score(y_test, y_pred))
    p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(
        y_test, y_pred, average="macro", zero_division=0
    )

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred, labels=[0, 1, 2])
    fig, ax = plt.subplots(figsize=(6, 5))
    cax = ax.matshow(cm, cmap=plt.cm.Greens, alpha=0.8)
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(x=j, y=i, s=str(cm[i, j]), va="center", ha="center", size="large")
    fig.colorbar(cax)
    ax.set_xticks([0, 1, 2])
    ax.set_yticks([0, 1, 2])
    ax.set_xticklabels(CLASSES)
    ax.set_yticklabels(CLASSES)
    ax.set_xlabel("Predicted Label")
    ax.set_ylabel("True Proxy Label")
    ax.set_title("UCI 697 Benchmark - Confusion Matrix")
    plt.tight_layout()
    cm_plot_path = REPORT_DIR / "benchmark_uci697_cm.png"
    plt.savefig(cm_plot_path, dpi=150)
    plt.close()

    # SHAP explanations for High risk (class index 2)
    rf_clf = best_pipe.named_steps["clf"]
    imputer = best_pipe.named_steps["imputer"]
    X_sample = imputer.transform(X_test.iloc[:150])

    explainer = shap.TreeExplainer(rf_clf)
    raw_shap = explainer.shap_values(X_sample)
    shap_3d = to_class_matrix(raw_shap, n_classes=3)

    # Class 2 is High risk (Dropout)
    mean_abs_high = np.mean(np.abs(shap_3d[:, :, 2]), axis=0)

    top_feat_indices = np.argsort(mean_abs_high)[::-1][:10]
    top_features = [{
        "feature": selected_cols[idx],
        "mean_abs_shap": round(float(mean_abs_high[idx]), 4),
    } for idx in top_feat_indices]

    # Plot top SHAP
    fig, ax = plt.subplots(figsize=(8, 5))
    y_pos = np.arange(len(top_features))
    labels = [f["feature"] for f in reversed(top_features)]
    vals = [f["mean_abs_shap"] for f in reversed(top_features)]
    ax.barh(y_pos, vals, color="#059669")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Mean |SHAP Value| (Impact on Dropout/High Risk)")
    ax.set_title("UCI 697 Benchmark - Top Predictive Features")
    plt.tight_layout()
    plot_path = REPORT_DIR / "benchmark_uci697_shap.png"
    plt.savefig(plot_path, dpi=150)
    plt.close()

    benchmark_results = {
        "dataset": "UCI 697 Predict Students Dropout and Academic Success",
        "proxy_mapping": {"Dropout": "High Risk", "Enrolled": "Medium Risk", "Graduate": "Low Risk"},
        "samples": len(df),
        "features_count": len(selected_cols),
        "cv_results": cv_scores,
        "test_metrics": {
            "accuracy": round(acc, 4),
            "macro_precision": round(float(p_macro), 4),
            "macro_recall": round(float(r_macro), 4),
            "macro_f1": round(float(f1_macro), 4),
        },
        "top_predictive_features": top_features,
    }

    out_json = REPORT_DIR / "benchmark_uci697.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(benchmark_results, f, indent=2)

    print(f"\n[SUCCESS] UCI 697 benchmark completed. Results saved to {out_json}")


if __name__ == "__main__":
    run_uci697_benchmark()
