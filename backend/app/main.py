"""
FastAPI Main Application Entry Point.
Implements modern lifespan management, security middleware, exception overrides,
and static frontend delivery.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings, BACKEND_DIR, PROJECT_ROOT
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.services.model_registry import model_bundle
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load ML ModelBundle into memory
    print(f"Starting {settings.APP_NAME}...")
    loaded = model_bundle.load()
    if loaded:
        print(f"[OK] Model artifacts loaded: {model_bundle.algorithm} (v{model_bundle.version})")
    else:
        print("[NOTICE] Model artifacts missing. API will start in degraded mode. Run ml_pipeline scripts to train.")
    yield
    # Shutdown
    print("Shutting down application server.")


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Exception Handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Security Headers Middleware (No CSP as frontend relies on inline scripts/fonts)
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API v1
app.include_router(api_router, prefix="/api/v1")


# Top-level Health check alias
@app.get("/health", tags=["Health"])
def top_health():
    return {
        "status": "healthy" if model_bundle.is_loaded else "degraded",
        "app": settings.APP_NAME,
        "model_loaded": model_bundle.is_loaded,
    }


# Mount Frontend Static Files LAST
frontend_path = PROJECT_ROOT / "frontend"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
