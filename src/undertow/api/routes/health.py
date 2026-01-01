"""
Health check routes.
"""

from typing import Any

from fastapi import APIRouter, Response

from undertow.services.health import get_health_service, HealthStatus

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """
    Basic health check endpoint.

    Returns 200 if the service is running.
    Used by load balancers and container orchestrators.
    """
    return {"status": "ok"}


@router.get("/health/live")
async def liveness_check() -> dict[str, str]:
    """
    Kubernetes liveness probe.

    Returns 200 if the service is alive.
    """
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_check(response: Response) -> dict[str, Any]:
    """
    Kubernetes readiness probe.

    Returns 200 if the service is ready to accept traffic.
    Checks database connectivity.
    """
    service = get_health_service()
    is_ready = await service.quick_check()

    if not is_ready:
        response.status_code = 503

    return {
        "status": "ready" if is_ready else "not_ready",
        "checks": {"database": is_ready},
    }


@router.get("/health/detailed")
async def detailed_health_check(response: Response) -> dict[str, Any]:
    """
    Detailed health check of all components.

    Returns comprehensive status of:
    - Database
    - Redis
    - LLM providers (Anthropic, OpenAI)
    - Celery workers
    - System resources (disk, memory)
    """
    service = get_health_service()
    health = await service.check_all()

    if health.status == HealthStatus.UNHEALTHY:
        response.status_code = 503
    elif health.status == HealthStatus.DEGRADED:
        response.status_code = 200  # Still operational

    return health.to_dict()


@router.get("/health/version")
async def version_info() -> dict[str, Any]:
    """
    Get version and build information.
    """
    service = get_health_service()

    return {
        "version": service.VERSION,
        "uptime_seconds": round(service.uptime_seconds, 2),
        "python_version": "3.11+",
        "framework": "FastAPI",
    }
