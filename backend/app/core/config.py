"""Application settings loaded from the project-root .env file."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    APP_NAME: str = "Student Academic Risk System"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "mysql+pymysql://risk_user:risk_pass_dev@localhost:3307/student_risk"
    JWT_SECRET_KEY: str = "change_me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    CORS_ORIGINS: str = "http://localhost:8000"

    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()