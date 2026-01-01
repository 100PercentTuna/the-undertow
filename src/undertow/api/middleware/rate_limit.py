"""
Rate limiting middleware.

Simple in-memory rate limiting. For production, use Redis-based rate limiting.
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Dict

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from undertow.config import settings


@dataclass
class RateLimitEntry:
    """Track rate limit for a single client."""

    requests: int = 0
    window_start: float = field(default_factory=time.time)


class RateLimiter:
    """
    In-memory rate limiter.

    For production, replace with Redis-based implementation.
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
    ) -> None:
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Max requests per minute per client
            requests_per_hour: Max requests per hour per client
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour

        self._minute_buckets: Dict[str, RateLimitEntry] = defaultdict(RateLimitEntry)
        self._hour_buckets: Dict[str, RateLimitEntry] = defaultdict(RateLimitEntry)

    def is_allowed(self, client_id: str) -> tuple[bool, dict]:
        """
        Check if request is allowed.

        Args:
            client_id: Client identifier (IP or API key)

        Returns:
            Tuple of (is_allowed, headers_to_add)
        """
        now = time.time()

        # Check minute limit
        minute_entry = self._minute_buckets[client_id]
        if now - minute_entry.window_start > 60:
            minute_entry.requests = 0
            minute_entry.window_start = now

        # Check hour limit
        hour_entry = self._hour_buckets[client_id]
        if now - hour_entry.window_start > 3600:
            hour_entry.requests = 0
            hour_entry.window_start = now

        # Calculate remaining
        minute_remaining = max(0, self.requests_per_minute - minute_entry.requests)
        hour_remaining = max(0, self.requests_per_hour - hour_entry.requests)

        headers = {
            "X-RateLimit-Limit-Minute": str(self.requests_per_minute),
            "X-RateLimit-Remaining-Minute": str(minute_remaining),
            "X-RateLimit-Limit-Hour": str(self.requests_per_hour),
            "X-RateLimit-Remaining-Hour": str(hour_remaining),
        }

        if minute_entry.requests >= self.requests_per_minute:
            reset_after = 60 - (now - minute_entry.window_start)
            headers["X-RateLimit-Reset-After"] = str(int(reset_after))
            return False, headers

        if hour_entry.requests >= self.requests_per_hour:
            reset_after = 3600 - (now - hour_entry.window_start)
            headers["X-RateLimit-Reset-After"] = str(int(reset_after))
            return False, headers

        # Increment counters
        minute_entry.requests += 1
        hour_entry.requests += 1

        return True, headers

    def reset(self, client_id: str | None = None) -> None:
        """
        Reset rate limits.

        Args:
            client_id: Specific client to reset, or None for all
        """
        if client_id:
            self._minute_buckets.pop(client_id, None)
            self._hour_buckets.pop(client_id, None)
        else:
            self._minute_buckets.clear()
            self._hour_buckets.clear()


# Global rate limiter instance
rate_limiter = RateLimiter(
    requests_per_minute=60,
    requests_per_hour=1000,
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware.

    Limits requests per client (by IP or API key).
    """

    # Paths to skip rate limiting
    SKIP_PATHS = {"/api/v1/health", "/api/v1/metrics", "/docs", "/redoc", "/openapi.json"}

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """Apply rate limiting."""
        # Skip for certain paths
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        # Get client identifier
        client_id = self._get_client_id(request)

        # Check rate limit
        allowed, headers = rate_limiter.is_allowed(client_id)

        if not allowed:
            response = Response(
                content='{"detail": "Rate limit exceeded"}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json",
            )
            for key, value in headers.items():
                response.headers[key] = value
            return response

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        for key, value in headers.items():
            response.headers[key] = value

        return response

    def _get_client_id(self, request: Request) -> str:
        """
        Get client identifier from request.

        Prefers API key, falls back to IP.
        """
        # Check for API key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"key:{api_key[:8]}"  # Use prefix for privacy

        # Fall back to IP
        client_ip = request.client.host if request.client else "unknown"

        # Check for forwarded header (behind proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()

        return f"ip:{client_ip}"

