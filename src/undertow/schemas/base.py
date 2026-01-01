"""
Base Pydantic schemas with strict validation.

ALL schemas MUST inherit from StrictModel.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    """
    Base model with strict validation.

    ALL schemas MUST inherit from this.

    Features:
    - Forbids extra fields (catches typos)
    - Validates on assignment (catches mutations)
    - Uses enum values in serialization
    - Validates default values
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        use_enum_values=True,
        validate_default=True,
        str_strip_whitespace=True,
        json_schema_extra={"examples": []},
    )


class UUIDMixin(StrictModel):
    """Mixin for models with UUID primary key."""

    id: UUID = Field(..., description="Unique identifier")


class TimestampMixin(StrictModel):
    """Mixin for models with timestamp fields."""

    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")


class PaginationParams(StrictModel):
    """Pagination parameters for list endpoints."""

    page: int = Field(default=1, ge=1, le=10000, description="Page number")
    per_page: int = Field(default=50, ge=1, le=200, description="Items per page")

    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.per_page


class PaginatedResponse(StrictModel):
    """Paginated response wrapper."""

    items: list[Any] = Field(..., description="List of items")
    total: int = Field(..., ge=0, description="Total number of items")
    page: int = Field(..., ge=1, description="Current page")
    per_page: int = Field(..., ge=1, description="Items per page")
    pages: int = Field(..., ge=0, description="Total number of pages")

    @classmethod
    def create(
        cls,
        items: list[Any],
        total: int,
        page: int,
        per_page: int,
    ) -> "PaginatedResponse":
        """Create paginated response with calculated pages."""
        pages = (total + per_page - 1) // per_page if per_page > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
        )


class HealthResponse(StrictModel):
    """Health check response."""

    status: str = Field(..., description="Health status")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Environment name")


class ErrorResponse(StrictModel):
    """Standard error response."""

    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: dict[str, Any] | None = Field(None, description="Additional error details")

