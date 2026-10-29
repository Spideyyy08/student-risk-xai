"""
What-If Academic Risk Simulator Endpoints.
"""

from typing import Annotated
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import get_current_user, require_self_or_staff
from app.schemas.simulator import WhatIfRequest, WhatIfResponse
from app.models.user import User
from app.services.simulation_service import run_what_if_simulation

router = APIRouter(prefix="/simulator", tags=["Simulator"])


@router.post("/what-if", response_model=WhatIfResponse)
def simulate_academic_risk(
    payload: WhatIfRequest,
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Run what-if counterfactual prediction with parameter overrides.
    Zero persistent database modifications.
    """
    # Permission check: student can simulate only themselves
    require_self_or_staff(payload.student_id, current_user, db, request)

    overrides_dict = payload.overrides.model_dump(exclude_unset=True)
    res = run_what_if_simulation(
        db=db,
        student_identifier=payload.student_id,
        overrides=overrides_dict,
        semester_code="sem5",
    )
    return WhatIfResponse(**res)
