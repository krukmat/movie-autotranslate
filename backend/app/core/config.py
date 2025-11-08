from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings


def _default_database_url() -> str:
    root = Path(__file__).resolve().parents[3]
    db_path = root / "data" / "app.db"
    return f"sqlite:///{db_path}"


class Settings(BaseSettings):
    app_name: str = "Movie AutoTranslate API"
    api_prefix: str = "/v1"
    environment: str = Field(default="dev", env="ENVIRONMENT")
    api_key_header: str = Field(default="X-API-Key", env="API_KEY_HEADER")
    api_keys: List[str] = Field(default_factory=list, env="API_KEYS")
    rate_limit_per_minute: int = Field(default=120, env="RATE_LIMIT_PER_MINUTE")

    database_url: str = Field(default_factory=_default_database_url, env="DATABASE_URL")

    redis_url: AnyUrl = Field(
        default="redis://redis:6379/0",
        env="REDIS_URL",
    )
    broker_queue: str = Field(default="pipeline", env="BROKER_QUEUE")

    minio_endpoint: str = Field(default="minio:9000", env="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="minioadmin", env="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(default="minioadmin", env="MINIO_SECRET_KEY")
    minio_bucket_raw: str = Field(default="raw", env="MINIO_BUCKET_RAW")
    minio_bucket_processed: str = Field(default="proc", env="MINIO_BUCKET_PROCESSED")
    minio_bucket_public: str = Field(default="pub", env="MINIO_BUCKET_PUBLIC")
    upload_url_expiry_seconds: int = Field(default=3600, env="UPLOAD_URL_EXPIRY")
    download_url_expiry_seconds: int = Field(default=900, env="DOWNLOAD_URL_EXPIRY")

    allowed_languages: List[str] = Field(
        default_factory=lambda: ["en", "es", "fr", "de"],
        env="ALLOWED_LANGUAGES",
    )
    upload_part_size: int = Field(default=8 * 1024 * 1024, env="UPLOAD_PART_SIZE")  # 8 MB
    max_upload_size: int = Field(default=8 * 1024 * 1024 * 1024, env="MAX_UPLOAD_SIZE")  # 8 GB
    max_active_jobs_per_key: int = Field(default=5, env="MAX_ACTIVE_JOBS_PER_KEY")

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()
