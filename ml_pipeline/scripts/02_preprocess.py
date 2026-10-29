"""
Data validation and preprocessing verification script.
Checks feature distributions, range bounds, and imputation readiness.
"""

import sys
from pathlib import Path

# Bootstrap sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from ml_pipeline.src.data_loader import load_synthetic_dataset
from ml_pipeline.src.preprocessing import create_preprocessor
from ml_pipeline.config import FEATURES, FEATURE_RANGES


def main():
    print("Verifying dataset and preprocessing pipeline integrity...")
    X, y, audit_df = load_synthetic_dataset()
    print(f"[OK] Successfully loaded {len(X)} rows with {len(FEATURES)} features.")

    # Check feature bounds
    out_of_bounds = []
    for col in FEATURES:
        col_min = X[col].min()
        col_max = X[col].max()
        spec_min = FEATURE_RANGES[col]["min"]
        spec_max = FEATURE_RANGES[col]["max"]
        if col_min < spec_min - 1e-4 or col_max > spec_max + 1e-4:
            out_of_bounds.append((col, col_min, col_max, spec_min, spec_max))

    if out_of_bounds:
        print("[WARNING] Features exceeding expected bounds:")
        for col, cmin, cmax, smin, smax in out_of_bounds:
            print(f"  {col}: [{cmin:.2f}, {cmax:.2f}] vs expected [{smin:.2f}, {smax:.2f}]")
    else:
        print("[OK] All feature values reside cleanly within specified domain ranges.")

    # Test preprocessor execution (median imputation)
    preprocessor = create_preprocessor(scale=False)
    X_trans = preprocessor.fit_transform(X)

    import numpy as np
    n_nans = np.isnan(X_trans).sum()
    if n_nans == 0:
        print(f"[OK] Preprocessor successfully imputed all missing values. Output shape: {X_trans.shape}")
    else:
        print(f"[FAIL] Transformed array contains {n_nans} residual NaNs.")
        sys.exit(1)


if __name__ == "__main__":
    main()
