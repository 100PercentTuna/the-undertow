"""
Database configuration and session management.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from undertow.config import settings
from undertow.models.base import Base

# Global engine instance
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


async def init_db() -> None:
    """
    Initialize database connection pool.

    Should be called during application startup.
    """
    global _engine, _session_factory

    _engine = create_async_engine(
        settings.database_url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_pool_max_overflow,
        pool_pre_ping=True,
        echo=settings.debug,
    )

    _session_factory = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


async def close_db() -> None:
    """
    Close database connection pool.

    Should be called during application shutdown.
    """
    global _engine

    if _engine:
        await _engine.dispose()
        _engine = None


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get a database session for dependency injection.

    Yields:
        AsyncSession for database operations
    """
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    async with _session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_tables() -> None:
    """
    Create all tables in the database.

    For development/testing only. Use Alembic migrations in production.
    """
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables() -> None:
    """
    Drop all tables in the database.

    For development/testing only. Use with extreme caution.
    """
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def get_engine() -> AsyncEngine:
    """Get the global database engine."""
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _engine

