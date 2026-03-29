"""Application configuration via environment variables."""

from pydantic import field_validator
from pydantic_settings import BaseSettings

_WEAK_SECRET_KEYS = frozenset({
    "change-me-in-production",
    "secret",
    "secret_key",
    "changeme",
    "password",
    "test",
    "development",
    "default",
})


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    secret_key: str
    app_url: str = "http://localhost:8000"
    debug: bool = False

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError("SECRET_KEY environment variable is required and must not be empty")
        if v.lower() in _WEAK_SECRET_KEYS:
            raise ValueError(
                f"SECRET_KEY is set to a known weak value ('{v}'). "
                "Generate a strong random key, e.g.: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
            )
        if len(v) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters long for adequate security"
            )
        return v

    # Database
    database_url: str = "postgresql+asyncpg://dataseal:dataseal@localhost:5432/dataseal"
    database_url_sync: str = "postgresql://dataseal:dataseal@localhost:5432/dataseal"

    # Valkey
    valkey_url: str = "redis://localhost:6379/0"

    # Email
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_address: str = "noreply@dataseal.example.com"
    smtp_from_name: str = "DataSeal"
    smtp_use_tls: bool = False

    # Storage
    storage_backend: str = "local"
    storage_local_path: str = "/data/storage"

    # Signing
    signing_token_expiry_hours: int = 72
    max_document_size_mb: int = 25
    max_documents_per_envelope: int = 10

    # Rate limiting
    rate_limit_per_minute: int = 100

    # Auth / JWT
    access_token_expiry_minutes: int = 15
    refresh_token_expiry_days: int = 7

    # bcrypt cost factor
    bcrypt_rounds: int = 12

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
