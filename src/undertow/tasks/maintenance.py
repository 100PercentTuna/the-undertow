"""
Maintenance tasks for cleanup and housekeeping.
"""

import asyncio
from datetime import datetime, timedelta, timezone

import structlog
from celery import shared_task
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from undertow.config import settings
from undertow.models.pipeline import AgentExecution, PipelineRun, PipelineStatus

logger = structlog.get_logger()


def get_async_session() -> async_sessionmaker[AsyncSession]:
    """Create async session factory for tasks."""
    engine = create_async_engine(settings.database_url)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@shared_task(name="undertow.tasks.maintenance.cleanup_old_data")
def cleanup_old_data() -> dict:
    """
    Clean up old data to prevent database bloat.
    
    Removes:
    - Agent executions older than 30 days
    - Failed pipeline runs older than 7 days
    """
    logger.info("Starting cleanup task")
    
    try:
        result = asyncio.run(_cleanup_async())
        return result
    except Exception as e:
        logger.error("Cleanup failed", error=str(e))
        raise


async def _cleanup_async() -> dict:
    """Async implementation of cleanup."""
    session_factory = get_async_session()
    
    async with session_factory() as session:
        now = datetime.now(timezone.utc)
        
        # Delete old agent executions (30 days)
        cutoff_executions = now - timedelta(days=30)
        exec_delete = delete(AgentExecution).where(
            AgentExecution.created_at < cutoff_executions
        )
        exec_result = await session.execute(exec_delete)
        executions_deleted = exec_result.rowcount
        
        # Delete old failed pipeline runs (7 days)
        cutoff_runs = now - timedelta(days=7)
        runs_delete = delete(PipelineRun).where(
            PipelineRun.status == PipelineStatus.FAILED,
            PipelineRun.created_at < cutoff_runs,
        )
        runs_result = await session.execute(runs_delete)
        runs_deleted = runs_result.rowcount
        
        await session.commit()
        
        logger.info(
            "Cleanup completed",
            executions_deleted=executions_deleted,
            runs_deleted=runs_deleted,
        )
        
        return {
            "status": "completed",
            "executions_deleted": executions_deleted,
            "runs_deleted": runs_deleted,
        }


@shared_task(name="undertow.tasks.maintenance.vacuum_database")
def vacuum_database() -> dict:
    """
    Run VACUUM on database tables.
    
    Should be run during low-traffic periods.
    """
    logger.info("Starting database vacuum")
    
    # Note: VACUUM cannot run inside a transaction
    # This would need a separate connection approach
    
    return {"status": "skipped", "reason": "Not implemented for async"}

