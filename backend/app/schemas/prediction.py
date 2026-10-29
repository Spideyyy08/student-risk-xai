"""
Prediction and SHAP Explanation Schemas.
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, ConfigDict


class Factor(BaseModel):
    feature: str
    label: str
    value: str
    shap: float
    detail: str

    model_config = ConfigDict(from_attributes=True)


class ExplanationResponse(BaseModel):
    base_value: float
    factors: List[Factor]

    model_config = ConfigDict(from_attributes=True)


class PredictionResponse(BaseModel):
    student_id: str
    risk_level: str
    probabilities: Dict[str, float]
    updated_at: str
    model_version: str
    low_confidence: bool
    is_estimate: bool = True

    model_config = ConfigDict(from_attributes=True)
