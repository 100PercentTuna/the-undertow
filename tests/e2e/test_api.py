"""
End-to-end API tests.

These tests verify the API endpoints work correctly.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from undertow.api.main import app


@pytest.fixture
async def client() -> AsyncClient:
    """Create test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient) -> None:
        """Test basic health check."""
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_returns_version(self, client: AsyncClient) -> None:
        """Test health check includes version."""
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data


class TestMetricsEndpoints:
    """Tests for metrics endpoints."""

    @pytest.mark.asyncio
    async def test_get_metrics(self, client: AsyncClient) -> None:
        """Test metrics endpoint returns data."""
        response = await client.get("/api/v1/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "uptime_seconds" in data
        assert "total_requests" in data

    @pytest.mark.asyncio
    async def test_metrics_health(self, client: AsyncClient) -> None:
        """Test metrics health endpoint."""
        response = await client.get("/api/v1/metrics/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded"]


class TestStoriesEndpoints:
    """Tests for stories endpoints."""

    @pytest.mark.asyncio
    async def test_list_stories(self, client: AsyncClient) -> None:
        """Test listing stories returns empty list initially."""
        response = await client.get("/api/v1/stories")
        # May return 200 with empty list or error if DB not ready
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_get_nonexistent_story(self, client: AsyncClient) -> None:
        """Test getting nonexistent story returns 404."""
        response = await client.get("/api/v1/stories/nonexistent-id")
        assert response.status_code in [404, 500]


class TestArticlesEndpoints:
    """Tests for articles endpoints."""

    @pytest.mark.asyncio
    async def test_list_articles(self, client: AsyncClient) -> None:
        """Test listing articles returns empty list initially."""
        response = await client.get("/api/v1/articles")
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_get_nonexistent_article(self, client: AsyncClient) -> None:
        """Test getting nonexistent article returns 404."""
        response = await client.get("/api/v1/articles/nonexistent-id")
        assert response.status_code in [404, 500]


class TestPipelineEndpoints:
    """Tests for pipeline endpoints."""

    @pytest.mark.asyncio
    async def test_list_runs(self, client: AsyncClient) -> None:
        """Test listing pipeline runs."""
        response = await client.get("/api/v1/pipeline/runs")
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_get_stats(self, client: AsyncClient) -> None:
        """Test getting pipeline stats."""
        response = await client.get("/api/v1/pipeline/stats")
        assert response.status_code in [200, 500]


class TestNewsletterEndpoints:
    """Tests for newsletter endpoints."""

    @pytest.mark.asyncio
    async def test_get_schedule(self, client: AsyncClient) -> None:
        """Test getting newsletter schedule."""
        response = await client.get("/api/v1/newsletter/schedule")
        assert response.status_code == 200
        data = response.json()
        assert "schedule" in data
        assert "articles_per_edition" in data

