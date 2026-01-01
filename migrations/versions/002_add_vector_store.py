"""Add vector store tables for RAG.

Revision ID: 002_add_vector_store
Revises: 001_initial_schema
Create Date: 2025-01-01

This migration adds:
- documents table with pgvector embedding column
- HNSW index for fast similarity search
- GIN indexes for array filtering
- Full-text search configuration
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "002_add_vector_store"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Create documents table
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("source_id", sa.String(255), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("zones", postgresql.ARRAY(sa.String()), default=[]),
        sa.Column("themes", postgresql.ARRAY(sa.String()), default=[]),
        sa.Column("metadata", postgresql.JSONB(), default={}),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Convert embedding column to vector type
    op.execute("""
        ALTER TABLE documents 
        ALTER COLUMN embedding TYPE vector(1536) 
        USING embedding::vector(1536)
    """)

    # Create HNSW index for fast similarity search
    op.execute("""
        CREATE INDEX ix_documents_embedding_hnsw 
        ON documents 
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)

    # Create GIN indexes for array containment queries
    op.execute("""
        CREATE INDEX ix_documents_zones_gin 
        ON documents 
        USING gin (zones)
    """)

    op.execute("""
        CREATE INDEX ix_documents_themes_gin 
        ON documents 
        USING gin (themes)
    """)

    # Create full-text search index
    op.execute("""
        CREATE INDEX ix_documents_content_fts 
        ON documents 
        USING gin (to_tsvector('english', content))
    """)

    # Create index on source_type for filtering
    op.create_index("ix_documents_source_type", "documents", ["source_type"])

    # Create index on created_at for time-based queries
    op.create_index("ix_documents_created_at", "documents", ["created_at"])

    # Create claims table for verification
    op.create_table(
        "claims",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("article_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("claim_text", sa.Text(), nullable=False),
        sa.Column("claim_type", sa.String(50), nullable=False),
        sa.Column("source_sentence", sa.Text(), nullable=True),
        sa.Column("verification_status", sa.String(50), default="unverified"),
        sa.Column("verification_score", sa.Float(), nullable=True),
        sa.Column("evidence", postgresql.JSONB(), default=[]),
        sa.Column("independent_sources", sa.Integer(), default=0),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
    )

    op.create_index("ix_claims_article_id", "claims", ["article_id"])
    op.create_index("ix_claims_verification_status", "claims", ["verification_status"])

    # Create escalations table
    op.create_table(
        "escalations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("story_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("pipeline_run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("priority", sa.String(20), nullable=False),
        sa.Column("reason", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), default="pending"),
        sa.Column("story_headline", sa.String(500), nullable=False),
        sa.Column("quality_score", sa.Float(), nullable=False),
        sa.Column("quality_details", postgresql.JSONB(), default={}),
        sa.Column("concerns", postgresql.ARRAY(sa.String()), default=[]),
        sa.Column("draft_content", sa.Text(), nullable=True),
        sa.Column("analysis_summary", sa.Text(), nullable=True),
        sa.Column("reviewer", sa.String(255), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
    )

    op.create_index("ix_escalations_status", "escalations", ["status"])
    op.create_index("ix_escalations_priority", "escalations", ["priority"])
    op.create_index("ix_escalations_created_at", "escalations", ["created_at"])


def downgrade() -> None:
    op.drop_table("escalations")
    op.drop_table("claims")
    op.drop_table("documents")
    op.execute("DROP EXTENSION IF EXISTS vector")

