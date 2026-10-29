"""
Intervention Log Model.
Tracks faculty-initiated support sessions, counselling, and parent communications.
"""

from datetime import date, datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, Date, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Intervention(Base):
    __tablename__ = "interventions"
    __table_args__ = (
        CheckConstraint(
            "type IN ('Counselling', 'Extra class', 'Parent meeting', 'Mentor assigned')",
            name="check_intervention_type",
        ),
        CheckConstraint(
            "status IN ('Planned', 'In progress', 'Completed')",
            name="check_intervention_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    semester_code: Mapped[str] = mapped_column(String(16), nullable=False)  # sem4, sem5
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="Planned", nullable=False)
    intervention_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="interventions")
    creator: Mapped[Optional["User"]] = relationship("User")
