"""
Feature preprocessing pipelines and transformations.
Strictly encapsulates all imputation inside sklearn Pipeline to prevent data leakage.
"""

from typing import List
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from ml_pipeline.config import FEATURES


def create_preprocessor(scale: bool = False, feature_names: List[str] = FEATURES) -> Pipeline:
    """
    Build scikit-learn preprocessing pipeline.
    Imputes missing values with median.
    Optionally standardizes features (used for Logistic Regression).
    """
    steps = [
        ("imputer", SimpleImputer(strategy="median")),
    ]
    if scale:
        steps.append(("scaler", StandardScaler()))

    pipeline = Pipeline(steps)
    return pipeline
