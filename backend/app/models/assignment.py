"""
Assignment Submission Model.
"""

from datetime import date
from sqlalchemy import String, Float, Date, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Assignment(Base):
    __tablename__ = "assignments"
    __table_args__ = (
        CheckConstraint(
            "status IN ('Submitted on time', 'Submitted late', 'Defaulter (Missing)')",
            name="check_assignment_status",
        ),
        CheckConstraint("score >= 0.0 AND score <= 10.0", name="check_assignment_score_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    submitted_on: Mapped[date] = mapped_column(Date, nullable=False)

    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="assignments")
    subject: Mapped["Subject"] = relationship("Subject", back_populates="assignments")
