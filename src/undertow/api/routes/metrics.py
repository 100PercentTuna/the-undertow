"""
Metrics API routes.
"""

from typing import Any

from fastapi import APIRouter, Depends

from undertow.api.middleware.auth import require_auth
from undertow.api.middleware.metrics import metrics_collector

router = APIRouter(prefix="/metrics", tags=["Monitoring"])


@router.get("", response_model=dict)
async def get_metrics() -> dict[str, Any]:
    """
    Get application metrics.

    Returns request counts, latencies, and error rates per endpoint.
    """
    return metrics_collector.get_summary()


@router.post("/reset", dependencies=[Depends(require_auth())])
async def reset_metrics() -> dict[str, str]:
    """
    Reset all metrics.

    Requires authentication.
    """
    metrics_collector.reset()
    return {"status": "reset"}


@router.get("/health")
async def metrics_health() -> dict[str, Any]:
    """
    Quick health summary from metrics.
    """
    summary = metrics_collector.get_summary()

    return {
        "status": "healthy" if summary["error_rate"] < 0.1 else "degraded",
        "uptime_seconds": summary["uptime_seconds"],
        "total_requests": summary["total_requests"],
        "error_rate": round(summary["error_rate"], 4),
    }

