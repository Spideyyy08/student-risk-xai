"""
FastAPI Dependencies: DB Session, Authentication, and Role-Based Access Control.
Annotated dependencies with audit trail logging upon authorization denial.
"""

from typing import Annotated, List, Optional
from fastapi import Depends, Header, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.core.security import decode_access_token
from app.core.exceptions import AppException, ForbiddenException
from app.core.roles import UserRole, STAFF_ROLES
from app.models.user import User
from app.models.student import Student
from app.models.audit_log import AuditLog

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Validate Bearer JWT and return authenticated User entity."""
    if not credentials or not credentials.credentials:
        raise AppException("Missing or invalid authorization header.", status_code=status.HTTP_401_UNAUTHORIZED)

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except Exception as err:
        raise AppException("Session expired or invalid token. Please log in again.", status_code=status.HTTP_401_UNAUTHORIZED)

    username: str = payload.get("sub")
    if not username:
        raise AppException("Invalid authentication payload.", status_code=status.HTTP_401_UNAUTHORIZED)

    user = db.scalar(select(User).where(User.username == username))
    if not user or not user.is_active:
        raise AppException("User account is inactive or not found.", status_code=status.HTTP_401_UNAUTHORIZED)

    return user


def require_roles(allowed_roles: List[UserRole]):
    """Enforce endpoint role authorization with security audit logging."""
    def role_checker(
        request: Request,
        current_user: Annotated[User, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)],
    ) -> User:
        user_role_str = str(current_user.role).upper()
        allowed_str = [str(r.value if isinstance(r, UserRole) else r).upper() for r in allowed_roles]

        if user_role_str not in allowed_str:
            # Audit forbidden attempt
            client_ip = request.client.host if request.client else "unknown"
            audit = AuditLog(
                user_id=current_user.id,
                username=current_user.username,
                action="FORBIDDEN",
                entity="ROLE_ACCESS",
                entity_id=request.url.path,
                ip=client_ip,
            )
            db.add(audit)
            db.commit()
            raise ForbiddenException(f"Access forbidden: role '{current_user.role}' lacks required permissions.")

        return current_user

    return role_checker


def require_self_or_staff(
    student_identifier: str,
    current_user: User,
    db: Session,
    request: Request,
) -> Student:
    """
    Ensure caller is either staff (ADMIN/TEACHER) or the student themselves.
    student_identifier matches student_code (e.g. STU101) or roll (e.g. 221101).
    """
    # Find student
    student = db.scalar(
        select(Student).where(
            (Student.student_code == student_identifier) | (Student.roll == student_identifier)
        )
    )
    if not student:
        raise AppException(f"Student '{student_identifier}' not found.", status_code=status.HTTP_404_NOT_FOUND)

    if current_user.role in [UserRole.ADMIN.value, UserRole.TEACHER.value, "ADMIN", "TEACHER"]:
        return student

    # If student, verify match
    if current_user.student_id != student.id:
        client_ip = request.client.host if request.client else "unknown"
        audit = AuditLog(
            user_id=current_user.id,
            username=current_user.username,
            action="FORBIDDEN_STUDENT_ACCESS",
            entity="STUDENT",
            entity_id=str(student_identifier),
            ip=client_ip,
        )
        db.add(audit)
        db.commit()
        raise ForbiddenException("Access forbidden: students may only view their own academic record.")

    return student
