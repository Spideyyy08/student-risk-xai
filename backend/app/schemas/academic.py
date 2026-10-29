"""
Academic Assessment, Attendance, Subject Breakdown, and Trend Schemas.
"""

from typing import List, Dict, Optional, Union
from pydantic import BaseModel, ConfigDict, field_validator


class SubjectPerformanceOut(BaseModel):
    subject_code: str
    subject_name: str
    subject_short: str
    attendance_pct: int
    quiz_avg: int
    quiz_max: int = 100
    assignment_pct: int
    internal_marks: int
    internal_max: int = 30
    status: str  # Satisfactory, Attention, Critical

    model_config = ConfigDict(from_attributes=True)


class TrendResponse(BaseModel):
    months: List[str]
    attendance: List[int]
    quiz_scores: List[int]
    past_sgpa: List[Dict[str, Any]] if False else List[dict]

    model_config = ConfigDict(from_attributes=True)


class PredictionSummary(BaseModel):
    risk_level: str
    probabilities: Dict[str, float]

    model_config = ConfigDict(from_attributes=True)


class AttendanceCreate(BaseModel):
    student_id: str
    subject: str
    date: str  # YYYY-MM-DD
    attendance_pct: float

    @field_validator("attendance_pct")
    @classmethod
    def check_range(cls, v: float) -> float:
        if v < 0.0 or v > 100.0:
            raise ValueError("Attendance percentage must be between 0 and 100.")
        return v


class AssessmentCreate(BaseModel):
    student_id: str
    subject: str
    assessment: str  # "Quiz 1", "Quiz 2", "Mid-Sem", "Lab Test"
    score: float
    max: float

    @field_validator("score", "max")
    @classmethod
    def check_scores(cls, v: float, info) -> float:
        if v < 0:
            raise ValueError("Assessment scores must be non-negative.")
        return v


class AssignmentCreate(BaseModel):
    student_id: str
    subject: str
    title: str
    status: str  # "Submitted on time", "Submitted late", "Defaulter (Missing)"
    score: Union[float, str, int]

    @field_validator("score")
    @classmethod
    def coerce_score(cls, v: Union[float, str, int]) -> float:
        try:
            val = float(v)
        except Exception:
            raise ValueError("Assignment score must be a valid number between 0 and 10.")
        if val < 0.0 or val > 10.0:
            raise ValueError("Assignment score must be between 0 and 10.")
        return val


class DataEntryResponse(BaseModel):
    success: bool = True
    message: str
    prediction: PredictionSummary
