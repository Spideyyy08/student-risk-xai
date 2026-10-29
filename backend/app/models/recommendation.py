"""
Personalized Early Intervention Recommendation Model.
Rule-based recommendation instances linked to student risk factors.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Recommendation(Base):
    __tablename__ = "recommendations"
    __table_args__ = (
        UniqueConstraint("student_id", "semester_code", "rule_id", name="uq_student_sem_rule"),
        CheckConstraint("priority IN ('High', 'Medium', 'Low')", name="check_recommendation_priority"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    semester_code: Mapped[str] = mapped_column(String(16), nullable=False)
    rule_id: Mapped[str] = mapped_column(String(64), nullable=False)
    priority: Mapped[str] = mapped_column(String(16), nullable=False)  # High, Medium, Low
    subject: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    assigned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    prediction_id: Mapped[Optional[int]] = mapped_column(ForeignKey("predictions.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="recommendations")
    prediction: Mapped[Optional["Prediction"]] = relationship("Prediction", back_populates="recommendations")
