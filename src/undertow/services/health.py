"""
Comprehensive health check service.

Checks all system components and reports status.
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import structlog

from undertow.config import settings

logger = structlog.get_logger()


class HealthStatus(str, Enum):
    """Health status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ComponentHealth:
    """Health of a single component."""

    name: str
    status: HealthStatus
    latency_ms: float | None = None
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemHealth:
    """Overall system health."""

    status: HealthStatus
    timestamp: datetime
    version: str
    components: list[ComponentHealth]
    uptime_seconds: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "version": self.version,
            "uptime_seconds": round(self.uptime_seconds, 2),
            "components": [
                {
                    "name": c.name,
                    "status": c.status.value,
                    "latency_ms": c.latency_ms,
                    "message": c.message,
                    "details": c.details,
                }
                for c in self.components
            ],
        }


class HealthCheckService:
    """
    Service for comprehensive health checks.

    Checks:
    - Database connectivity
    - Redis connectivity
    - LLM provider availability
    - Celery workers
    - Disk space
    - Memory usage
    """

    VERSION = "1.0.0"

    def __init__(self) -> None:
        """Initialize health check service."""
        self._start_time = time.time()

    @property
    def uptime_seconds(self) -> float:
        """Get uptime in seconds."""
        return time.time() - self._start_time

    async def check_all(self) -> SystemHealth:
        """
        Run all health checks.

        Returns:
            SystemHealth with status of all components
        """
        checks = await asyncio.gather(
            self._check_database(),
            self._check_redis(),
            self._check_llm_providers(),
            self._check_celery(),
            self._check_system_resources(),
            return_exceptions=True,
        )

        components = []
        for result in checks:
            if isinstance(result, Exception):
                components.append(
                    ComponentHealth(
                        name="unknown",
                        status=HealthStatus.UNHEALTHY,
                        message=str(result),
                    )
                )
            elif isinstance(result, list):
                components.extend(result)
            else:
                components.append(result)

        # Determine overall status
        if any(c.status == HealthStatus.UNHEALTHY for c in components):
            overall = HealthStatus.UNHEALTHY
        elif any(c.status == HealthStatus.DEGRADED for c in components):
            overall = HealthStatus.DEGRADED
        else:
            overall = HealthStatus.HEALTHY

        return SystemHealth(
            status=overall,
            timestamp=datetime.utcnow(),
            version=self.VERSION,
            components=components,
            uptime_seconds=self.uptime_seconds,
        )

    async def _check_database(self) -> ComponentHealth:
        """Check database connectivity."""
        start = time.time()

        try:
            from undertow.infrastructure.database import get_session

            async with get_session() as session:
                result = await session.execute("SELECT 1")
                result.scalar()

            latency = (time.time() - start) * 1000

            return ComponentHealth(
                name="database",
                status=HealthStatus.HEALTHY if latency < 100 else HealthStatus.DEGRADED,
                latency_ms=round(latency, 2),
                message="Connected" if latency < 100 else "Slow response",
                details={"database_url": settings.database_url[:20] + "..."},
            )

        except Exception as e:
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                latency_ms=(time.time() - start) * 1000,
                message=f"Connection failed: {str(e)[:100]}",
            )

    async def _check_redis(self) -> ComponentHealth:
        """Check Redis connectivity."""
        start = time.time()

        try:
            from undertow.infrastructure.cache import get_cache

            cache = get_cache()
            await cache.set("health_check", "ok", ttl=10)
            value = await cache.get("health_check")

            if value != "ok":
                raise ValueError("Cache read mismatch")

            latency = (time.time() - start) * 1000

            return ComponentHealth(
                name="redis",
                status=HealthStatus.HEALTHY if latency < 50 else HealthStatus.DEGRADED,
                latency_ms=round(latency, 2),
                message="Connected" if latency < 50 else "Slow response",
            )

        except Exception as e:
            return ComponentHealth(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                latency_ms=(time.time() - start) * 1000,
                message=f"Connection failed: {str(e)[:100]}",
            )

    async def _check_llm_providers(self) -> list[ComponentHealth]:
        """Check LLM provider availability."""
        components = []

        # Check Anthropic
        anthropic_status = HealthStatus.HEALTHY
        anthropic_msg = "API key configured"

        if not settings.anthropic_api_key:
            anthropic_status = HealthStatus.UNHEALTHY
            anthropic_msg = "API key not configured"

        components.append(
            ComponentHealth(
                name="anthropic",
                status=anthropic_status,
                message=anthropic_msg,
            )
        )

        # Check OpenAI
        openai_status = HealthStatus.HEALTHY
        openai_msg = "API key configured"

        if not settings.openai_api_key:
            openai_status = HealthStatus.DEGRADED  # Degraded, not unhealthy (it's fallback)
            openai_msg = "API key not configured (fallback unavailable)"

        components.append(
            ComponentHealth(
                name="openai",
                status=openai_status,
                message=openai_msg,
            )
        )

        return components

    async def _check_celery(self) -> ComponentHealth:
        """Check Celery workers."""
        try:
            from undertow.tasks.celery_app import celery_app

            # Inspect active workers
            inspect = celery_app.control.inspect()
            active = inspect.active()

            if active is None:
                return ComponentHealth(
                    name="celery",
                    status=HealthStatus.DEGRADED,
                    message="No workers responding (may be starting)",
                )

            worker_count = len(active)
            task_count = sum(len(tasks) for tasks in active.values())

            return ComponentHealth(
                name="celery",
                status=HealthStatus.HEALTHY if worker_count > 0 else HealthStatus.DEGRADED,
                message=f"{worker_count} workers, {task_count} active tasks",
                details={
                    "workers": worker_count,
                    "active_tasks": task_count,
                },
            )

        except Exception as e:
            return ComponentHealth(
                name="celery",
                status=HealthStatus.DEGRADED,
                message=f"Cannot inspect workers: {str(e)[:50]}",
            )

    async def _check_system_resources(self) -> list[ComponentHealth]:
        """Check system resources (disk, memory)."""
        components = []

        try:
            import shutil
            import psutil
        except ImportError:
            return [
                ComponentHealth(
                    name="system",
                    status=HealthStatus.DEGRADED,
                    message="psutil not installed for resource checks",
                )
            ]

        # Check disk space
        try:
            total, used, free = shutil.disk_usage("/")
            free_pct = (free / total) * 100

            if free_pct < 10:
                disk_status = HealthStatus.UNHEALTHY
            elif free_pct < 20:
                disk_status = HealthStatus.DEGRADED
            else:
                disk_status = HealthStatus.HEALTHY

            components.append(
                ComponentHealth(
                    name="disk",
                    status=disk_status,
                    message=f"{free_pct:.1f}% free ({free // (1024**3)}GB)",
                    details={
                        "total_gb": total // (1024**3),
                        "free_gb": free // (1024**3),
                        "free_pct": round(free_pct, 1),
                    },
                )
            )
        except Exception as e:
            components.append(
                ComponentHealth(
                    name="disk",
                    status=HealthStatus.DEGRADED,
                    message=f"Cannot check: {str(e)[:50]}",
                )
            )

        # Check memory
        try:
            memory = psutil.virtual_memory()
            available_pct = memory.available / memory.total * 100

            if available_pct < 10:
                mem_status = HealthStatus.UNHEALTHY
            elif available_pct < 20:
                mem_status = HealthStatus.DEGRADED
            else:
                mem_status = HealthStatus.HEALTHY

            components.append(
                ComponentHealth(
                    name="memory",
                    status=mem_status,
                    message=f"{available_pct:.1f}% available",
                    details={
                        "total_gb": round(memory.total / (1024**3), 1),
                        "available_gb": round(memory.available / (1024**3), 1),
                        "available_pct": round(available_pct, 1),
                    },
                )
            )
        except Exception as e:
            components.append(
                ComponentHealth(
                    name="memory",
                    status=HealthStatus.DEGRADED,
                    message=f"Cannot check: {str(e)[:50]}",
                )
            )

        return components

    async def quick_check(self) -> bool:
        """
        Quick health check (just database).

        Returns:
            True if healthy
        """
        try:
            result = await self._check_database()
            return result.status == HealthStatus.HEALTHY
        except Exception:
            return False


# Global instance
_health_service: HealthCheckService | None = None


def get_health_service() -> HealthCheckService:
    """Get global health service instance."""
    global _health_service
    if _health_service is None:
        _health_service = HealthCheckService()
    return _health_service

