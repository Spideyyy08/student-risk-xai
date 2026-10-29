"""
User Management Schemas.
"""

from typing import Optional
from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    username: str
    full_name: str
    role: str
    department: Optional[str] = "Computer Engineering"
    student_id: Optional[int] = None
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class UserCreate(UserBase):
    password: str


class UserOut(UserBase):
    id: int
