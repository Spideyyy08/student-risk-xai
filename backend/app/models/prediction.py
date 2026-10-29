"""
Prediction Model.
Stores historical and latest academic risk inferences, probabilities, and SHAP factors.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List
from sqlalchemy import String, Float, Boolean, DateTime, ForeignKey, JSON, Index, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Prediction(Base):
    __tablename__ = "predictions"
    __table_args__ = (
        CheckConstraint("risk_level IN ('Low', 'Medium', 'High')", name="check_prediction_risk_level"),
        Index("idx_student_sem_latest", "student_id", "semester_code", "is_latest"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    semester_code: Mapped[str] = mapped_column(String(16), nullable=False)
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False)
    p_low: Mapped[float] = mapped_column(Float, nullable=False)
    p_medium: Mapped[float] = mapped_column(Float, nullable=False)
    p_high: Mapped[float] = mapped_column(Float, nullable=False)
    low_confidence: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    features: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    shap: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False)
    base_value: Mapped[float] = mapped_column(Float, default=0.25, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    is_latest: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)

    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="predictions")
    recommendations: Mapped[List["Recommendation"]] = relationship("Recommendation", back_populates="prediction")
