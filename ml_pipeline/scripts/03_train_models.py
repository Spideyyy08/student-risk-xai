"""
Train candidate models, select best deployable tree model, and save versioned artifacts.
Supports --source csv|db switch.
"""

import sys
import argparse
from pathlib import Path

# Bootstrap sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from ml_pipeline.src.data_loader import load_synthetic_dataset, load_db_dataset
from ml_pipeline.src.train_models import train_and_select_model


def main():
    parser = argparse.ArgumentParser(description="Train academic risk classification models.")
    parser.add_argument(
        "--source",
        choices=["csv", "db"],
        default="csv",
        help="Data source: synthetic 'csv' (default) or MySQL 'db' (minimum 300 student-semesters)",
    )
    parser.add_argument(
        "--version",
        default="v1",
        help="Model artifact version tag (default: v1)",
    )
    args = parser.parse_args()

    print(f"Loading dataset from source: {args.source.upper()}...")
    if args.source == "db":
        X, y, audit_df = load_db_dataset()
    else:
        X, y, audit_df = load_synthetic_dataset()

    print(f"[OK] Training set size: {len(X)} rows across {len(X.columns)} features.")

    pipe, best_name, train_info = train_and_select_model(X, y, version=args.version)
    print("\nModel training and artifact serialization complete.")


if __name__ == "__main__":
    main()
