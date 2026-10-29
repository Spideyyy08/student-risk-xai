"""
Academic Semester Model.
"""

from datetime import date
from typing import Optional, List
from sqlalchemy import String, Boolean, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Semester(Base):
    __tablename__ = "semesters"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(16), unique=True, index=True, nullable=False)  # e.g. sem4, sem5
    label: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g. Semester 5 (AY 2026-27)
    academic_year: Mapped[str] = mapped_column(String(32), nullable=False)  # e.g. 2026-27
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    subjects: Mapped[List["Subject"]] = relationship("Subject", back_populates="semester")
