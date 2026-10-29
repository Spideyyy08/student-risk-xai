"""
Academic Assessment Model (Quiz, Mid-Sem, Lab Test).
"""

from datetime import date
from sqlalchemy import String, Float, Date, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Assessment(Base):
    __tablename__ = "assessments"
    __table_args__ = (
        CheckConstraint("kind IN ('QUIZ', 'MIDSEM', 'LABTEST')", name="check_assessment_kind"),
        CheckConstraint("max_score > 0", name="check_max_score_positive"),
        CheckConstraint("score >= 0 AND score <= max_score", name="check_score_valid"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g. Quiz 1, Mid-Sem
    kind: Mapped[str] = mapped_column(String(16), nullable=False)  # QUIZ, MIDSEM, LABTEST
    score: Mapped[float] = mapped_column(Float, nullable=False)
    max_score: Mapped[float] = mapped_column(Float, nullable=False)
    assessed_on: Mapped[date] = mapped_column(Date, nullable=False)

    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="assessments")
    subject: Mapped["Subject"] = relationship("Subject", back_populates="assessments")
