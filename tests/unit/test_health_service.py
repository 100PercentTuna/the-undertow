"""
Unit tests for Health Check service.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from undertow.services.health import (
    HealthCheckService,
    HealthStatus,
    ComponentHealth,
    SystemHealth,
)


@pytest.fixture
def health_service() -> HealthCheckService:
    """Create health service."""
    return HealthCheckService()


class TestHealthCheckService:
    """Tests for HealthCheckService."""

    def test_uptime(self, health_service: HealthCheckService) -> None:
        """Test uptime tracking."""
        import time

        # Should have some uptime
        time.sleep(0.1)
        assert health_service.uptime_seconds > 0

    @pytest.mark.asyncio
    async def test_check_all_returns_system_health(
        self,
        health_service: HealthCheckService,
    ) -> None:
        """Test check_all returns SystemHealth."""
        with patch.object(
            health_service, "_check_database", new_callable=AsyncMock
        ) as mock_db, patch.object(
            health_service, "_check_redis", new_callable=AsyncMock
        ) as mock_redis, patch.object(
            health_service, "_check_llm_providers", new_callable=AsyncMock
        ) as mock_llm, patch.object(
            health_service, "_check_celery", new_callable=AsyncMock
        ) as mock_celery, patch.object(
            health_service, "_check_system_resources", new_callable=AsyncMock
        ) as mock_sys:
            # Mock all checks to return healthy
            mock_db.return_value = ComponentHealth(
                name="database", status=HealthStatus.HEALTHY
            )
            mock_redis.return_value = ComponentHealth(
                name="redis", status=HealthStatus.HEALTHY
            )
            mock_llm.return_value = [
                ComponentHealth(name="anthropic", status=HealthStatus.HEALTHY)
            ]
            mock_celery.return_value = ComponentHealth(
                name="celery", status=HealthStatus.HEALTHY
            )
            mock_sys.return_value = [
                ComponentHealth(name="disk", status=HealthStatus.HEALTHY)
            ]

            result = await health_service.check_all()

            assert isinstance(result, SystemHealth)
            assert result.status == HealthStatus.HEALTHY
            assert len(result.components) >= 4

    @pytest.mark.asyncio
    async def test_degraded_status(
        self,
        health_service: HealthCheckService,
    ) -> None:
        """Test degraded overall status when component is degraded."""
        with patch.object(
            health_service, "_check_database", new_callable=AsyncMock
        ) as mock_db, patch.object(
            health_service, "_check_redis", new_callable=AsyncMock
        ) as mock_redis, patch.object(
            health_service, "_check_llm_providers", new_callable=AsyncMock
        ) as mock_llm, patch.object(
            health_service, "_check_celery", new_callable=AsyncMock
        ) as mock_celery, patch.object(
            health_service, "_check_system_resources", new_callable=AsyncMock
        ) as mock_sys:
            # One component degraded
            mock_db.return_value = ComponentHealth(
                name="database", status=HealthStatus.DEGRADED
            )
            mock_redis.return_value = ComponentHealth(
                name="redis", status=HealthStatus.HEALTHY
            )
            mock_llm.return_value = []
            mock_celery.return_value = ComponentHealth(
                name="celery", status=HealthStatus.HEALTHY
            )
            mock_sys.return_value = []

            result = await health_service.check_all()

            assert result.status == HealthStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_unhealthy_status(
        self,
        health_service: HealthCheckService,
    ) -> None:
        """Test unhealthy overall status when component fails."""
        with patch.object(
            health_service, "_check_database", new_callable=AsyncMock
        ) as mock_db, patch.object(
            health_service, "_check_redis", new_callable=AsyncMock
        ) as mock_redis, patch.object(
            health_service, "_check_llm_providers", new_callable=AsyncMock
        ) as mock_llm, patch.object(
            health_service, "_check_celery", new_callable=AsyncMock
        ) as mock_celery, patch.object(
            health_service, "_check_system_resources", new_callable=AsyncMock
        ) as mock_sys:
            # One component unhealthy
            mock_db.return_value = ComponentHealth(
                name="database", status=HealthStatus.UNHEALTHY, message="Connection failed"
            )
            mock_redis.return_value = ComponentHealth(
                name="redis", status=HealthStatus.HEALTHY
            )
            mock_llm.return_value = []
            mock_celery.return_value = ComponentHealth(
                name="celery", status=HealthStatus.HEALTHY
            )
            mock_sys.return_value = []

            result = await health_service.check_all()

            assert result.status == HealthStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_quick_check(
        self,
        health_service: HealthCheckService,
    ) -> None:
        """Test quick health check."""
        with patch.object(
            health_service, "_check_database", new_callable=AsyncMock
        ) as mock_db:
            mock_db.return_value = ComponentHealth(
                name="database", status=HealthStatus.HEALTHY
            )

            result = await health_service.quick_check()

            assert result is True

    @pytest.mark.asyncio
    async def test_quick_check_failure(
        self,
        health_service: HealthCheckService,
    ) -> None:
        """Test quick health check failure."""
        with patch.object(
            health_service, "_check_database", new_callable=AsyncMock
        ) as mock_db:
            mock_db.return_value = ComponentHealth(
                name="database", status=HealthStatus.UNHEALTHY
            )

            result = await health_service.quick_check()

            assert result is False


class TestSystemHealth:
    """Tests for SystemHealth dataclass."""

    def test_to_dict(self) -> None:
        """Test SystemHealth to_dict conversion."""
        from datetime import datetime

        health = SystemHealth(
            status=HealthStatus.HEALTHY,
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            version="1.0.0",
            components=[
                ComponentHealth(
                    name="database",
                    status=HealthStatus.HEALTHY,
                    latency_ms=5.0,
                ),
            ],
            uptime_seconds=3600.0,
        )

        result = health.to_dict()

        assert result["status"] == "healthy"
        assert result["version"] == "1.0.0"
        assert result["uptime_seconds"] == 3600.0
        assert len(result["components"]) == 1
        assert result["components"][0]["name"] == "database"


class TestComponentHealth:
    """Tests for ComponentHealth dataclass."""

    def test_component_creation(self) -> None:
        """Test ComponentHealth creation."""
        component = ComponentHealth(
            name="test",
            status=HealthStatus.HEALTHY,
            latency_ms=10.5,
            message="All good",
            details={"extra": "info"},
        )

        assert component.name == "test"
        assert component.status == HealthStatus.HEALTHY
        assert component.latency_ms == 10.5
        assert component.details["extra"] == "info"

