"""
Pipeline management endpoints.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from undertow.infrastructure.database import get_session
from undertow.models.pipeline import PipelineRun, PipelineStatus, AgentExecution
from undertow.schemas.base import PaginatedResponse, PaginationParams

router = APIRouter()


@router.get("/runs")
async def list_pipeline_runs(
    page: Annotated[int, Query(ge=1, le=10000)] = 1,
    per_page: Annotated[int, Query(ge=1, le=200)] = 50,
    status_filter: PipelineStatus | None = None,
    session: AsyncSession = Depends(get_session),
) -> PaginatedResponse:
    """
    List pipeline runs with pagination.

    Args:
        page: Page number
        per_page: Items per page
        status_filter: Filter by status

    Returns:
        Paginated list of pipeline runs
    """
    pagination = PaginationParams(page=page, per_page=per_page)

    query = select(PipelineRun).order_by(PipelineRun.created_at.desc())

    if status_filter:
        query = query.where(PipelineRun.status == status_filter)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_query)).scalar() or 0

    query = query.offset(pagination.offset).limit(pagination.per_page)
    result = await session.execute(query)
    runs = result.scalars().all()

    return PaginatedResponse.create(
        items=[_run_to_dict(r) for r in runs],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/runs/{run_id}")
async def get_pipeline_run(
    run_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Get pipeline run details including agent executions.

    Args:
        run_id: Pipeline run UUID

    Returns:
        Full run details with metrics
    """
    run = await session.get(PipelineRun, run_id)

    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline run {run_id} not found",
        )

    # Get agent executions
    exec_query = (
        select(AgentExecution)
        .where(AgentExecution.pipeline_run_id == run_id)
        .order_by(AgentExecution.started_at)
    )
    result = await session.execute(exec_query)
    executions = result.scalars().all()

    data = _run_to_dict(run)
    data["agent_executions"] = [_execution_to_dict(e) for e in executions]

    return data


@router.post("/trigger")
async def trigger_pipeline(
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Manually trigger a pipeline run.

    Returns:
        Created pipeline run info
    """
    # Check if there's already a running pipeline
    running_query = select(PipelineRun).where(
        PipelineRun.status == PipelineStatus.RUNNING
    )
    result = await session.execute(running_query)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A pipeline is already running",
        )

    # Create new pipeline run
    run = PipelineRun(status=PipelineStatus.PENDING)
    session.add(run)
    await session.commit()
    await session.refresh(run)

    # TODO: Queue pipeline task with Celery
    # run_daily_pipeline.delay(run.id)

    return {
        "message": "Pipeline triggered",
        "run_id": run.id,
        "status": run.status.value,
    }


@router.get("/stats")
async def get_pipeline_stats(
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Get pipeline statistics.

    Returns:
        Aggregated statistics across all runs
    """
    # Count by status
    status_query = select(
        PipelineRun.status,
        func.count().label("count"),
    ).group_by(PipelineRun.status)

    result = await session.execute(status_query)
    status_counts = {row.status.value: row.count for row in result}

    # Totals from completed runs
    totals_query = select(
        func.sum(PipelineRun.stories_processed).label("total_stories"),
        func.sum(PipelineRun.articles_generated).label("total_articles"),
        func.sum(PipelineRun.total_cost_usd).label("total_cost"),
        func.avg(PipelineRun.avg_quality_score).label("avg_quality"),
    ).where(PipelineRun.status == PipelineStatus.COMPLETED)

    result = await session.execute(totals_query)
    totals = result.one()

    return {
        "runs_by_status": status_counts,
        "totals": {
            "stories_processed": int(totals.total_stories or 0),
            "articles_generated": int(totals.total_articles or 0),
            "total_cost_usd": float(totals.total_cost or 0),
            "avg_quality_score": float(totals.avg_quality or 0),
        },
    }


def _run_to_dict(run: PipelineRun) -> dict:
    """Convert PipelineRun to dict."""
    return {
        "id": run.id,
        "status": run.status.value,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "stories_processed": run.stories_processed,
        "articles_generated": run.articles_generated,
        "total_cost_usd": run.total_cost_usd,
        "total_tokens": run.total_tokens,
        "avg_quality_score": run.avg_quality_score,
        "error_message": run.error_message,
        "metrics": run.metrics,
        "created_at": run.created_at.isoformat(),
    }


def _execution_to_dict(execution: AgentExecution) -> dict:
    """Convert AgentExecution to dict."""
    return {
        "id": execution.id,
        "agent_name": execution.agent_name,
        "agent_version": execution.agent_version,
        "started_at": execution.started_at.isoformat(),
        "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
        "duration_ms": execution.duration_ms,
        "model_used": execution.model_used,
        "input_tokens": execution.input_tokens,
        "output_tokens": execution.output_tokens,
        "cost_usd": execution.cost_usd,
        "success": execution.success,
        "error_message": execution.error_message,
        "quality_score": execution.quality_score,
        "story_id": execution.story_id,
    }

