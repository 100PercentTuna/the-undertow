"""
FastAPI application factory and configuration.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from undertow import __version__
from undertow.api.routes import health, stories, articles, pipeline, newsletter, metrics, prometheus, openapi, costs, zones, export, jobs, verification, escalations, settings, docs, dashboard, preview, benchmarks
from undertow.api.middleware.logging import LoggingMiddleware
from undertow.api.middleware.metrics import MetricsMiddleware
from undertow.api.middleware.rate_limit import RateLimitMiddleware
from undertow.config import settings
from undertow.infrastructure.database import init_db, close_db
from undertow.infrastructure.logging import setup_logging

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown tasks:
    - Database connection pool
    - Logging configuration
    - Cache initialization
    """
    # Startup
    setup_logging()
    logger.info(
        "Starting The Undertow",
        version=__version__,
        environment=settings.app_env.value,
    )

    await init_db()
    logger.info("Database initialized")

    yield

    # Shutdown
    logger.info("Shutting down The Undertow")
    await close_db()
    logger.info("Database connections closed")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI instance
    """
    app = FastAPI(
        title="The Undertow API",
        description="AI-powered geopolitical intelligence system",
        version=__version__,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.is_development else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom middleware (order matters - last added is first executed)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(RateLimitMiddleware)

    # Register routes
    app.include_router(health.router, prefix="/api/v1", tags=["health"])
    app.include_router(stories.router, prefix="/api/v1/stories", tags=["stories"])
    app.include_router(articles.router, prefix="/api/v1/articles", tags=["articles"])
    app.include_router(pipeline.router, prefix="/api/v1/pipeline", tags=["pipeline"])
    app.include_router(newsletter.router, prefix="/api/v1", tags=["newsletter"])
    app.include_router(metrics.router, prefix="/api/v1", tags=["monitoring"])
    app.include_router(prometheus.router, prefix="/api/v1", tags=["monitoring"])
    app.include_router(openapi.router, prefix="/api/v1", tags=["documentation"])
    app.include_router(costs.router, prefix="/api/v1", tags=["costs"])
    app.include_router(zones.router, prefix="/api/v1", tags=["zones"])
    app.include_router(export.router, prefix="/api/v1", tags=["export"])
    app.include_router(jobs.router, prefix="/api/v1", tags=["jobs"])
    app.include_router(verification.router, prefix="/api/v1", tags=["verification"])
    app.include_router(escalations.router, prefix="/api/v1", tags=["escalations"])
    app.include_router(settings.router, prefix="/api/v1", tags=["settings"])
    app.include_router(docs.router, prefix="/api/v1", tags=["documentation"])
    app.include_router(dashboard.router, prefix="/api/v1", tags=["dashboard"])
    app.include_router(preview.router, prefix="/api/v1", tags=["preview"])
    app.include_router(benchmarks.router, prefix="/api/v1", tags=["benchmarks"])

    return app


# Create app instance for uvicorn
app = create_app()

