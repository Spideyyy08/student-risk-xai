"""
SHAP Explanation Stability Assessment.
Evaluates ranking consistency across bootstrap resamples using Spearman rank correlation.
Includes both explanation resampling and model retraining stability.
"""

from typing import Dict, Any, List
import numpy as np
from scipy.stats import spearmanr
from sklearn.base import clone
import shap
from ml_pipeline.src.explain_shap import to_class_matrix
from ml_pipeline.config import RANDOM_STATE, FEATURES


def evaluate_shap_stability(
    tree_classifier,
    X_imputed: np.ndarray,
    n_bootstraps: int = 5,
    sample_size: int = 100,
) -> Dict[str, Any]:
    """
    Computes global feature importance rankings across bootstrap resamples of the explanation set
    and calculates pairwise Spearman rank correlation.
    """
    rng = np.random.RandomState(RANDOM_STATE)
    n_total = len(X_imputed)
    eff_sample_size = min(sample_size, n_total)

    explainer = shap.TreeExplainer(tree_classifier)
    importance_rankings: List[np.ndarray] = []

    for _ in range(n_bootstraps):
        idx = rng.choice(n_total, size=eff_sample_size, replace=True)
        boot_sample = X_imputed[idx]
        raw_shap = explainer.shap_values(boot_sample)
        matrix = to_class_matrix(raw_shap, n_classes=3)
        mean_abs_high = np.mean(np.abs(matrix[:, :, 2]), axis=0)
        importance_rankings.append(mean_abs_high)

    correlations: List[float] = []
    for i in range(n_bootstraps):
        for j in range(i + 1, n_bootstraps):
            corr, _ = spearmanr(importance_rankings[i], importance_rankings[j])
            if not np.isnan(corr):
                correlations.append(float(corr))

    mean_corr = float(np.mean(correlations)) if correlations else 1.0

    return {
        "n_bootstraps": int(n_bootstraps),
        "sample_size_per_bootstrap": int(eff_sample_size),
        "mean_spearman_rank_correlation": round(mean_corr, 4),
        "min_spearman_rank_correlation": round(float(np.min(correlations)), 4) if correlations else 1.0,
        "pairwise_correlations": [round(c, 4) for c in correlations],
        "is_stable": bool(mean_corr >= 0.85),
    }


def evaluate_retrain_stability(
    pipeline,
    X_train: np.ndarray,
    y_train_int: np.ndarray,
    n_bootstraps: int = 5,
    eval_size: int = 150,
) -> Dict[str, Any]:
    """
    Re-fits the model on 5 bootstrap resamples of training data and compares global SHAP rankings
    (as described in synopsis reference [5]).
    """
    rng = np.random.RandomState(RANDOM_STATE)
    n_train = len(X_train)
    eval_indices = rng.choice(n_train, size=min(eval_size, n_train), replace=False)
    X_eval = X_train[eval_indices]

    rankings: List[np.ndarray] = []

    for b in range(n_bootstraps):
        boot_idx = rng.choice(n_train, size=n_train, replace=True)
        pipe_clone = clone(pipeline)
        # Avoid thread spawning overhead in loops
        clf = pipe_clone.named_steps["classifier"]
        if hasattr(clf, "n_jobs"):
            clf.n_jobs = 1

        pipe_clone.fit(X_train[boot_idx], y_train_int[boot_idx])
        fitted_clf = pipe_clone.named_steps["classifier"]
        imputed_eval = pipe_clone.named_steps["preprocessor"].transform(X_eval)

        explainer = shap.TreeExplainer(fitted_clf)
        raw_shap = explainer.shap_values(imputed_eval)
        matrix = to_class_matrix(raw_shap, n_classes=3)
        mean_abs_high = np.mean(np.abs(matrix[:, :, 2]), axis=0)
        rankings.append(mean_abs_high)

    correlations: List[float] = []
    for i in range(n_bootstraps):
        for j in range(i + 1, n_bootstraps):
            corr, _ = spearmanr(rankings[i], rankings[j])
            if not np.isnan(corr):
                correlations.append(float(corr))

    mean_corr = float(np.mean(correlations)) if correlations else 1.0

    return {
        "n_bootstraps": int(n_bootstraps),
        "mean_spearman_rank_correlation": round(mean_corr, 4),
        "pairwise_correlations": [round(c, 4) for c in correlations],
        "is_retrain_stable": bool(mean_corr >= 0.80),
    }
