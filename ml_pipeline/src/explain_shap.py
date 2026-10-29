"""
SHAP Explainability Module for Tree Models.
Normalizes SHAP values across tree library versions and formats human-readable factors.
"""

from typing import List, Dict, Any, Union, Tuple
import numpy as np
import shap
from ml_pipeline.config import FEATURES, CLASSES
from ml_pipeline.src.feature_engineering import FEATURE_META, format_feature_value, get_feature_detail


def to_class_matrix(raw: Union[List[np.ndarray], np.ndarray], n_classes: int = 3) -> np.ndarray:
    """
    Normalizes shap_values output across shap versions.
    Older versions return a list of arrays [shape: (n_samples, n_features)] of length n_classes.
    Newer versions return a single 3D array [shape: (n_samples, n_features, n_classes)].
    Returns unified 3D numpy array of shape (n_samples, n_features, n_classes).
    """
    if isinstance(raw, list):
        # List of n_classes arrays with shape (n_samples, n_features)
        # Stack along axis 2 so shape becomes (n_samples, n_features, n_classes)
        return np.stack(raw, axis=-1)
    elif isinstance(raw, np.ndarray):
        if raw.ndim == 3:
            return raw
        elif raw.ndim == 2:
            # Single sample 2D or binary classification
            if raw.shape[1] == len(FEATURES) and n_classes == 1:
                return np.expand_dims(raw, axis=-1)
            raise ValueError(f"Unexpected 2D shap array shape {raw.shape} for multi-class classification.")
        else:
            raise ValueError(f"Unsupported SHAP array dimensions: {raw.ndim}")
    else:
        raise TypeError(f"Unsupported SHAP values type: {type(raw)}")


def extract_base_value(explainer: Any, class_idx: int = 2) -> float:
    """
    Extract expected base value for specified class index (2 = High risk).
    Handles scalar, 1D array/list, or ndarray.
    """
    ev = explainer.expected_value
    if isinstance(ev, (list, np.ndarray)):
        val = ev[class_idx]
    else:
        val = ev
    return float(val)


def explain_instance(
    explainer: Any,
    preprocessed_row: np.ndarray,
    raw_feature_dict: Dict[str, Any],
    top_n: int = 6,
    class_idx: int = 2,
) -> Tuple[float, List[Dict[str, Any]]]:
    """
    Generate SHAP explanation for a single student row.
    preprocessed_row: 2D array (1, n_features) matching tree model inputs.
    raw_feature_dict: Dictionary with raw feature values before preprocessing.
    Returns:
        base_value: float (expected probability for High risk)
        factors: List[Dict] sorted by abs(shap) descending, capped at top_n
            Each factor: {feature, label, value, shap, detail}
    """
    raw_shap = explainer.shap_values(preprocessed_row)
    matrix = to_class_matrix(raw_shap, n_classes=len(CLASSES))  # (1, n_features, 3)

    # Class 2 is High risk: positive shap means increases risk
    high_shap = matrix[0, :, class_idx]
    base_val = extract_base_value(explainer, class_idx=class_idx)

    factors: List[Dict[str, Any]] = []
    for idx, feat_name in enumerate(FEATURES):
        raw_val = raw_feature_dict.get(feat_name, 0.0)
        shap_val = float(high_shap[idx])
        meta = FEATURE_META.get(feat_name, {})
        label = meta.get("label", feat_name)
        val_str = format_feature_value(feat_name, raw_val)
        detail_str = get_feature_detail(feat_name, raw_val, shap_val)

        factors.append({
            "feature": feat_name,
            "label": label,
            "value": val_str,
            "shap": round(float(shap_val), 4),
            "detail": detail_str,
        })

    # Sort by absolute SHAP descending
    factors.sort(key=lambda x: abs(x["shap"]), reverse=True)
    selected_factors = factors[:top_n]

    return round(float(base_val), 4), selected_factors
