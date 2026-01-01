"""
Metrics collection middleware.

Collects request metrics for monitoring.
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, Dict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


@dataclass
class EndpointMetrics:
    """Metrics for a single endpoint."""

    request_count: int = 0
    error_count: int = 0
    total_duration_ms: float = 0.0
    min_duration_ms: float = float("inf")
    max_duration_ms: float = 0.0
    status_codes: Dict[int, int] = field(default_factory=lambda: defaultdict(int))

    @property
    def avg_duration_ms(self) -> float:
        """Average request duration."""
        if self.request_count == 0:
            return 0.0
        return self.total_duration_ms / self.request_count


class MetricsCollector:
    """
    Collects and stores request metrics.

    Thread-safe singleton for collecting metrics across requests.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.endpoints: Dict[str, EndpointMetrics] = defaultdict(EndpointMetrics)
        self.start_time = datetime.utcnow()
        self.total_requests = 0
        self.total_errors = 0

    def record(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
    ) -> None:
        """Record a request."""
        key = f"{method} {path}"
        metrics = self.endpoints[key]

        metrics.request_count += 1
        metrics.total_duration_ms += duration_ms
        metrics.min_duration_ms = min(metrics.min_duration_ms, duration_ms)
        metrics.max_duration_ms = max(metrics.max_duration_ms, duration_ms)
        metrics.status_codes[status_code] += 1

        self.total_requests += 1
        if status_code >= 400:
            metrics.error_count += 1
            self.total_errors += 1

    def get_summary(self) -> dict:
        """Get metrics summary."""
        uptime = datetime.utcnow() - self.start_time

        return {
            "uptime_seconds": int(uptime.total_seconds()),
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "error_rate": (
                self.total_errors / self.total_requests
                if self.total_requests > 0
                else 0
            ),
            "endpoints": {
                key: {
                    "requests": m.request_count,
                    "errors": m.error_count,
                    "avg_duration_ms": round(m.avg_duration_ms, 2),
                    "min_duration_ms": round(m.min_duration_ms, 2)
                    if m.min_duration_ms != float("inf")
                    else 0,
                    "max_duration_ms": round(m.max_duration_ms, 2),
                    "status_codes": dict(m.status_codes),
                }
                for key, m in self.endpoints.items()
            },
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self.endpoints.clear()
        self.start_time = datetime.utcnow()
        self.total_requests = 0
        self.total_errors = 0


# Global collector instance
metrics_collector = MetricsCollector()


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware for collecting request metrics.

    Metrics are stored in memory and can be retrieved via /metrics endpoint.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """Process request and collect metrics."""
        start_time = time.perf_counter()

        # Skip metrics collection for metrics endpoint itself
        if request.url.path == "/api/v1/metrics":
            return await call_next(request)

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            status_code = 500
            raise
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Normalize path (remove IDs for grouping)
            path = self._normalize_path(request.url.path)

            metrics_collector.record(
                method=request.method,
                path=path,
                status_code=status_code,
                duration_ms=duration_ms,
            )

        return response

    def _normalize_path(self, path: str) -> str:
        """
        Normalize path by replacing IDs with placeholders.

        /api/v1/stories/abc123 -> /api/v1/stories/{id}
        """
        parts = path.split("/")
        normalized = []

        for i, part in enumerate(parts):
            # Check if this looks like an ID (UUID or similar)
            if (
                len(part) > 10
                and any(c.isdigit() for c in part)
                and any(c.isalpha() for c in part)
            ):
                normalized.append("{id}")
            else:
                normalized.append(part)

        return "/".join(normalized)

