"""
Application Configuration and Settings.
Pydantic v2 Settings with strict environment and secret key validation.
"""

import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

# Paths
BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    APP_NAME: str = "Student Academic Risk Prediction & Early Intervention System"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "mysql+pymysql://risk_user:risk_pass_dev@localhost:3307/student_risk"
    JWT_SECRET_KEY: str = "dev_secret_key_change_in_production_min_32_chars_ok"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    CORS_ORIGINS: List[str] = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Model and artifacts
    MODEL_ARTIFACTS_DIR: str = str(PROJECT_ROOT / "ml_pipeline" / "artifacts")
    RULES_FILE_PATH: str = str(PROJECT_ROOT / "data" / "rules" / "recommendation_rules.json")
    DEFAULT_SEMESTER: str = "sem5"
    HIGH_RISK_THRESHOLD: float = 0.40

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, v: str, info) -> str:
        env = os.environ.get("ENVIRONMENT", "development")
        if env.lower() == "production":
            if v == "change_me" or len(v) < 32:
                raise ValueError("In production, JWT_SECRET_KEY must not be 'change_me' and must be >= 32 characters long.")
        return v


settings = Settings()
