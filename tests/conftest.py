"""
Pytest configuration and fixtures.
"""

import asyncio
from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from undertow.models.base import Base
from undertow.llm.router import ModelRouter
from undertow.llm.providers.base import LLMResponse


# Use a test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    session_factory = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session


@pytest.fixture
def mock_llm_response() -> LLMResponse:
    """Create mock LLM response."""
    return LLMResponse(
        content='{"test": "response"}',
        model="test-model",
        input_tokens=100,
        output_tokens=50,
        latency_ms=500,
        finish_reason="stop",
    )


@pytest.fixture
def mock_router(mock_llm_response) -> ModelRouter:
    """Create mock model router."""
    mock_provider = MagicMock()
    mock_provider.complete = AsyncMock(return_value=mock_llm_response)

    router = ModelRouter(
        providers={"mock": mock_provider},
        preference="mock",
        daily_budget=100.0,
    )

    return router

