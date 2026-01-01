"""
Article model for generated content.
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Index, String, Text, Float
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from undertow.models.base import Base, TimestampMixin, UUIDMixin


class ArticleStatus(str, Enum):
    """Article lifecycle status."""

    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Article(Base, UUIDMixin, TimestampMixin):
    """
    Published article model.

    Represents a fully analyzed and written article ready for
    publication in the newsletter.
    """

    __tablename__ = "articles"

    # Core fields
    headline: Mapped[str] = mapped_column(String(500), nullable=False)
    subhead: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)

    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    read_time_minutes: Mapped[int] = mapped_column(default=5)

    # Status and dates
    status: Mapped[ArticleStatus] = mapped_column(
        SQLEnum(ArticleStatus),
        default=ArticleStatus.DRAFT,
        nullable=False,
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Quality metrics
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    story_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("stories.id"),
        nullable=False,
    )
    story: Mapped["Story"] = relationship(back_populates="articles")

    pipeline_run_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("pipeline_runs.id"),
        nullable=True,
    )

    # Metadata (tags, zones, themes, sources)
    zones: Mapped[list[str]] = mapped_column(JSONB, default=list)
    themes: Mapped[list[str]] = mapped_column(JSONB, default=list)
    sources: Mapped[list[dict]] = mapped_column(JSONB, default=list)

    # Analysis data (preserved for reference)
    analysis_data: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        Index("ix_articles_status", "status"),
        Index("ix_articles_published_at", "published_at"),
        Index("ix_articles_zones", "zones", postgresql_using="gin"),
    )

    def __repr__(self) -> str:
        return f"<Article {self.slug}>"


# Import at end to avoid circular import
from undertow.models.story import Story  # noqa: E402

