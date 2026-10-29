"""
Intervention Management Schemas.
"""

from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator


class InterventionCreate(BaseModel):
    student_id: str
    type: str  # Counselling, Extra class, Parent meeting, Mentor assigned
    status: str = "Planned"  # Planned, In progress, Completed
    date: str  # YYYY-MM-DD
    notes: Optional[str] = None
    semester: Optional[str] = None

    model_config = ConfigDict(extra="ignore")

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        valid = ["Counselling", "Extra class", "Parent meeting", "Mentor assigned"]
        if v not in valid:
            raise ValueError(f"Invalid intervention type. Allowed: {valid}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid = ["Planned", "In progress", "Completed"]
        if v not in valid:
            raise ValueError(f"Invalid intervention status. Allowed: {valid}")
        return v


class InterventionOut(BaseModel):
    id: int
    student_id: str
    student_name: str
    division: str
    semester: str  # code, e.g. sem5
    type: str
    date: str
    status: str
    notes: Optional[str] = ""

    model_config = ConfigDict(from_attributes=True)


class InterventionCreateResponse(BaseModel):
    success: bool = True
    item: InterventionOut

    model_config = ConfigDict(from_attributes=True)
