"""
Model Registry Service.
Single global ModelBundle loaded during FastAPI lifespan.
Provides thread-safe access to pipeline, explainer, and metadata.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import numpy as np
import pandas as pd
import shap
import joblib

from app.core.config import settings
from ml_pipeline.config import MODEL_DIR, SHAP_DIR, FEATURES
from ml_pipeline.src.predict import load_model_pipeline

logger = logging.getLogger(__name__)


class ModelBundle:
    def __init__(self):
        self.is_loaded: bool = False
        self.version: str = "unknown"
        self.algorithm: str = "unknown"
        self.pipeline = None
        self.classifier = None
        self.explainer = None
        self.metadata: Dict[str, Any] = {}
        self.background_df: Optional[pd.DataFrame] = None
        self.base_value: float = 0.25

    def load(self) -> bool:
        """Attempt to load model artifacts from disk. Never crashes if missing."""
        meta_path = MODEL_DIR / "metadata.json"
        if not meta_path.exists():
            logger.warning(f"Metadata file not found at {meta_path}. Model not loaded.")
            self.is_loaded = False
            return False

        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)

            self.version = self.metadata.get("version", "v1")
            self.algorithm = self.metadata.get("algorithm", "RandomForest")

            self.pipeline = load_model_pipeline()
            self.classifier = self.pipeline.named_steps["classifier"]

            # Fix 9: Set single thread inference for low latency
            if hasattr(self.classifier, "n_jobs"):
                self.classifier.n_jobs = 1

            # Load TreeExplainer
            self.explainer = shap.TreeExplainer(self.classifier)

            # Extract base value for Class 2 (High Risk)
            ev = self.explainer.expected_value
            if isinstance(ev, (list, np.ndarray)):
                self.base_value = float(ev[2])
            else:
                self.base_value = float(ev)

            # Load background sample if available
            bg_path = SHAP_DIR / "background.csv"
            if bg_path.exists():
                self.background_df = pd.read_csv(bg_path)

            self.is_loaded = True
            logger.info(f"Successfully loaded ModelBundle: {self.algorithm} (v{self.version})")
            return True
        except Exception as err:
            logger.error(f"Failed to load model artifacts: {err}")
            self.is_loaded = False
            return False


# Global singleton instance
model_bundle = ModelBundle()
