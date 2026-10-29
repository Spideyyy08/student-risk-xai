"""
Authentication Endpoints.
Handles JSON login, rate throttling, JWT generation, and identity resolution.
"""

from typing import Annotated
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.core.config import settings
from app.core.security import (
    verify_password,
    create_access_token,
    check_login_throttled,
    record_failed_login,
    reset_failed_login,
)
from app.core.exceptions import AppException
from app.core.deps import get_current_user
from app.schemas.auth import LoginRequest, LoginResponse, UserMeResponse
from app.models.user import User
from app.models.student import Student
from app.models.audit_log import AuditLog

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Authenticate user with username and password, with 5-attempt rate throttling."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    username = payload.username.strip()

    # Throttling check
    check_login_throttled(username, client_ip)

    user = db.scalar(select(User).where(User.username == username))
    if not user or not verify_password(payload.password, user.password_hash) or not user.is_active:
        record_failed_login(username, client_ip)
        audit = AuditLog(
            user_id=user.id if user else None,
            username=username,
            action="LOGIN_FAIL",
            entity="AUTH",
            ip=client_ip,
        )
        db.add(audit)
        db.commit()
        raise AppException("Invalid username or password.", status_code=status.HTTP_401_UNAUTHORIZED)

    # Success
    reset_failed_login(username, client_ip)
    user.last_login_at = datetime.now(timezone.utc)

    # Resolve student_code if student role
    student_code = None
    if user.student_id:
        st = db.scalar(select(Student).where(Student.id == user.student_id))
        if st:
            student_code = st.student_code

    token = create_access_token(
        subject=user.username,
        role=user.role,
        student_id=student_code,
        name=user.full_name,
        department=user.department,
    )

    audit = AuditLog(
        user_id=user.id,
        username=user.username,
        action="LOGIN_OK",
        entity="AUTH",
        ip=client_ip,
    )
    db.add(audit)
    db.commit()

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        role=user.role,
        name=user.full_name,
        department=user.department,
        student_id=student_code,
    )


@router.get("/me", response_model=UserMeResponse)
def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Return currently authenticated user details."""
    student_code = None
    if current_user.student_id:
        st = db.scalar(select(Student).where(Student.id == current_user.student_id))
        if st:
            student_code = st.student_code

    return UserMeResponse(
        username=current_user.username,
        role=current_user.role,
        name=current_user.full_name,
        student_id=student_code,
    )
