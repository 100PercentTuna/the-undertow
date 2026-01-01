"""
Application configuration using Pydantic Settings.

All configuration is loaded from environment variables with sensible defaults.
"""

from enum import Enum
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Application environment."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class AIProvider(str, Enum):
    """Supported AI providers."""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    BEST_FIT = "best_fit"


class Settings(BaseSettings):
    """
    Application settings with validation.

    All settings are loaded from environment variables.
    Prefix: None (direct mapping)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # =========================================================================
    # Application
    # =========================================================================
    app_name: str = Field(default="The Undertow")
    app_env: Environment = Field(default=Environment.DEVELOPMENT)
    debug: bool = Field(default=False)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")

    # =========================================================================
    # Database
    # =========================================================================
    database_url: str = Field(
        default="postgresql+asyncpg://undertow:undertow@localhost:5432/undertow",
        description="PostgreSQL connection URL",
    )
    database_pool_size: int = Field(default=20, ge=5, le=100)
    database_pool_max_overflow: int = Field(default=10, ge=0, le=50)

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v.startswith("postgresql"):
            raise ValueError("Only PostgreSQL is supported")
        return v

    # =========================================================================
    # Redis
    # =========================================================================
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )

    # =========================================================================
    # AI Providers
    # =========================================================================
    anthropic_api_key: str = Field(default="", description="Anthropic API key")
    openai_api_key: str = Field(default="", description="OpenAI API key")

    # AI Configuration
    ai_provider_preference: AIProvider = Field(
        default=AIProvider.ANTHROPIC,
        description="Preferred AI provider",
    )
    ai_daily_budget_usd: float = Field(
        default=1.50,  # ~$1/day target
        ge=0.5,
        le=100.0,
        description="Daily budget limit in USD",
    )
    ai_quality_threshold: float = Field(
        default=0.80,
        ge=0.5,
        le=1.0,
        description="Minimum quality score for output",
    )

    # =========================================================================
    # Celery
    # =========================================================================
    celery_broker_url: str = Field(
        default="redis://localhost:6379/1",
        description="Celery broker URL",
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/2",
        description="Celery result backend URL",
    )

    # =========================================================================
    # Email & Notifications
    # =========================================================================
    # Email Provider: "smtp" (Gmail/O365) or "postmark" (Postmark API)
    email_provider: str = Field(
        default="smtp",
        description="Email provider: 'smtp' (Gmail/O365) or 'postmark'",
    )
    
    # SMTP Configuration (for Gmail/O365/any SMTP server)
    smtp_host: str = Field(
        default="smtp.gmail.com",
        description="SMTP server hostname (Gmail: smtp.gmail.com, O365: smtp.office365.com)",
    )
    smtp_port: int = Field(
        default=587,
        ge=1,
        le=65535,
        description="SMTP server port (587 for TLS, 465 for SSL)",
    )
    smtp_username: str = Field(
        default="",
        description="SMTP username (your email address)",
    )
    smtp_password: str = Field(
        default="",
        description="SMTP password (App Password for Gmail/O365, not regular password)",
    )
    smtp_use_tls: bool = Field(
        default=True,
        description="Use TLS encryption (True for port 587, False for port 465 with SSL)",
    )
    
    # Postmark Configuration (alternative to SMTP)
    postmark_api_key: str = Field(
        default="",
        description="Postmark API key (if using Postmark instead of SMTP)",
    )
    postmark_server_token: str = Field(
        default="",
        description="Postmark server token (same as API key, for clarity)",
    )
    from_email: str = Field(
        default="",
        description="From email address (must match SMTP username for Gmail)",
    )
    alert_email: str = Field(
        default="",
        description="Email for system alerts",
    )
    slack_webhook_url: str = Field(
        default="",
        description="Slack webhook URL for notifications (optional)",
    )
    app_url: str = Field(
        default="http://localhost:3000",
        description="Application URL for links in notifications",
    )

    # =========================================================================
    # AWS S3
    # =========================================================================
    aws_access_key_id: str = Field(default="", description="AWS access key")
    aws_secret_access_key: str = Field(default="", description="AWS secret key")
    aws_s3_bucket: str = Field(default="undertow-articles", description="S3 bucket name")
    aws_region: str = Field(default="us-east-1", description="AWS region")

    # =========================================================================
    # Security
    # =========================================================================
    secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for signing",
    )
    api_key_header: str = Field(default="X-API-Key", description="API key header name")
    api_keys: list[str] = Field(
        default_factory=list,
        description="Valid API keys (comma-separated in env)",
    )

    @field_validator("api_keys", mode="before")
    @classmethod
    def parse_api_keys(cls, v):
        """Parse comma-separated API keys."""
        if isinstance(v, str):
            return [k.strip() for k in v.split(",") if k.strip()]
        return v or []

    # =========================================================================
    # Pipeline Schedule
    # =========================================================================
    pipeline_start_hour: int = Field(
        default=20,  # 8:30 PM UTC = 4:30 AM SGT
        ge=0,
        le=23,
        description="Hour (UTC) to start daily pipeline",
    )
    pipeline_start_minute: int = Field(
        default=30,
        ge=0,
        le=59,
        description="Minute to start daily pipeline",
    )
    newsletter_publish_hour: int = Field(
        default=20,
        ge=0,
        le=23,
        description="Hour (UTC) to publish newsletter",
    )
    newsletter_recipients: str = Field(
        default="",
        description="Comma-separated list of newsletter recipients",
    )

    # =========================================================================
    # Quality Gates
    # =========================================================================
    quality_gate_foundation: float = Field(default=0.75, ge=0.5, le=1.0)
    quality_gate_analysis: float = Field(default=0.80, ge=0.5, le=1.0)
    quality_gate_adversarial: float = Field(default=0.80, ge=0.5, le=1.0)
    quality_gate_output: float = Field(default=0.85, ge=0.5, le=1.0)

    # =========================================================================
    # Properties
    # =========================================================================
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == Environment.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env == Environment.PRODUCTION


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()


# Convenience alias
settings = get_settings()

