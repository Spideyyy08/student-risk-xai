"""
Recommendation Schemas.
"""

from typing import Optional
from pydantic import BaseModel, ConfigDict


class RecommendationOut(BaseModel):
    id: int
    priority: str  # High, Medium, Low
    action: str
    reason: str
    subject: Optional[str] = None
    assigned: bool = False

    model_config = ConfigDict(from_attributes=True)


class RecommendationUpdate(BaseModel):
    assigned: bool

    model_config = ConfigDict(extra="ignore")


class GenericSuccessResponse(BaseModel):
    success: bool = True
    message: Optional[str] = "Operation successful."
