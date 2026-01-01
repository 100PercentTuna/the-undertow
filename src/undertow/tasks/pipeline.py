"""
Pipeline tasks for async execution.

These can be run via CLI or Celery.
"""

import asyncio
from datetime import datetime
from typing import Any

import structlog

from undertow.config import settings
from undertow.infrastructure.database import init_db, get_session
from undertow.repositories import StoryRepository, ArticleRepository, PipelineRepository

logger = structlog.get_logger()


def run_daily_pipeline() -> dict[str, Any]:
    """
    Run the complete daily pipeline.

    Synchronous wrapper for async implementation.
    """
    return asyncio.run(_run_daily_pipeline_async())


async def _run_daily_pipeline_async() -> dict[str, Any]:
    """Async implementation of daily pipeline."""
    logger.info("Starting daily pipeline")

    await init_db()

    async for session in get_session():
        pipeline_repo = PipelineRepository(session)
        story_repo = StoryRepository(session)

        # Create pipeline run
        run = await pipeline_repo.create_run()
        await pipeline_repo.start_run(run.id)

        try:
            # Get pending stories
            stories = await story_repo.list_pending_for_analysis(limit=10)
            logger.info(f"Found {len(stories)} stories to process")

            stories_processed = 0
            articles_generated = 0
            total_cost = 0.0
            quality_scores: list[float] = []

            for story in stories:
                try:
                    result = await _process_story(story, session)

                    if result.get("success"):
                        stories_processed += 1
                        total_cost += result.get("cost", 0)

                        if result.get("article_generated"):
                            articles_generated += 1
                            if result.get("quality_score"):
                                quality_scores.append(result["quality_score"])

                except Exception as e:
                    logger.error(
                        "Failed to process story",
                        story_id=story.id,
                        error=str(e),
                    )

            # Complete the run
            avg_quality = (
                sum(quality_scores) / len(quality_scores)
                if quality_scores
                else None
            )

            await pipeline_repo.complete_run(
                run_id=run.id,
                stories_processed=stories_processed,
                articles_generated=articles_generated,
                total_cost=total_cost,
                avg_quality=avg_quality,
            )

            await session.commit()

            result = {
                "run_id": run.id,
                "status": "completed",
                "stories_processed": stories_processed,
                "articles_generated": articles_generated,
                "total_cost": total_cost,
                "avg_quality_score": avg_quality,
            }

            logger.info("Daily pipeline completed", **result)
            return result

        except Exception as e:
            logger.error("Pipeline failed", error=str(e))
            await pipeline_repo.fail_run(run.id, str(e))
            await session.commit()

            return {
                "run_id": run.id,
                "status": "failed",
                "error": str(e),
            }


async def _process_story(story, session) -> dict[str, Any]:
    """Process a single story through the analysis pipeline."""
    from undertow.llm.router import ModelRouter
    from undertow.llm.providers.anthropic import AnthropicProvider
    from undertow.llm.providers.openai import OpenAIProvider
    from undertow.core.pipeline.orchestrator import PipelineOrchestrator
    from undertow.schemas.agents.motivation import StoryContext, AnalysisContext

    # Create router
    providers = {}
    if settings.anthropic_api_key:
        providers["anthropic"] = AnthropicProvider(settings.anthropic_api_key)
    if settings.openai_api_key:
        providers["openai"] = OpenAIProvider(settings.openai_api_key)

    if not providers:
        return {"success": False, "error": "No API keys configured"}

    router = ModelRouter(providers=providers, preference="anthropic")
    orchestrator = PipelineOrchestrator(router)

    # Build input
    story_context = StoryContext(
        headline=story.headline,
        summary=story.summary or "",
        key_events=[],  # Would come from collection
        primary_actors=[],  # Would come from collection
        zones_affected=[story.primary_zone.value] if story.primary_zone else [],
    )

    analysis_context = AnalysisContext()

    # Run pipeline
    result = await orchestrator.run(
        story_context=story_context,
        analysis_context=analysis_context,
    )

    # Update story
    story_repo = StoryRepository(session)

    if result.success:
        await story_repo.update_analysis(
            story_id=story.id,
            analysis_data={
                "motivation": result.motivation.model_dump() if result.motivation else None,
                "chains": result.chains.model_dump() if result.chains else None,
            },
        )

    return {
        "success": result.success,
        "cost": result.total_cost,
        "article_generated": False,  # TODO: implement article generation
        "quality_score": result.final_quality_score,
    }


def analyze_story(story_id: str) -> dict[str, Any]:
    """
    Analyze a specific story by ID.

    Synchronous wrapper for async implementation.
    """
    return asyncio.run(_analyze_story_async(story_id))


async def _analyze_story_async(story_id: str) -> dict[str, Any]:
    """Async implementation of story analysis."""
    await init_db()

    async for session in get_session():
        story_repo = StoryRepository(session)
        story = await story_repo.get(story_id)

        if not story:
            return {"success": False, "error": "Story not found"}

        result = await _process_story(story, session)
        await session.commit()

        return result
