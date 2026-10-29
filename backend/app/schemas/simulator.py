"""
What-If Academic Simulator Schemas.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, field_validator
from app.schemas.prediction import Factor
from ml_pipeline.config import FEATURE_RANGES, SIMULATOR_OVERRIDABLE_FEATURES


class SimulatorOverrides(BaseModel):
    attendance_pct: Optional[float] = None
    quiz_avg: Optional[float] = None
    assignment_pct: Optional[float] = None
    internal_marks: Optional[float] = None
    practical_marks: Optional[float] = None
    backlogs: Optional[float] = None

    model_config = ConfigDict(extra="ignore")

    @field_validator("*")
    @classmethod
    def validate_bounds(cls, v: Optional[float], info) -> Optional[float]:
        if v is None:
            return v
        field_name = info.field_name
        if field_name in FEATURE_RANGES:
            r = FEATURE_RANGES[field_name]
            if v < r["min"] or v > r["max"]:
                raise ValueError(f"{field_name} must be within [{r['min']}, {r['max']}]. Got {v}.")
        return v


class WhatIfRequest(BaseModel):
    student_id: str
    overrides: SimulatorOverrides

    model_config = ConfigDict(extra="ignore")


class CurrentProfile(BaseModel):
    student_id: str
    name: str
    roll: str
    risk_level: str
    probabilities: Dict[str, float]
    attendance_pct: int
    quiz_avg: int
    assignment_pct: int
    internal_marks: int
    practical_marks: int
    backlogs: int

    model_config = ConfigDict(from_attributes=True)


class SimulatedProfile(BaseModel):
    risk_level: str
    probabilities: Dict[str, float]
    factors: List[Factor]

    model_config = ConfigDict(from_attributes=True)


class WhatIfResponse(BaseModel):
    current: CurrentProfile
    simulated: SimulatedProfile

    model_config = ConfigDict(from_attributes=True)
