"""
Settings API routes.

Provides endpoints for system configuration.
"""

from typing import Any
from pydantic import BaseModel, Field

from fastapi import APIRouter, HTTPException

from undertow.config import get_settings

router = APIRouter(prefix="/settings", tags=["Settings"])


class PipelineSettings(BaseModel):
    """Pipeline configuration."""
    
    daily_article_count: int = Field(default=5, ge=1, le=20)
    pipeline_start_hour: int = Field(default=4, ge=0, le=23)
    newsletter_publish_hour: int = Field(default=10, ge=0, le=23)
    daily_budget: float = Field(default=50.0, ge=1, le=500)


class QualityGateSettings(BaseModel):
    """Quality gate thresholds."""
    
    foundation_gate: float = Field(default=0.75, ge=0.5, le=0.99)
    analysis_gate: float = Field(default=0.80, ge=0.5, le=0.99)
    adversarial_gate: float = Field(default=0.80, ge=0.5, le=0.99)
    output_gate: float = Field(default=0.85, ge=0.5, le=0.99)


class ModelSettings(BaseModel):
    """AI model configuration."""
    
    default_provider: str = Field(default="anthropic")
    frontier_model: str = Field(default="claude-sonnet-4-20250514")
    high_model: str = Field(default="claude-sonnet-4-20250514")
    standard_model: str = Field(default="gpt-4o-mini")
    fast_model: str = Field(default="claude-3-5-haiku-20241022")


class NotificationSettings(BaseModel):
    """Notification configuration."""
    
    alert_email: str = Field(default="")
    slack_webhook_enabled: bool = Field(default=False)
    webhook_url: str = Field(default="")


class SystemSettings(BaseModel):
    """Complete system settings."""
    
    pipeline: PipelineSettings = Field(default_factory=PipelineSettings)
    quality_gates: QualityGateSettings = Field(default_factory=QualityGateSettings)
    models: ModelSettings = Field(default_factory=ModelSettings)
    notifications: NotificationSettings = Field(default_factory=NotificationSettings)


# In-memory settings storage (would be database in production)
_current_settings: SystemSettings = SystemSettings()


@router.get("", response_model=SystemSettings)
async def get_system_settings() -> SystemSettings:
    """
    Get current system settings.
    """
    return _current_settings


@router.put("", response_model=SystemSettings)
async def update_system_settings(settings: SystemSettings) -> SystemSettings:
    """
    Update system settings.
    """
    global _current_settings
    _current_settings = settings
    return _current_settings


@router.get("/pipeline", response_model=PipelineSettings)
async def get_pipeline_settings() -> PipelineSettings:
    """Get pipeline settings."""
    return _current_settings.pipeline


@router.put("/pipeline", response_model=PipelineSettings)
async def update_pipeline_settings(settings: PipelineSettings) -> PipelineSettings:
    """Update pipeline settings."""
    _current_settings.pipeline = settings
    return settings


@router.get("/quality-gates", response_model=QualityGateSettings)
async def get_quality_gate_settings() -> QualityGateSettings:
    """Get quality gate thresholds."""
    return _current_settings.quality_gates


@router.put("/quality-gates", response_model=QualityGateSettings)
async def update_quality_gate_settings(settings: QualityGateSettings) -> QualityGateSettings:
    """Update quality gate thresholds."""
    _current_settings.quality_gates = settings
    return settings


@router.get("/models", response_model=ModelSettings)
async def get_model_settings() -> ModelSettings:
    """Get AI model settings."""
    return _current_settings.models


@router.put("/models", response_model=ModelSettings)
async def update_model_settings(settings: ModelSettings) -> ModelSettings:
    """Update AI model settings."""
    _current_settings.models = settings
    return settings


@router.get("/notifications", response_model=NotificationSettings)
async def get_notification_settings() -> NotificationSettings:
    """Get notification settings."""
    return _current_settings.notifications


@router.put("/notifications", response_model=NotificationSettings)
async def update_notification_settings(settings: NotificationSettings) -> NotificationSettings:
    """Update notification settings."""
    _current_settings.notifications = settings
    return settings


@router.post("/reset")
async def reset_to_defaults() -> dict[str, str]:
    """Reset all settings to defaults."""
    global _current_settings
    _current_settings = SystemSettings()
    return {"status": "reset", "message": "Settings reset to defaults"}


@router.get("/environment")
async def get_environment_info() -> dict[str, Any]:
    """
    Get environment information (non-sensitive).
    
    Returns system configuration derived from environment.
    """
    settings = get_settings()
    
    return {
        "environment": settings.environment,
        "debug": settings.debug,
        "database_configured": bool(settings.database_url),
        "redis_configured": bool(settings.redis_url),
        "anthropic_configured": bool(settings.anthropic_api_key),
        "openai_configured": bool(settings.openai_api_key),
        "sendgrid_configured": bool(settings.sendgrid_api_key),
    }

