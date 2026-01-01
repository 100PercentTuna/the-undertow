"""
Request logging middleware.
"""

import time
from typing import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger()


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging all HTTP requests.

    Logs:
    - Request method, path, client IP
    - Response status code
    - Request duration
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """Process request and log details."""
        start_time = time.perf_counter()

        # Extract request info
        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"

        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
            error = None
        except Exception as e:
            status_code = 500
            error = str(e)
            raise
        finally:
            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Log the request
            log_data = {
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": round(duration_ms, 2),
                "client_ip": client_ip,
            }

            if error:
                log_data["error"] = error
                logger.error("HTTP request failed", **log_data)
            elif status_code >= 400:
                logger.warning("HTTP request error", **log_data)
            else:
                logger.info("HTTP request", **log_data)

        return response

