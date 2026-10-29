"""
User Role Definitions and Permissions.
"""

from enum import Enum


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"


STAFF_ROLES = [UserRole.ADMIN, UserRole.TEACHER]
ALL_ROLES = [UserRole.ADMIN, UserRole.TEACHER, UserRole.STUDENT]
