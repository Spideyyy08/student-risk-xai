"""
API v1 Central Router.
Mounts all functional domain routers and public health check.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import get_db
from app.core.config import settings
from app.services.model_registry import model_bundle

from app.api.v1.endpoints import (
    auth,
    users,
    students,
    subjects,
    attendance,
    assessments,
    assignments,
    imports,
    predictions,
    explanations,
    analytics,
    recommendations,
    simulator,
    interventions,
)

api_router = APIRouter()

# Health check (public, no auth)
@api_router.get("/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """API health status and dependency checks."""
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    return {
        "status": "healthy" if (db_status == "ok" and model_bundle.is_loaded) else "degraded",
        "app": settings.APP_NAME,
        "model_loaded": model_bundle.is_loaded,
        "model_version": model_bundle.version if model_bundle.is_loaded else None,
        "db": db_status,
    }

# Mount subrouters
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(students.router)
api_router.include_router(subjects.router)
api_router.include_router(attendance.router)
api_router.include_router(assessments.router)
api_router.include_router(assignments.router)
api_router.include_router(imports.router)
api_router.include_router(predictions.router)
api_router.include_router(explanations.router)
api_router.include_router(analytics.router)
api_router.include_router(recommendations.router)
api_router.include_router(simulator.router)
api_router.include_router(interventions.router)
