"""
Prediction Engine, Decision Boundaries, and SHAP Additivity Tests.
"""

import numpy as np
import pytest
from ml_pipeline.src.label_generation import decide_risk
from ml_pipeline.src.explain_shap import to_class_matrix
from app.services.model_registry import model_bundle


def test_decide_risk_high_threshold():
    # p_high = 0.41 (>= 0.40) -> High
    probs = [0.30, 0.29, 0.41]
    risk, norm, low_conf = decide_risk(probs)
    assert risk == "High"
    assert round(sum(norm.values()), 2) == 1.00


def test_decide_risk_medium_argmax():
    # p_high = 0.35 (< 0.40) -> compare medium vs low
    probs = [0.25, 0.40, 0.35]
    risk, norm, low_conf = decide_risk(probs)
    assert risk == "Medium"
    assert round(sum(norm.values()), 2) == 1.00


def test_decide_risk_low_argmax():
    probs = [0.55, 0.25, 0.20]
    risk, norm, low_conf = decide_risk(probs)
    assert risk == "Low"
    assert round(sum(norm.values()), 2) == 1.00


def test_low_confidence_flag():
    # Max probability 0.38 < 0.45 -> low_confidence = True
    probs = [0.35, 0.38, 0.27]
    risk, norm, low_conf = decide_risk(probs)
    assert low_conf is True


def test_to_class_matrix_list_and_array_shapes():
    n_samples = 5
    n_feats = 10
    n_classes = 3

    # Shape variant 1: list of arrays
    list_shap = [np.ones((n_samples, n_feats)) * c for c in range(n_classes)]
    res1 = to_class_matrix(list_shap, n_classes=n_classes)
    assert res1.shape == (n_samples, n_feats, n_classes)
    assert np.all(res1[:, :, 2] == 2)

    # Shape variant 2: 3D array
    arr_3d = np.zeros((n_samples, n_feats, n_classes))
    res2 = to_class_matrix(arr_3d, n_classes=n_classes)
    assert res2.shape == (n_samples, n_feats, n_classes)


def test_shap_additivity_on_test_model():
    # Assert base_value + sum(shap) == predict_proba[:, 2] within 1e-2
    clf = model_bundle.classifier
    explainer = model_bundle.explainer
    base_val = model_bundle.base_value

    rng = np.random.RandomState(42)
    sample_rows = rng.uniform(20.0, 90.0, size=(10, 10))

    pred_probs = clf.predict_proba(sample_rows)[:, 2]
    raw_shap = explainer.shap_values(sample_rows)
    shap_3d = to_class_matrix(raw_shap, n_classes=3)
    sum_shap = np.sum(shap_3d[:, :, 2], axis=1)

    diffs = np.abs((base_val + sum_shap) - pred_probs)
    max_err = float(np.max(diffs))
    assert max_err < 1e-2, f"Additivity error {max_err} exceeds 0.01 threshold"
