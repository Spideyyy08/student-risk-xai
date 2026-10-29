"""
Student Entity Schemas.
Matches frozen frontend contract precisely.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, ConfigDict


class PastSGPAItem(BaseModel):
    semester: str
    sgpa: float

    model_config = ConfigDict(from_attributes=True)


class StudentOut(BaseModel):
    id: str  # student_code, e.g. STU101
    roll: str
    name: str
    division: str
    semester: str  # Semester label, e.g. "Semester 5 (AY 2026-27)"
    risk_level: str  # High, Medium, Low
    probabilities: Dict[str, float]  # {"low": 0.08, "medium": 0.17, "high": 0.75}
    updated_at: str  # "YYYY-MM-DD"
    attendance_pct: int
    quiz_avg: int
    assignment_pct: int
    internal_marks: int
    practical_marks: int
    backlogs: int
    key_factor: str
    past_sgpa: List[PastSGPAItem]

    model_config = ConfigDict(from_attributes=True)


class StudentListResponse(BaseModel):
    items: List[StudentOut]
    total: int
    page: int
    total_pages: int
    page_size: int
    semester: str

    model_config = ConfigDict(from_attributes=True)
