"""
Celery task definitions.

These wrap the pipeline functions for async execution.
"""

import structlog

from undertow.tasks.celery_app import app
from undertow.tasks.pipeline import run_daily_pipeline, analyze_story
from undertow.tasks.ingestion import ingest_all_sources

logger = structlog.get_logger()


@app.task(
    name="undertow.tasks.celery_tasks.run_daily_pipeline_task",
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 min
)
def run_daily_pipeline_task(self):
    """
    Run the daily pipeline.

    Retries up to 3 times on failure.
    """
    try:
        logger.info("Starting daily pipeline task")
        result = run_daily_pipeline()

        if result.get("status") == "failed":
            raise Exception(result.get("error", "Unknown error"))

        logger.info("Daily pipeline task completed", **result)
        return result

    except Exception as exc:
        logger.error("Daily pipeline task failed", error=str(exc))
        raise self.retry(exc=exc)


@app.task(
    name="undertow.tasks.celery_tasks.analyze_story_task",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def analyze_story_task(self, story_id: str):
    """
    Analyze a specific story.

    Args:
        story_id: Story ID to analyze
    """
    try:
        logger.info("Starting story analysis task", story_id=story_id)
        result = analyze_story(story_id)

        if not result.get("success"):
            raise Exception(result.get("error", "Analysis failed"))

        logger.info("Story analysis task completed", story_id=story_id)
        return result

    except Exception as exc:
        logger.error(
            "Story analysis task failed",
            story_id=story_id,
            error=str(exc),
        )
        raise self.retry(exc=exc)


@app.task(
    name="undertow.tasks.celery_tasks.ingest_sources_task",
    bind=True,
    max_retries=2,
    default_retry_delay=120,
)
def ingest_sources_task(self):
    """
    Ingest from all configured sources.
    """
    try:
        logger.info("Starting source ingestion task")
        result = ingest_all_sources()

        logger.info("Source ingestion task completed", **result)
        return result

    except Exception as exc:
        logger.error("Source ingestion task failed", error=str(exc))
        raise self.retry(exc=exc)


@app.task(name="undertow.tasks.celery_tasks.send_newsletter_task")
def send_newsletter_task(subscriber_emails: list[str]):
    """
    Compile and send newsletter to subscribers.

    Args:
        subscriber_emails: List of subscriber email addresses
    """
    import asyncio
    from undertow.services.newsletter import NewsletterService
    from undertow.infrastructure.database import init_db, get_session
    from undertow.repositories import ArticleRepository

    async def _send():
        await init_db()

        async for session in get_session():
            article_repo = ArticleRepository(session)
            articles = await article_repo.list_for_newsletter()

            if not articles:
                logger.warning("No articles for newsletter")
                return {"status": "skipped", "reason": "no_articles"}

            # Convert to dicts
            article_dicts = [
                {
                    "headline": a.headline,
                    "subhead": a.subhead or "",
                    "summary": a.summary or "",
                    "content": a.content or "",
                    "read_time_minutes": a.read_time_minutes or 5,
                    "zones": a.zones or [],
                }
                for a in articles
            ]

            service = NewsletterService()
            newsletter = await service.compile_edition(article_dicts)
            result = await service.send_to_subscribers(newsletter, subscriber_emails)

            return result

    return asyncio.run(_send())


@app.task(name="undertow.tasks.celery_tasks.cleanup_old_data_task")
def cleanup_old_data_task():
    """
    Clean up old pipeline runs and processed stories.
    """
    import asyncio
    from datetime import datetime, timedelta
    from undertow.infrastructure.database import init_db, get_session
    from undertow.repositories import PipelineRepository

    async def _cleanup():
        await init_db()

        async for session in get_session():
            pipeline_repo = PipelineRepository(session)

            # Get old completed runs (> 30 days)
            cutoff = datetime.utcnow() - timedelta(days=30)
            old_runs = await pipeline_repo.list_recent(days=60)

            deleted = 0
            for run in old_runs:
                if run.created_at < cutoff and run.status.value in [
                    "completed",
                    "failed",
                ]:
                    await pipeline_repo.delete(run.id)
                    deleted += 1

            await session.commit()

            logger.info("Cleanup completed", deleted_runs=deleted)
            return {"deleted_runs": deleted}

    return asyncio.run(_cleanup())


@app.task(name="undertow.tasks.celery_tasks.health_check_task")
def health_check_task():
    """
    Health check task for monitoring.
    """
    import asyncio
    from undertow.infrastructure.database import init_db, get_session
    from undertow.infrastructure.cache import get_cache

    async def _check():
        checks = {}

        # Database check
        try:
            await init_db()
            async for session in get_session():
                from sqlalchemy import text
                await session.execute(text("SELECT 1"))
                checks["database"] = "ok"
        except Exception as e:
            checks["database"] = f"error: {str(e)}"

        # Cache check
        try:
            cache = get_cache()
            await cache.set("health_check", "ok", ttl=10)
            value = await cache.get("health_check")
            checks["cache"] = "ok" if value == "ok" else "error"
        except Exception as e:
            checks["cache"] = f"error: {str(e)}"

        return checks

    return asyncio.run(_check())

