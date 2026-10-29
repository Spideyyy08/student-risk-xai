"""
SQLAlchemy Models Package.
Exports all entity tables for metadata registration and migration.
"""

from app.models.student import Student
from app.models.user import User
from app.models.semester import Semester
from app.models.subject import Subject
from app.models.attendance import AttendanceRecord
from app.models.assessment import Assessment
from app.models.assignment import Assignment
from app.models.semester_result import SemesterResult
from app.models.model_version import ModelVersion
from app.models.prediction import Prediction
from app.models.recommendation import Recommendation
from app.models.intervention import Intervention
from app.models.import_batch import ImportBatch
from app.models.audit_log import AuditLog

__all__ = [
    "Student",
    "User",
    "Semester",
    "Subject",
    "AttendanceRecord",
    "Assessment",
    "Assignment",
    "SemesterResult",
    "ModelVersion",
    "Prediction",
    "Recommendation",
    "Intervention",
    "ImportBatch",
    "AuditLog",
]
