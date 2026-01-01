"""Initial schema.

Revision ID: 001
Revises:
Create Date: 2026-01-01

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    op.execute("CREATE TYPE storystatus AS ENUM ('pending', 'analyzing', 'analyzed', 'published', 'archived', 'rejected')")
    op.execute("CREATE TYPE articlestatus AS ENUM ('draft', 'review', 'approved', 'published', 'archived')")
    op.execute("CREATE TYPE pipelinestatus AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled')")
    op.execute("""CREATE TYPE zone AS ENUM (
        'western_europe', 'southern_europe', 'nordic_baltic', 'british_isles',
        'central_europe', 'western_balkans', 'eastern_europe', 'south_caucasus',
        'russia_core', 'central_asia_west', 'central_asia_east',
        'levant', 'gulf_gcc', 'iraq', 'iran', 'turkey', 'maghreb', 'egypt',
        'horn_of_africa', 'east_africa', 'great_lakes', 'sahel', 'west_africa', 'southern_africa',
        'india', 'pakistan_afghanistan', 'south_asia_periphery',
        'china', 'taiwan', 'korea', 'japan', 'mongolia',
        'mainland_sea', 'maritime_sea',
        'australia_nz', 'pacific_islands',
        'usa', 'canada', 'mexico_central_america', 'caribbean', 'andean', 'southern_cone'
    )""")

    # Stories table
    op.create_table(
        "stories",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("headline", sa.String(500), nullable=False),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("source_url", sa.String(2000), nullable=True),
        sa.Column("source_name", sa.String(200), nullable=True),
        sa.Column("primary_zone", postgresql.ENUM(name="zone", create_type=False), nullable=True),
        sa.Column("secondary_zones", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("status", postgresql.ENUM(name="storystatus", create_type=False), nullable=False, server_default="pending"),
        sa.Column("relevance_score", sa.Float, nullable=True),
        sa.Column("importance_score", sa.Float, nullable=True),
        sa.Column("analysis_data", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), onupdate=sa.text("now()"), nullable=False),
    )

    # Articles table
    op.create_table(
        "articles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("story_id", sa.String(36), sa.ForeignKey("stories.id"), nullable=True),
        sa.Column("headline", sa.String(500), nullable=False),
        sa.Column("subhead", sa.String(500), nullable=True),
        sa.Column("slug", sa.String(200), nullable=True, unique=True),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("content", sa.Text, nullable=True),
        sa.Column("zones", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("themes", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("status", postgresql.ENUM(name="articlestatus", create_type=False), nullable=False, server_default="draft"),
        sa.Column("quality_score", sa.Float, nullable=True),
        sa.Column("read_time_minutes", sa.Integer, nullable=True),
        sa.Column("word_count", sa.Integer, nullable=True),
        sa.Column("analysis_metadata", postgresql.JSONB, nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), onupdate=sa.text("now()"), nullable=False),
    )

    # Pipeline runs table
    op.create_table(
        "pipeline_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("status", postgresql.ENUM(name="pipelinestatus", create_type=False), nullable=False, server_default="pending"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stories_processed", sa.Integer, nullable=True, server_default="0"),
        sa.Column("articles_generated", sa.Integer, nullable=True, server_default="0"),
        sa.Column("total_cost_usd", sa.Float, nullable=True, server_default="0"),
        sa.Column("avg_quality_score", sa.Float, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), onupdate=sa.text("now()"), nullable=False),
    )

    # Agent executions table
    op.create_table(
        "agent_executions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("pipeline_run_id", sa.String(36), sa.ForeignKey("pipeline_runs.id"), nullable=False),
        sa.Column("story_id", sa.String(36), sa.ForeignKey("stories.id"), nullable=True),
        sa.Column("agent_name", sa.String(100), nullable=False),
        sa.Column("agent_version", sa.String(20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer, nullable=True),
        sa.Column("model_used", sa.String(100), nullable=True),
        sa.Column("input_tokens", sa.Integer, nullable=True),
        sa.Column("output_tokens", sa.Integer, nullable=True),
        sa.Column("cost_usd", sa.Float, nullable=True),
        sa.Column("success", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("quality_score", sa.Float, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # Create indexes
    op.create_index("ix_stories_status", "stories", ["status"])
    op.create_index("ix_stories_primary_zone", "stories", ["primary_zone"])
    op.create_index("ix_stories_created_at", "stories", ["created_at"])
    op.create_index("ix_stories_relevance_score", "stories", ["relevance_score"])

    op.create_index("ix_articles_status", "articles", ["status"])
    op.create_index("ix_articles_slug", "articles", ["slug"])
    op.create_index("ix_articles_published_at", "articles", ["published_at"])
    op.create_index("ix_articles_story_id", "articles", ["story_id"])

    op.create_index("ix_pipeline_runs_status", "pipeline_runs", ["status"])
    op.create_index("ix_pipeline_runs_created_at", "pipeline_runs", ["created_at"])

    op.create_index("ix_agent_executions_pipeline_run_id", "agent_executions", ["pipeline_run_id"])
    op.create_index("ix_agent_executions_agent_name", "agent_executions", ["agent_name"])


def downgrade() -> None:
    op.drop_table("agent_executions")
    op.drop_table("pipeline_runs")
    op.drop_table("articles")
    op.drop_table("stories")

    op.execute("DROP TYPE zone")
    op.execute("DROP TYPE pipelinestatus")
    op.execute("DROP TYPE articlestatus")
    op.execute("DROP TYPE storystatus")

