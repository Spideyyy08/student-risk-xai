"""
Attendance Record Model.
Stores cumulative attendance percentage snapshots.
"""

from datetime import date
from typing import Optional
from sqlalchemy import Float, Integer, Date, ForeignKey, Index, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    __table_args__ = (
        CheckConstraint("attendance_pct >= 0.0 AND attendance_pct <= 100.0", name="check_attendance_pct_range"),
        Index("idx_student_subject_date", "student_id", "subject_id", "record_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    record_date: Mapped[date] = mapped_column(Date, nullable=False)
    attendance_pct: Mapped[float] = mapped_column(Float, nullable=False)
    classes_held: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    classes_attended: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="attendance_records")
    subject: Mapped["Subject"] = relationship("Subject", back_populates="attendance_records")
