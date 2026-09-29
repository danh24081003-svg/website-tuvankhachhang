from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    app_name: str = "Oshin Thời Đại"
    environment: str = Field(default="development", alias="APP_ENV")
    host: str = Field(default="127.0.0.1", alias="HOST")
    port: int = Field(default=8080, alias="PORT")
    app_url: str = Field(default="http://127.0.0.1:8080", alias="APP_URL")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-1.5-flash", alias="GEMINI_MODEL")
    gemini_fallback_model: str | None = Field(default=None, alias="GEMINI_FALLBACK_MODEL")
    gemini_timeout_ms: int = Field(default=30000, alias="GEMINI_TIMEOUT_MS")
    google_cloud_project: str | None = Field(default=None, alias="GOOGLE_CLOUD_PROJECT")
    google_cloud_location: str = Field(default="global", alias="GOOGLE_CLOUD_LOCATION")
    vertex_model: str = Field(default="gemini-2.5-flash", alias="VERTEX_MODEL")
    database_url: str = Field(default=f"sqlite:///{(BASE_DIR / 'customer_ai.db').as_posix()}", alias="DATABASE_URL")
    allowed_origins: str = Field(default="http://127.0.0.1:8080,http://localhost:8080", alias="ALLOWED_ORIGINS")
    chat_rate_limit_per_minute: int = Field(default=20, alias="CHAT_RATE_LIMIT_PER_MINUTE")
    secret_key: str = Field(default="change-this-secret-key-in-production", alias="SECRET_KEY")
    admin_session_minutes: int = Field(default=480, alias="ADMIN_SESSION_MINUTES")
    admin_login_rate_limit_per_minute: int = Field(default=6, alias="ADMIN_LOGIN_RATE_LIMIT_PER_MINUTE")
    upload_max_bytes: int = Field(default=5 * 1024 * 1024, alias="UPLOAD_MAX_BYTES")
    upload_storage: str = Field(default="database", alias="UPLOAD_STORAGE")
    upload_dir: str = Field(default=str(BASE_DIR / "static" / "uploads"), alias="UPLOAD_DIR")
    upload_url_prefix: str = Field(default="/static/uploads", alias="UPLOAD_URL_PREFIX")
    gcs_bucket_name: str | None = Field(default=None, alias="GCS_BUCKET_NAME")

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", env_file_encoding="utf-8", extra="ignore")

    @model_validator(mode="after")
    def normalize_project_paths(self):
        if self.database_url.startswith("sqlite:///"):
            db_path = self.database_url.replace("sqlite:///", "", 1)
            if db_path and db_path != ":memory:":
                path = Path(db_path)
                if not path.is_absolute():
                    self.database_url = f"sqlite:///{(BASE_DIR / path).resolve().as_posix()}"
        upload_path = Path(self.upload_dir)
        if not upload_path.is_absolute():
            self.upload_dir = str((BASE_DIR / upload_path).resolve())
        return self

    @property
    def cors_origins(self) -> List[str]:
        origins = [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]
        for dynamic in [f"http://127.0.0.1:{self.port}", f"http://localhost:{self.port}"]:
            if dynamic not in origins:
                origins.append(dynamic)
        return origins


@lru_cache
def get_settings() -> Settings:
    return Settings()
