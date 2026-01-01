"""
Celery application configuration.

Usage:
    celery -A undertow.tasks.celery_app worker -l info
    celery -A undertow.tasks.celery_app beat -l info
"""

from celery import Celery
from celery.schedules import crontab

from undertow.config import settings

# Create Celery app
app = Celery(
    "undertow",
    broker=settings.celery_broker_url or "redis://localhost:6379/0",
    backend=settings.celery_result_backend or "redis://localhost:6379/0",
)

# Configure Celery
app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Result expiration
    result_expires=3600 * 24,  # 24 hours

    # Task execution
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3000,  # 50 min soft limit

    # Worker settings
    worker_prefetch_multiplier=1,
    worker_concurrency=2,  # LLM calls are I/O bound

    # Beat schedule (periodic tasks)
    beat_schedule={
        # Run daily pipeline at 5 AM UTC
        "daily-pipeline": {
            "task": "undertow.tasks.celery_tasks.run_daily_pipeline_task",
            "schedule": crontab(hour=5, minute=0),
        },
        # Ingest sources every 4 hours
        "source-ingestion": {
            "task": "undertow.tasks.celery_tasks.ingest_sources_task",
            "schedule": crontab(hour="*/4", minute=30),
        },
        # Cleanup old data weekly
        "weekly-cleanup": {
            "task": "undertow.tasks.celery_tasks.cleanup_old_data_task",
            "schedule": crontab(day_of_week=0, hour=3, minute=0),
        },
    },
)

# Auto-discover tasks
app.autodiscover_tasks(["undertow.tasks"])

