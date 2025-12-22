import os
import secrets
from pydantic_settings import BaseSettings
from pydantic import ConfigDict, field_validator


class Settings(BaseSettings):
    # Environment
    ENVIRONMENT: str = os.getenv(
        "ENVIRONMENT", "development"
    )  # development, staging, production
    VERSION: str = os.getenv("VERSION", "2.0.0")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    PROJECT_NAME: str = "Holistic Learning Ecosystem"
    BASE_URL: str = os.getenv("BASE_URL", "https://a7z4kjysmp.us-east-1.awsapprunner.com")
    API_V1_STR: str = "/api/v1"
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "eduecosystem")

    # Superuser
    FIRST_SUPERUSER: str = os.getenv("FIRST_SUPERUSER", "ktej255@gmail.com")
    FIRST_SUPERUSER_PASSWORD: str = os.getenv("FIRST_SUPERUSER_PASSWORD", "Tej@1106")

    # Database URL - use PostgreSQL in production, SQLite for development
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./eduecosystem_v2.db"
        if os.getenv("ENVIRONMENT", "development") != "production"
        else "postgresql://user:password@localhost/eduecosystem",
    )
    MONGO_URL: str = os.getenv("MONGO_URL", "mongodb://127.0.0.1:27017")

    # Security - SECRET_KEY must be set in production
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        # Generate a random key for development, but require it in production
        secrets.token_urlsafe(32)
        if os.getenv("ENVIRONMENT", "development") == "development"
        else "",  # Empty string will trigger validation error in production
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v, info):
        """Ensure SECRET_KEY is set in production"""
        environment = info.data.get("ENVIRONMENT", "development")
        if environment == "production" and not v:
            raise ValueError(
                "SECRET_KEY must be set in production environment. "
                "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        if environment == "production" and len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters in production")
        return v

    # CORS Configuration - Parse from environment for production flexibility
    @property
    def BACKEND_CORS_ORIGINS(self) -> list[str]:
        """Parse CORS origins from environment variable (comma-separated)"""
        origins_str = os.getenv(
            "BACKEND_CORS_ORIGINS", "https://d2azz9jngd0rmq.amplifyapp.com,https://a7z4kjysmp.us-east-1.awsapprunner.com,http://localhost:3000,http://localhost:3001,http://localhost:8000"
        )
        return [origin.strip() for origin in origins_str.split(",") if origin.strip()]

    # Email Configuration
    MAIL_USERNAME: str = os.getenv("MAIL_USERNAME", "your_email@gmail.com")
    MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD", "your_app_password")
    MAIL_FROM: str = os.getenv("MAIL_FROM", "your_email@gmail.com")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", 587))
    MAIL_SERVER: str = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_FROM_NAME: str = os.getenv("MAIL_FROM_NAME", "Holistic Learning Ecosystem")
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True
    MAIL_SUPPRESS_SEND: bool = int(
        os.getenv("MAIL_SUPPRESS_SEND", 1)
    )  # Default to 1 (True) for dev

    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB: int = int(os.getenv("REDIS_DB", 0))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")

    @field_validator("REDIS_PASSWORD")
    @classmethod
    def validate_redis_password(cls, v, info):
        """Warn if Redis is used without password in production"""
        environment = info.data.get("ENVIRONMENT", "development")
        if environment == "production" and not v:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(
                "REDIS_PASSWORD not set in production. "
                "Redis cache will be accessible without authentication. "
                "This is a security risk if Redis is exposed publicly."
            )
        return v

    @property
    def REDIS_URL(self) -> str:
        """Construct Redis URL from components"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Celery Configuration
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = os.getenv(
        "CELERY_RESULT_BACKEND", "redis://localhost:6379/2"
    )

    # Stripe Configuration
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "sk_test_placeholder")
    STRIPE_PUBLISHABLE_KEY: str = os.getenv(
        "STRIPE_PUBLISHABLE_KEY", "pk_test_placeholder"
    )
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_placeholder")
    PREMIUM_PRICE_ID: str = os.getenv("PREMIUM_PRICE_ID", "price_placeholder")

    # File Storage Configuration
    STORAGE_BACKEND: str = os.getenv("STORAGE_BACKEND", "local")  # Options: local, s3
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_S3_BUCKET: str = os.getenv("AWS_S3_BUCKET", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")

    # Virus Scanning Configuration
    ENABLE_VIRUS_SCAN: bool = os.getenv("ENABLE_VIRUS_SCAN", "false").lower() == "true"
    CLAMAV_HOST: str = os.getenv("CLAMAV_HOST", "localhost")
    CLAMAV_PORT: int = int(os.getenv("CLAMAV_PORT", "3310"))

    # Monitoring & Error Tracking
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")  # Leave empty to disable Sentry
    APP_VERSION: str = os.getenv("APP_VERSION", "2.0.0")

    # AI Configuration (OpenRouter) - Multiple models for redundancy
    # Primary: Gemini 2.0 Flash (free, fast)
    OPENROUTER_API_KEY: str = os.getenv(
        "OPENROUTER_API_KEY",
        "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"  # Gemini 2.0 Flash
    )
    
    # Legacy GROK_API_KEY for backward compatibility (uses Gemma 3 27B)
    GROK_API_KEY: str = os.getenv(
        "GROK_API_KEY",
        "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"  # Gemma 3 27B
    )
    
    # Alternative models (fallback options)
    LLAMA_API_KEY: str = os.getenv(
        "LLAMA_API_KEY",
        "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"  # Llama 3
    )
    MISTRAL_API_KEY: str = os.getenv(
        "MISTRAL_API_KEY",
        "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"  # Mistral
    )
    
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    
    # Default AI model to use
    DEFAULT_AI_MODEL: str = os.getenv("DEFAULT_AI_MODEL", "google/gemini-2.0-flash-exp:free")

    model_config = ConfigDict(case_sensitive=True)


settings = Settings()
