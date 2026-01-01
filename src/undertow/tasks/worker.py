"""
Celery worker configuration and task definitions.
"""

from celery import Celery
from celery.schedules import crontab

from undertow.config import settings

# Create Celery app
app = Celery(
    "undertow",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Celery configuration
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3300,  # Soft limit at 55 minutes
    worker_prefetch_multiplier=1,  # Don't prefetch tasks
    task_acks_late=True,  # Acknowledge after completion
    task_reject_on_worker_lost=True,
    result_expires=86400,  # Results expire after 1 day
)

# Beat schedule (periodic tasks)
app.conf.beat_schedule = {
    "run-daily-pipeline": {
        "task": "undertow.tasks.pipeline.run_daily_pipeline",
        "schedule": crontab(hour=settings.pipeline_start_hour, minute=0),
        "options": {"queue": "pipeline"},
    },
    "ingest-sources": {
        "task": "undertow.tasks.ingestion.ingest_all_sources",
        "schedule": crontab(minute="*/30"),  # Every 30 minutes
        "options": {"queue": "ingestion"},
    },
    "cleanup-old-data": {
        "task": "undertow.tasks.maintenance.cleanup_old_data",
        "schedule": crontab(hour=2, minute=0),  # 2 AM daily
        "options": {"queue": "maintenance"},
    },
}

# Task routing
app.conf.task_routes = {
    "undertow.tasks.pipeline.*": {"queue": "pipeline"},
    "undertow.tasks.ingestion.*": {"queue": "ingestion"},
    "undertow.tasks.maintenance.*": {"queue": "maintenance"},
    "undertow.tasks.analysis.*": {"queue": "analysis"},
}

# Import tasks to register them
app.autodiscover_tasks([
    "undertow.tasks.pipeline",
    "undertow.tasks.ingestion",
    "undertow.tasks.analysis",
    "undertow.tasks.maintenance",
])

