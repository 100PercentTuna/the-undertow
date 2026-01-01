"""
Celery tasks for The Undertow.

Provides background task processing for pipelines, ingestion,
verification, escalations, and notifications.
"""

from undertow.tasks.celery_app import celery_app
from undertow.tasks.celery_tasks import (
    run_daily_pipeline,
    analyze_story,
    ingest_all_feeds,
    send_daily_newsletter,
    cleanup_old_data,
    system_health_check,
)
from undertow.tasks.verification_tasks import (
    verify_article_claims,
    batch_verify_claims,
    index_document,
    bulk_index_documents,
)
from undertow.tasks.escalation_tasks import (
    notify_escalation,
    process_escalation_queue,
    escalation_stats_report,
)

__all__ = [
    # Celery app
    "celery_app",
    # Pipeline tasks
    "run_daily_pipeline",
    "analyze_story",
    "ingest_all_feeds",
    "send_daily_newsletter",
    "cleanup_old_data",
    "system_health_check",
    # Verification tasks
    "verify_article_claims",
    "batch_verify_claims",
    "index_document",
    "bulk_index_documents",
    # Escalation tasks
    "notify_escalation",
    "process_escalation_queue",
    "escalation_stats_report",
]
