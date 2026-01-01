"""
Pipeline execution models.
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Index, String, Text, Float, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from undertow.models.base import Base, TimestampMixin, UUIDMixin


class PipelineStatus(str, Enum):
    """Pipeline run status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PipelineRun(Base, UUIDMixin, TimestampMixin):
    """
    Pipeline execution record.

    Tracks a complete run of the daily analysis pipeline.
    """

    __tablename__ = "pipeline_runs"

    # Timing
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Status
    status: Mapped[PipelineStatus] = mapped_column(
        SQLEnum(PipelineStatus),
        default=PipelineStatus.PENDING,
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Statistics
    stories_processed: Mapped[int] = mapped_column(Integer, default=0)
    articles_generated: Mapped[int] = mapped_column(Integer, default=0)
    total_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)

    # Quality metrics
    avg_quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Detailed metrics
    metrics: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Agent executions
    agent_executions: Mapped[list["AgentExecution"]] = relationship(
        back_populates="pipeline_run",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_pipeline_runs_status", "status"),
        Index("ix_pipeline_runs_started_at", "started_at"),
    )

    def __repr__(self) -> str:
        return f"<PipelineRun {self.id} {self.status}>"


class AgentExecution(Base, UUIDMixin, TimestampMixin):
    """
    Individual agent execution record.

    Tracks each agent call within a pipeline run.
    """

    __tablename__ = "agent_executions"

    # Parent pipeline
    pipeline_run_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("pipeline_runs.id"),
        nullable=False,
    )
    pipeline_run: Mapped["PipelineRun"] = relationship(back_populates="agent_executions")

    # Related story
    story_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("stories.id"),
        nullable=True,
    )

    # Agent info
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    agent_version: Mapped[str] = mapped_column(String(20), nullable=False)

    # Timing
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Model info
    model_used: Mapped[str] = mapped_column(String(100), nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)

    # Result
    success: Mapped[bool] = mapped_column(default=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Input/output preview (truncated)
    input_preview: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_preview: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_agent_executions_pipeline", "pipeline_run_id"),
        Index("ix_agent_executions_agent", "agent_name"),
        Index("ix_agent_executions_story", "story_id"),
    )

    def __repr__(self) -> str:
        return f"<AgentExecution {self.agent_name}>"

