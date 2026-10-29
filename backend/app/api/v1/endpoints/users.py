"""
User Administration Endpoints.
"""

from typing import Annotated, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.core.deps import require_roles
from app.core.roles import UserRole
from app.schemas.user import UserOut
from app.models.user import User

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=List[UserOut])
def list_users(
    current_user: Annotated[User, Depends(require_roles([UserRole.ADMIN]))],
    db: Session = Depends(get_db),
):
    """List registered users. Restricted to ADMIN."""
    users = db.scalars(select(User).order_by(User.id)).all()
    return users
