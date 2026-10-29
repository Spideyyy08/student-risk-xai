"""
Subject / Course Model.
"""

from typing import List
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)  # e.g. CS301
    name: Mapped[str] = mapped_column(String(128), nullable=False)  # e.g. Data Structures & Algorithms
    short_name: Mapped[str] = mapped_column(String(32), nullable=False)  # e.g. DSA
    semester_code: Mapped[str] = mapped_column(ForeignKey("semesters.code"), index=True, nullable=False)
    max_quiz: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    max_internal: Mapped[int] = mapped_column(Integer, default=30, nullable=False)

    # Relationships
    semester: Mapped["Semester"] = relationship("Semester", back_populates="subjects")
    attendance_records: Mapped[List["AttendanceRecord"]] = relationship("AttendanceRecord", back_populates="subject")
    assessments: Mapped[List["Assessment"]] = relationship("Assessment", back_populates="subject")
    assignments: Mapped[List["Assignment"]] = relationship("Assignment", back_populates="subject")
