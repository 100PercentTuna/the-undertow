"""
Analysis tasks for background processing.
"""

import asyncio

import structlog
from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from undertow.config import settings

logger = structlog.get_logger()


def get_async_session() -> async_sessionmaker[AsyncSession]:
    """Create async session factory for tasks."""
    engine = create_async_engine(settings.database_url)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@shared_task(name="undertow.tasks.analysis.run_motivation_analysis")
def run_motivation_analysis(story_id: str) -> dict:
    """
    Run motivation analysis on a story.
    
    Standalone task for individual analysis.
    """
    logger.info("Running motivation analysis", story_id=story_id)
    
    try:
        result = asyncio.run(_run_motivation_async(story_id))
        return result
    except Exception as e:
        logger.error("Motivation analysis failed", story_id=story_id, error=str(e))
        raise


async def _run_motivation_async(story_id: str) -> dict:
    """Async implementation of motivation analysis."""
    session_factory = get_async_session()
    
    async with session_factory() as session:
        from undertow.models.story import Story
        from undertow.agents.analysis.motivation import MotivationAnalysisAgent
        from undertow.llm.router import ModelRouter
        from undertow.llm.providers.anthropic import AnthropicProvider
        from undertow.schemas.agents.motivation import (
            MotivationInput,
            StoryContext,
            AnalysisContext,
        )
        
        story = await session.get(Story, story_id)
        if not story:
            raise ValueError(f"Story {story_id} not found")
        
        # Create router
        providers = {}
        if settings.anthropic_api_key:
            providers["anthropic"] = AnthropicProvider(settings.anthropic_api_key)
        
        if not providers:
            raise ValueError("No LLM providers configured")
        
        router = ModelRouter(providers=providers, preference="anthropic")
        agent = MotivationAnalysisAgent(router)
        
        # Build input
        input_data = MotivationInput(
            story=StoryContext(
                headline=story.headline,
                summary=story.summary,
                key_events=story.key_events or ["Event details pending"],
                primary_actors=story.primary_actors or ["Actors pending"],
                zones_affected=[story.primary_zone.value],
            ),
            context=AnalysisContext(),
        )
        
        # Run agent
        result = await agent.run(input_data)
        
        if result.success and result.output:
            # Store in story
            analysis_data = story.analysis_data or {}
            analysis_data["motivation"] = result.output.model_dump()
            story.analysis_data = analysis_data
            await session.commit()
        
        return {
            "story_id": story_id,
            "success": result.success,
            "quality_score": result.metadata.quality_score,
            "cost": result.metadata.cost_usd,
            "error": result.error,
        }


@shared_task(name="undertow.tasks.analysis.run_chains_analysis")
def run_chains_analysis(story_id: str) -> dict:
    """
    Run chains analysis on a story.
    
    Standalone task for individual analysis.
    """
    logger.info("Running chains analysis", story_id=story_id)
    
    try:
        result = asyncio.run(_run_chains_async(story_id))
        return result
    except Exception as e:
        logger.error("Chains analysis failed", story_id=story_id, error=str(e))
        raise


async def _run_chains_async(story_id: str) -> dict:
    """Async implementation of chains analysis."""
    session_factory = get_async_session()
    
    async with session_factory() as session:
        from undertow.models.story import Story
        from undertow.agents.analysis.chains import ChainMappingAgent
        from undertow.llm.router import ModelRouter
        from undertow.llm.providers.anthropic import AnthropicProvider
        from undertow.schemas.agents.chains import ChainsInput
        from undertow.schemas.agents.motivation import StoryContext, AnalysisContext
        
        story = await session.get(Story, story_id)
        if not story:
            raise ValueError(f"Story {story_id} not found")
        
        # Create router
        providers = {}
        if settings.anthropic_api_key:
            providers["anthropic"] = AnthropicProvider(settings.anthropic_api_key)
        
        if not providers:
            raise ValueError("No LLM providers configured")
        
        router = ModelRouter(providers=providers, preference="anthropic")
        agent = ChainMappingAgent(router)
        
        # Get motivation synthesis if available
        motivation_synthesis = ""
        if story.analysis_data and "motivation" in story.analysis_data:
            synth = story.analysis_data["motivation"].get("synthesis", {})
            motivation_synthesis = synth.get("primary_driver_explanation", "")
        
        # Build input
        input_data = ChainsInput(
            story=StoryContext(
                headline=story.headline,
                summary=story.summary,
                key_events=story.key_events or ["Event details pending"],
                primary_actors=story.primary_actors or ["Actors pending"],
                zones_affected=[story.primary_zone.value],
            ),
            context=AnalysisContext(),
            motivation_synthesis=motivation_synthesis,
        )
        
        # Run agent
        result = await agent.run(input_data)
        
        if result.success and result.output:
            # Store in story
            analysis_data = story.analysis_data or {}
            analysis_data["chains"] = result.output.model_dump()
            story.analysis_data = analysis_data
            await session.commit()
        
        return {
            "story_id": story_id,
            "success": result.success,
            "quality_score": result.metadata.quality_score,
            "cost": result.metadata.cost_usd,
            "error": result.error,
        }

