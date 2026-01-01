"""
Pipeline repository for database operations.
"""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from undertow.models.pipeline import PipelineRun, PipelineStatus, AgentExecution
from undertow.repositories.base import BaseRepository


class PipelineRepository(BaseRepository[PipelineRun]):
    """
    Repository for Pipeline operations.

    Provides specialized queries for pipeline management.
    """

    model = PipelineRun

    async def get_latest(self) -> PipelineRun | None:
        """
        Get the most recent pipeline run.

        Returns:
            Latest pipeline run or None
        """
        query = (
            select(PipelineRun)
            .order_by(PipelineRun.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_running(self) -> PipelineRun | None:
        """
        Get currently running pipeline.

        Returns:
            Running pipeline or None
        """
        query = select(PipelineRun).where(
            PipelineRun.status == PipelineStatus.RUNNING
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_recent(
        self,
        days: int = 7,
        limit: int = 50,
    ) -> list[PipelineRun]:
        """
        List recent pipeline runs.

        Args:
            days: Days to look back
            limit: Maximum results

        Returns:
            Recent pipeline runs
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        query = (
            select(PipelineRun)
            .where(PipelineRun.created_at >= cutoff)
            .order_by(PipelineRun.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_by_status(
        self,
        status: PipelineStatus,
        limit: int = 50,
    ) -> list[PipelineRun]:
        """
        List pipeline runs by status.

        Args:
            status: Pipeline status
            limit: Maximum results

        Returns:
            Pipeline runs with status
        """
        query = (
            select(PipelineRun)
            .where(PipelineRun.status == status)
            .order_by(PipelineRun.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_executions(
        self,
        run_id: str,
    ) -> list[AgentExecution]:
        """
        Get agent executions for a pipeline run.

        Args:
            run_id: Pipeline run ID

        Returns:
            Agent executions
        """
        query = (
            select(AgentExecution)
            .where(AgentExecution.pipeline_run_id == run_id)
            .order_by(AgentExecution.started_at)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_stats(self, days: int = 30) -> dict[str, Any]:
        """
        Get pipeline statistics.

        Args:
            days: Days to analyze

        Returns:
            Statistics dict
        """
        cutoff = datetime.utcnow() - timedelta(days=days)

        # Count by status
        status_query = (
            select(PipelineRun.status, func.count())
            .where(PipelineRun.created_at >= cutoff)
            .group_by(PipelineRun.status)
        )
        status_result = await self.session.execute(status_query)
        status_counts = {row[0].value: row[1] for row in status_result}

        # Totals from completed runs
        totals_query = (
            select(
                func.sum(PipelineRun.stories_processed),
                func.sum(PipelineRun.articles_generated),
                func.sum(PipelineRun.total_cost_usd),
                func.avg(PipelineRun.avg_quality_score),
            )
            .where(
                and_(
                    PipelineRun.created_at >= cutoff,
                    PipelineRun.status == PipelineStatus.COMPLETED,
                )
            )
        )
        totals_result = await self.session.execute(totals_query)
        totals = totals_result.one()

        # Success rate
        total_runs = sum(status_counts.values())
        completed = status_counts.get("completed", 0)
        success_rate = completed / total_runs if total_runs > 0 else 0

        return {
            "period_days": days,
            "by_status": status_counts,
            "total_runs": total_runs,
            "success_rate": round(success_rate, 3),
            "stories_processed": int(totals[0] or 0),
            "articles_generated": int(totals[1] or 0),
            "total_cost_usd": round(float(totals[2] or 0), 2),
            "avg_quality_score": round(float(totals[3] or 0), 3),
        }

    async def create_run(self) -> PipelineRun:
        """
        Create a new pipeline run.

        Returns:
            Created pipeline run
        """
        run = PipelineRun(status=PipelineStatus.PENDING)
        return await self.create(run)

    async def start_run(self, run_id: str) -> PipelineRun | None:
        """
        Mark a pipeline run as started.

        Args:
            run_id: Pipeline run ID

        Returns:
            Updated run or None
        """
        run = await self.get(run_id)
        if run:
            run.status = PipelineStatus.RUNNING
            run.started_at = datetime.utcnow()
            await self.session.flush()
            return run
        return None

    async def complete_run(
        self,
        run_id: str,
        stories_processed: int,
        articles_generated: int,
        total_cost: float,
        avg_quality: float | None = None,
    ) -> PipelineRun | None:
        """
        Mark a pipeline run as completed.

        Args:
            run_id: Pipeline run ID
            stories_processed: Number of stories processed
            articles_generated: Number of articles generated
            total_cost: Total cost in USD
            avg_quality: Average quality score

        Returns:
            Updated run or None
        """
        run = await self.get(run_id)
        if run:
            run.status = PipelineStatus.COMPLETED
            run.completed_at = datetime.utcnow()
            run.stories_processed = stories_processed
            run.articles_generated = articles_generated
            run.total_cost_usd = total_cost
            run.avg_quality_score = avg_quality
            await self.session.flush()
            return run
        return None

    async def fail_run(
        self,
        run_id: str,
        error_message: str,
    ) -> PipelineRun | None:
        """
        Mark a pipeline run as failed.

        Args:
            run_id: Pipeline run ID
            error_message: Error description

        Returns:
            Updated run or None
        """
        run = await self.get(run_id)
        if run:
            run.status = PipelineStatus.FAILED
            run.completed_at = datetime.utcnow()
            run.error_message = error_message
            await self.session.flush()
            return run
        return None

    async def record_execution(
        self,
        run_id: str,
        story_id: str | None,
        agent_name: str,
        agent_version: str,
        model_used: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        duration_ms: int,
        success: bool,
        quality_score: float | None = None,
        error_message: str | None = None,
    ) -> AgentExecution:
        """
        Record an agent execution.

        Args:
            run_id: Pipeline run ID
            story_id: Story ID if applicable
            agent_name: Name of agent
            agent_version: Agent version
            model_used: LLM model used
            input_tokens: Input tokens consumed
            output_tokens: Output tokens generated
            cost_usd: Cost in USD
            duration_ms: Duration in milliseconds
            success: Whether execution succeeded
            quality_score: Quality score if available
            error_message: Error message if failed

        Returns:
            Created execution record
        """
        now = datetime.utcnow()
        execution = AgentExecution(
            pipeline_run_id=run_id,
            story_id=story_id,
            agent_name=agent_name,
            agent_version=agent_version,
            started_at=now - timedelta(milliseconds=duration_ms),
            completed_at=now,
            duration_ms=duration_ms,
            model_used=model_used,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            success=success,
            quality_score=quality_score,
            error_message=error_message,
        )
        self.session.add(execution)
        await self.session.flush()
        return execution

