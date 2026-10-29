"""
Batch prediction scoring script for cohort analysis.
Reads students from database or dataset and computes risk classifications.
Properly imports from app.* with backend on sys.path.
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

from ml_pipeline.src.data_loader import load_synthetic_dataset
from ml_pipeline.src.predict import load_model_pipeline, predict_batch_students
from ml_pipeline.config import FEATURES


def main():
    parser = argparse.ArgumentParser(description="Batch inference on student cohort.")
    parser.add_argument("--source", choices=["csv", "db"], default="csv")
    parser.add_argument("--semester", default="sem5", help="Target semester code (default: sem5)")
    args = parser.parse_args()

    print(f"Running batch prediction (source: {args.source.upper()})...")

    if args.source == "db":
        try:
            from app.db.session import SessionLocal
            from app.models.student import Student
            from app.services.prediction_service import score_and_store_prediction

            db = SessionLocal()
            try:
                students = db.query(Student).filter(Student.is_active == True).all()
                print(f"Scoring {len(students)} active students from database for {args.semester}...")
                for st in students:
                    score_and_store_prediction(db, student_id=st.id, semester_code=args.semester)
                print("[SUCCESS] All database students scored and updated in predictions table.")
            finally:
                db.close()
            return
        except Exception as e:
            print(f"[NOTICE] Database batch scoring encountered error or DB not ready: {e}")
            print("Falling back to dataset batch scoring...")

    pipeline = load_model_pipeline()
    X, _, audit_df = load_synthetic_dataset()
    sample_df = X.head(50)
    risks, norm_probs, low_confs = predict_batch_students(pipeline, sample_df)

    print(f"\nScored sample cohort of {len(sample_df)} students:")
    print("Roll      | Risk Level | Low    | Medium | High   | Low Conf")
    print("----------+------------+--------+--------+--------+---------")
    for i in range(min(15, len(sample_df))):
        roll = audit_df.iloc[i].get("roll", f"STU_{i}")
        p = norm_probs[i]
        print(f"{roll:<9} | {risks[i]:<10} | {p['low']:<6.2f} | {p['medium']:<6.2f} | {p['high']:<6.2f} | {str(low_confs[i]):<8}")


if __name__ == "__main__":
    main()
