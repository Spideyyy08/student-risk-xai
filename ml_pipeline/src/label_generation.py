"""
Risk label determination and synthetic outcome mapping.
Single source of truth for risk categorization rules.
"""

from typing import Dict, Tuple, List, Union
import numpy as np
from ml_pipeline.config import (
    CLASSES,
    HIGH_RISK_PROB_THRESHOLD,
    LOW_CONFIDENCE_THRESHOLD,
)


def decide_risk(probs: Union[List[float], Dict[str, float], np.ndarray]) -> Tuple[str, Dict[str, float], bool]:
    """
    Given class probabilities for [Low, Medium, High]:
    - Risk is High if p_high >= HIGH_RISK_PROB_THRESHOLD (0.40)
    - Otherwise, argmax of (p_low, p_medium)
    - Probabilities rounded to 2 decimals, summed to exactly 1.00
    - Returns (risk_level, normalized_probs_dict, low_confidence_bool)
    """
    if isinstance(probs, dict):
        p_low = float(probs.get("low", probs.get("Low", 0.0)))
        p_med = float(probs.get("medium", probs.get("Medium", 0.0)))
        p_high = float(probs.get("high", probs.get("High", 0.0)))
    else:
        p_low = float(probs[0])
        p_med = float(probs[1])
        p_high = float(probs[2])

    r_low = round(p_low, 2)
    r_med = round(p_med, 2)
    r_high = round(p_high, 2)

    total = round(r_low + r_med + r_high, 2)
    diff = round(1.00 - total, 2)
    if diff != 0.0:
        vals = [r_low, r_med, r_high]
        max_idx = int(np.argmax(vals))
        if max_idx == 0:
            r_low = round(r_low + diff, 2)
        elif max_idx == 1:
            r_med = round(r_med + diff, 2)
        else:
            r_high = round(r_high + diff, 2)

    norm_probs = {
        "low": float(r_low),
        "medium": float(r_med),
        "high": float(r_high),
    }

    if norm_probs["high"] >= HIGH_RISK_PROB_THRESHOLD:
        risk_level = "High"
    elif norm_probs["medium"] >= norm_probs["low"]:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    max_prob = max(norm_probs.values())
    low_confidence = bool(max_prob < LOW_CONFIDENCE_THRESHOLD)

    return risk_level, norm_probs, low_confidence


def assign_synthetic_labels(
    ability: np.ndarray,
    diligence: np.ndarray,
    attendance_pct: np.ndarray,
    backlogs: np.ndarray,
    rng: np.random.Generator,
    noise_sigma: float = 0.80,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Simulate end-of-semester outcomes and map into Low / Medium / High.
    outcome = 0.45*ability + 0.30*diligence + 0.08*(attendance_pct - 75)/10 - 0.10*backlogs + N(0, noise_sigma)
    noise_sigma: Calibrated parameter controlling classification difficulty.
    Target distribution: High ~22-28%, Medium ~27-33%, Low ~40-50%.
    3% random label noise applied.
    """
    n = len(ability)
    noise = rng.normal(0.0, noise_sigma, size=n)

    outcome = (
        0.45 * ability
        + 0.30 * diligence
        + 0.08 * ((attendance_pct - 75.0) / 10.0)
        - 0.10 * backlogs
        + noise
    )

    q_high = float(np.percentile(outcome, 25))
    q_med = float(np.percentile(outcome, 55))

    labels = np.empty(n, dtype=object)
    for i in range(n):
        if outcome[i] <= q_high:
            labels[i] = "High"
        elif outcome[i] <= q_med:
            labels[i] = "Medium"
        else:
            labels[i] = "Low"

    # 3% label noise
    noise_mask = rng.random(size=n) < 0.03
    random_classes = rng.choice(CLASSES, size=n)
    labels[noise_mask] = random_classes[noise_mask]

    return labels, outcome
