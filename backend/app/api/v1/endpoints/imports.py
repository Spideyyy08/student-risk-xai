"""
Bulk Data Ingestion Endpoint.
"""

from typing import Annotated
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import require_roles
from app.core.roles import STAFF_ROLES
from app.schemas.imports import ImportBatchRequest, ImportBatchResponse
from app.models.user import User
from app.services.ingestion_service import process_import_batch

router = APIRouter(prefix="/imports", tags=["Imports"])


@router.post("", response_model=ImportBatchResponse)
def import_student_data(
    payload: ImportBatchRequest,
    request: Request,
    current_user: Annotated[User, Depends(require_roles(STAFF_ROLES))],
    db: Session = Depends(get_db),
):
    """
    Ingest bulk class records from JSON/CSV payload.
    Restricted to ADMIN and TEACHER roles.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    result = process_import_batch(
        db=db,
        records=payload.records,
        semester_code=payload.semester or "sem5",
        user_id=current_user.id,
        username=current_user.username,
        client_ip=client_ip,
    )
    return ImportBatchResponse(**result)
