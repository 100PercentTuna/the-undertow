"""
Story model for ingested stories.
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SQLEnum, Index, String, Text, Float
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from undertow.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from undertow.models.article import Article


class StoryStatus(str, Enum):
    """Story processing status."""

    PENDING = "pending"  # Awaiting analysis
    ANALYZING = "analyzing"  # Currently being analyzed
    ANALYZED = "analyzed"  # Analysis complete
    SELECTED = "selected"  # Selected for publication
    REJECTED = "rejected"  # Rejected (low quality/relevance)
    PUBLISHED = "published"  # Article published


class Zone(str, Enum):
    """The 42 global coverage zones."""

    WESTERN_EUROPE = "western_europe"
    SOUTHERN_EUROPE = "southern_europe"
    NORDIC_BALTIC = "nordic_baltic"
    BRITISH_ISLES = "british_isles"
    CENTRAL_EUROPE = "central_europe"
    WESTERN_BALKANS = "western_balkans"
    EASTERN_EUROPE = "eastern_europe"
    SOUTH_CAUCASUS = "south_caucasus"
    RUSSIA_CORE = "russia_core"
    CENTRAL_ASIA_WEST = "central_asia_west"
    CENTRAL_ASIA_EAST = "central_asia_east"
    LEVANT = "levant"
    GULF_GCC = "gulf_gcc"
    IRAQ = "iraq"
    IRAN = "iran"
    TURKEY = "turkey"
    MAGHREB = "maghreb"
    EGYPT = "egypt"
    HORN_OF_AFRICA = "horn_of_africa"
    EAST_AFRICA = "east_africa"
    GREAT_LAKES = "great_lakes"
    SAHEL = "sahel"
    WEST_AFRICA = "west_africa"
    SOUTHERN_AFRICA = "southern_africa"
    INDIA = "india"
    PAKISTAN_AFGHANISTAN = "pakistan_afghanistan"
    SOUTH_ASIA_PERIPHERY = "south_asia_periphery"
    CHINA = "china"
    TAIWAN = "taiwan"
    KOREA = "korea"
    JAPAN = "japan"
    MONGOLIA = "mongolia"
    MAINLAND_SEA = "mainland_sea"
    MARITIME_SEA = "maritime_sea"
    AUSTRALIA_NZ = "australia_nz"
    PACIFIC_ISLANDS = "pacific_islands"
    USA = "usa"
    CANADA = "canada"
    MEXICO_CENTRAL_AMERICA = "mexico_central_america"
    CARIBBEAN = "caribbean"
    ANDEAN = "andean"
    SOUTHERN_CONE = "southern_cone"


class Story(Base, UUIDMixin, TimestampMixin):
    """
    Ingested story model.

    Represents a story collected from sources that may be
    analyzed and turned into an article.
    """

    __tablename__ = "stories"

    # Core fields
    headline: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Source information
    source_name: Mapped[str] = mapped_column(String(200), nullable=False)
    source_url: Mapped[str] = mapped_column(String(2000), nullable=False, unique=True)
    source_published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Classification
    primary_zone: Mapped[Zone] = mapped_column(SQLEnum(Zone), nullable=False)
    secondary_zones: Mapped[list[str]] = mapped_column(JSONB, default=list)

    # Status
    status: Mapped[StoryStatus] = mapped_column(
        SQLEnum(StoryStatus),
        default=StoryStatus.PENDING,
        nullable=False,
    )

    # Scoring
    relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    importance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    complexity_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Analysis results
    key_events: Mapped[list[str]] = mapped_column(JSONB, default=list)
    primary_actors: Mapped[list[str]] = mapped_column(JSONB, default=list)
    themes: Mapped[list[str]] = mapped_column(JSONB, default=list)

    # Full analysis data (motivation, chains, etc.)
    analysis_data: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Relationships
    articles: Mapped[list["Article"]] = relationship(back_populates="story")

    __table_args__ = (
        Index("ix_stories_status", "status"),
        Index("ix_stories_primary_zone", "primary_zone"),
        Index("ix_stories_source_published_at", "source_published_at"),
        Index("ix_stories_relevance", "relevance_score"),
    )

    def __repr__(self) -> str:
        return f"<Story {self.headline[:50]}...>"

