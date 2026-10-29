"""
Authentication and User Profile Schemas.
Pydantic v2 schemas.
"""

from typing import Optional
from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    username: str
    password: str

    model_config = ConfigDict(extra="ignore")


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str
    department: Optional[str] = "Computer Engineering"
    student_id: Optional[str] = None  # student_code if role is STUDENT

    model_config = ConfigDict(from_attributes=True)


class UserMeResponse(BaseModel):
    username: str
    role: str
    name: str
    student_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
