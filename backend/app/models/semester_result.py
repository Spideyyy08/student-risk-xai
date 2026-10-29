"""
Semester Result Model.
Tracks historical SGPA, active backlogs, and faculty ground-truth outcome label.
"""

from typing import Optional
from sqlalchemy import String, Float, Integer, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class SemesterResult(Base):
    __tablename__ = "semester_results"
    __table_args__ = (
        UniqueConstraint("student_id", "semester_code", name="uq_student_semester_result"),
        CheckConstraint("sgpa >= 0.0 AND sgpa <= 10.0", name="check_sgpa_range"),
        CheckConstraint("backlogs_count >= 0 AND backlogs_count <= 20", name="check_backlogs_count_range"),
        CheckConstraint("outcome_label IS NULL OR outcome_label IN ('Low', 'Medium', 'High')", name="check_outcome_label"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    semester_code: Mapped[str] = mapped_column(String(16), nullable=False)  # e.g. sem2, sem3, sem4
    sgpa: Mapped[float] = mapped_column(Float, nullable=False)
    backlogs_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    outcome_label: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)  # Low/Medium/High

    # Relationship
    student: Mapped["Student"] = relationship("Student", back_populates="semester_results")
