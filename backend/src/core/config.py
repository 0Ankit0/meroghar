"""
Application configuration and environment variable management.
Implements T023 and T016 from tasks.md.
"""

import logging
import sys
from functools import lru_cache
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="Meroghar Rental Management", alias="APP_NAME")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=True, alias="DEBUG")
    api_version: str = Field(default="v1", alias="API_VERSION")

    # Server
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    # Database
    database_url: str = Field(
        default="postgresql://meroghar:meroghar_dev_password@localhost:5432/meroghar_dev",
        alias="DATABASE_URL",
    )
    db_echo: bool = Field(default=False, alias="DB_ECHO")
    db_pool_size: int = Field(default=20, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=40, alias="DB_MAX_OVERFLOW")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    # Security
    secret_key: str = Field(
        default="your-secret-key-here-change-in-production-min-32-chars",
        alias="SECRET_KEY",
    )
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")
    bcrypt_cost_factor: int = Field(default=12, alias="BCRYPT_COST_FACTOR")

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        alias="CORS_ORIGINS",
    )
    cors_credentials: bool = Field(default=True, alias="CORS_CREDENTIALS")
    cors_methods: List[str] = Field(default=["*"], alias="CORS_METHODS")
    cors_headers: List[str] = Field(default=["*"], alias="CORS_HEADERS")

    # JWT
    jwt_secret_key: str = Field(
        default="your-jwt-secret-key-change-in-production", alias="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=30, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7, alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS"
    )

    # Celery
    celery_broker_url: str = Field(
        default="redis://localhost:6379/0", alias="CELERY_BROKER_URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/0", alias="CELERY_RESULT_BACKEND"
    )
    celery_task_serializer: str = Field(default="json", alias="CELERY_TASK_SERIALIZER")
    celery_result_serializer: str = Field(
        default="json", alias="CELERY_RESULT_SERIALIZER"
    )
    celery_accept_content: List[str] = Field(
        default=["json"], alias="CELERY_ACCEPT_CONTENT"
    )
    celery_timezone: str = Field(default="UTC", alias="CELERY_TIMEZONE")
    celery_enable_utc: bool = Field(default=True, alias="CELERY_ENABLE_UTC")

    # Payment Gateways
    stripe_api_key: Optional[str] = Field(default=None, alias="STRIPE_API_KEY")
    stripe_webhook_secret: Optional[str] = Field(
        default=None, alias="STRIPE_WEBHOOK_SECRET"
    )
    razorpay_key_id: Optional[str] = Field(default=None, alias="RAZORPAY_KEY_ID")
    razorpay_key_secret: Optional[str] = Field(
        default=None, alias="RAZORPAY_KEY_SECRET"
    )
    paypal_client_id: Optional[str] = Field(default=None, alias="PAYPAL_CLIENT_ID")
    paypal_client_secret: Optional[str] = Field(
        default=None, alias="PAYPAL_CLIENT_SECRET"
    )
    paypal_mode: str = Field(default="sandbox", alias="PAYPAL_MODE")
    
    # Khalti Payment Gateway (Nepal)
    khalti_secret_key: Optional[str] = Field(default=None, alias="KHALTI_SECRET_KEY")
    khalti_use_sandbox: bool = Field(default=True, alias="KHALTI_USE_SANDBOX")
    khalti_return_url: Optional[str] = Field(default=None, alias="KHALTI_RETURN_URL")
    khalti_website_url: Optional[str] = Field(default=None, alias="KHALTI_WEBSITE_URL")

    # eSewa Payment Gateway (Nepal)
    esewa_merchant_id: Optional[str] = Field(default=None, alias="ESEWA_MERCHANT_ID")
    esewa_secret_key: Optional[str] = Field(default=None, alias="ESEWA_SECRET_KEY")
    esewa_use_sandbox: bool = Field(default=True, alias="ESEWA_USE_SANDBOX")

    # IME Pay Payment Gateway (Nepal)
    imepay_merchant_code: Optional[str] = Field(default=None, alias="IMEPAY_MERCHANT_CODE")
    imepay_secret_key: Optional[str] = Field(default=None, alias="IMEPAY_SECRET_KEY")
    imepay_use_sandbox: bool = Field(default=True, alias="IMEPAY_USE_SANDBOX")

    # Cloud Storage (AWS S3)
    aws_access_key_id: Optional[str] = Field(default=None, alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(
        default=None, alias="AWS_SECRET_ACCESS_KEY"
    )
    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    s3_bucket_name: Optional[str] = Field(default=None, alias="S3_BUCKET_NAME")
    s3_bucket_receipts: Optional[str] = Field(default=None, alias="S3_BUCKET_RECEIPTS")
    s3_bucket_uploads: Optional[str] = Field(default=None, alias="S3_BUCKET_UPLOADS")

    # Messaging
    twilio_account_sid: Optional[str] = Field(default=None, alias="TWILIO_ACCOUNT_SID")
    twilio_auth_token: Optional[str] = Field(default=None, alias="TWILIO_AUTH_TOKEN")
    twilio_phone_number: Optional[str] = Field(
        default=None, alias="TWILIO_PHONE_NUMBER"
    )
    twilio_whatsapp_number: Optional[str] = Field(
        default=None, alias="TWILIO_WHATSAPP_NUMBER"
    )

    # Push Notifications
    firebase_credentials_path: Optional[str] = Field(
        default=None, alias="FIREBASE_CREDENTIALS_PATH"
    )
    fcm_server_key: Optional[str] = Field(default=None, alias="FCM_SERVER_KEY")

    # Monitoring & Logging
    sentry_dsn: Optional[str] = Field(default=None, alias="SENTRY_DSN")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    rate_limit_per_minute: int = Field(default=60, alias="RATE_LIMIT_PER_MINUTE")

    # File Upload
    max_upload_size_mb: int = Field(default=10, alias="MAX_UPLOAD_SIZE_MB")
    allowed_image_types: List[str] = Field(
        default=["image/jpeg", "image/png", "image/webp"],
        alias="ALLOWED_IMAGE_TYPES",
    )
    allowed_document_types: List[str] = Field(
        default=["application/pdf", "image/jpeg", "image/png"],
        alias="ALLOWED_DOCUMENT_TYPES",
    )

    # Pagination
    default_page_size: int = Field(default=20, alias="DEFAULT_PAGE_SIZE")
    max_page_size: int = Field(default=100, alias="MAX_PAGE_SIZE")

    # Currency
    default_currency: str = Field(default="INR", alias="DEFAULT_CURRENCY")
    exchange_rate_api_key: Optional[str] = Field(
        default=None, alias="EXCHANGE_RATE_API_KEY"
    )

    # Testing
    test_database_url: Optional[str] = Field(default=None, alias="TEST_DATABASE_URL")

    @field_validator("bcrypt_cost_factor")
    @classmethod
    def validate_bcrypt_cost(cls, v: int) -> int:
        """Ensure bcrypt cost factor is at least 12."""
        if v < 12:
            raise ValueError("bcrypt_cost_factor must be at least 12 for security")
        return v

    @field_validator("secret_key", "jwt_secret_key")
    @classmethod
    def validate_secret_keys(cls, v: str) -> str:
        """Ensure secret keys are sufficiently long."""
        if len(v) < 32:
            raise ValueError("Secret keys must be at least 32 characters long")
        return v

    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL (for Alembic)."""
        return self.database_url.replace("+asyncpg", "")

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def setup_logging() -> None:
    """
    Configure application-wide logging.
    Implements T016 from tasks.md.
    """
    settings = get_settings()

    # Determine log level
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    # Set specific log levels for noisy libraries
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.db_echo else logging.WARNING
    )
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)

    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging configured: level={settings.log_level}, environment={settings.environment}"
    )


# Initialize logging on module import
setup_logging()


__all__ = ["Settings", "get_settings", "setup_logging"]
