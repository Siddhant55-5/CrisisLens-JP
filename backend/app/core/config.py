"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """CrisisLens application settings."""

    # ── Data Source API Keys ──────────────────────────────────────
    FRED_API_KEY: str = ""
    YAHOO_FINANCE_KEY: str = ""
    NEWS_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # ── Database ──────────────────────────────────────────────────
    DB_USER: str = "crisislens"
    DB_PASSWORD: str = "crisislens_secret"
    DB_HOST: str = "timescaledb"
    DB_PORT: int = 5432
    DB_NAME: str = "crisislens"
    DB_URL: str = "postgresql+asyncpg://crisislens:crisislens_secret@timescaledb:5432/crisislens"

    # ── Redis ─────────────────────────────────────────────────────
    REDIS_URL: str = "redis://redis:6379/0"

    # ── Backend ───────────────────────────────────────────────────
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    LOG_LEVEL: str = "info"

    # ── MLflow ────────────────────────────────────────────────────
    MLFLOW_TRACKING_URI: str = "http://mlflow:5001"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
