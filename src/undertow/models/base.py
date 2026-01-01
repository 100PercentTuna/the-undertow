"""
SQLAlchemy base model configuration.
"""

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Base class for all models.

    Provides:
    - UUID primary key
    - Common configuration
    - Type annotation support
    """

    # Enable strict typing
    type_annotation_map = {
        datetime: DateTime(timezone=True),
    }


class TimestampMixin:
    """
    Mixin for created_at and updated_at timestamps.

    Add to any model that needs timestamp tracking:

        class MyModel(Base, TimestampMixin):
            ...
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
    )


class UUIDMixin:
    """
    Mixin for UUID primary key.

    Add to any model that needs UUID pk:

        class MyModel(Base, UUIDMixin):
            ...
    """

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

