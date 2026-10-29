"""
Data loading utilities for synthetic, external, and database sources.
Windows-safe path handling, dialect-neutral types, and proper app.* imports.
"""

from pathlib import Path
from typing import Tuple, Optional
import pandas as pd
from ml_pipeline.config import SYNTHETIC_DATA_DIR, EXTERNAL_DATA_DIR, FEATURES


def load_synthetic_dataset(filepath: Optional[Path] = None) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """
    Load synthetic dataset, splitting features (X), risk label (y), and audit info (metadata).
    Returns (X, y, audit_df).
    """
    path = filepath or (SYNTHETIC_DATA_DIR / "student_risk_train.csv")
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found at {path}. Run: python ml_pipeline/scripts/01_generate_synthetic_data.py"
        )

    df = pd.read_csv(path)
    if "risk_level" not in df.columns:
        raise ValueError("Missing 'risk_level' column in dataset.")

    missing_feats = [f for f in FEATURES if f not in df.columns]
    if missing_feats:
        raise ValueError(f"Dataset missing required model features: {missing_feats}")

    X = df[FEATURES].copy()
    y = df["risk_level"].copy()

    audit_cols = [c for c in ["student_code", "roll", "name", "division", "gender"] if c in df.columns]
    audit_df = df[audit_cols].copy() if audit_cols else pd.DataFrame(index=df.index)

    return X, y, audit_df


def load_db_dataset(db_url: Optional[str] = None) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """
    Load real student records and faculty-assigned ground truth outcome labels (Low/Medium/High)
    from semester_results table. Avoids circular prediction retraining.
    Requires at least 300 labeled student-semesters.
    """
    import sqlalchemy as sa
    from app.core.config import settings
    from app.services.feature_service import compute_features_for_student_semester

    url = db_url or settings.DATABASE_URL
    engine = sa.create_engine(url)

    query = """
    SELECT
        s.id AS student_id,
        s.student_code,
        s.roll,
        s.name,
        s.division,
        s.gender,
        sr.semester_code,
        sr.outcome_label
    FROM semester_results sr
    JOIN students s ON sr.student_id = s.id
    WHERE sr.outcome_label IS NOT NULL AND sr.outcome_label IN ('Low', 'Medium', 'High')
    """

    with engine.connect() as conn:
        df = pd.read_sql(sa.text(query), conn)

    if len(df) < 300:
        raise ValueError(
            f"Insufficient faculty-labeled student-semesters in database: found {len(df)}, required at least 300. "
            "Use synthetic source instead: --source csv"
        )

    # Compute features on the fly from raw records
    from app.db.session import SessionLocal
    db = SessionLocal()
    feature_rows = []
    try:
        for _, row in df.iterrows():
            feats = compute_features_for_student_semester(db, int(row["student_id"]), str(row["semester_code"]))
            feature_rows.append({f: feats.get(f, 0.0) for f in FEATURES})
    finally:
        db.close()

    X = pd.DataFrame(feature_rows)[FEATURES]
    y = df["outcome_label"]
    audit_df = df[["student_code", "roll", "name", "division", "gender"]].copy()

    return X, y, audit_df
