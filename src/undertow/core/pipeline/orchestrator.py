"""
Pipeline orchestrator for daily analysis runs.

Coordinates the 4-pass pipeline:
1. Foundation: Fact reconstruction, context, actor profiling
2. Analysis: Motivation, chains, subtleties
3. Adversarial: Debate, verification, critique
4. Production: Writing, editing, assembly
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from undertow.agents.analysis.motivation import MotivationAnalysisAgent
from undertow.agents.analysis.chains import ChainMappingAgent
from undertow.agents.result import AgentResult
from undertow.exceptions import (
    PipelineError,
    QualityGateFailure,
    HumanEscalationRequired,
)
from undertow.llm.router import ModelRouter
from undertow.models.pipeline import AgentExecution, PipelineRun, PipelineStatus
from undertow.models.story import Story, StoryStatus
from undertow.schemas.agents.motivation import (
    MotivationInput,
    MotivationOutput,
    StoryContext,
    AnalysisContext,
)
from undertow.schemas.agents.chains import ChainsInput, ChainsOutput

logger = structlog.get_logger()


@dataclass
class PipelineContext:
    """Context passed through pipeline stages."""

    pipeline_run_id: str
    story: Story
    session: AsyncSession
    router: ModelRouter

    # Accumulated analysis results
    foundation_data: dict[str, Any] = field(default_factory=dict)
    motivation_result: AgentResult[MotivationOutput] | None = None
    chains_result: AgentResult[ChainsOutput] | None = None
    adversarial_data: dict[str, Any] = field(default_factory=dict)
    production_data: dict[str, Any] = field(default_factory=dict)

    # Metrics
    total_cost: float = 0.0
    total_tokens: int = 0


@dataclass
class PipelineResult:
    """Result of pipeline execution for a story."""

    success: bool
    story_id: str
    error: str | None = None
    quality_scores: dict[str, float] = field(default_factory=dict)
    total_cost: float = 0.0
    total_tokens: int = 0


class PipelineOrchestrator:
    """
    Orchestrates the 4-pass analysis pipeline.

    Usage:
        orchestrator = PipelineOrchestrator(session, router)
        result = await orchestrator.analyze_story(story)
    """

    def __init__(
        self,
        session: AsyncSession,
        router: ModelRouter,
    ) -> None:
        """
        Initialize orchestrator.

        Args:
            session: Database session
            router: LLM router
        """
        self.session = session
        self.router = router

        # Initialize agents
        self.motivation_agent = MotivationAnalysisAgent(router, temperature=0.7)
        self.chains_agent = ChainMappingAgent(router, temperature=0.7)

    async def analyze_story(
        self,
        story: Story,
        pipeline_run_id: str | None = None,
    ) -> PipelineResult:
        """
        Run full analysis pipeline on a story.

        Args:
            story: Story to analyze
            pipeline_run_id: Optional parent pipeline run ID

        Returns:
            PipelineResult with analysis outcome
        """
        run_id = pipeline_run_id or str(uuid4())

        context = PipelineContext(
            pipeline_run_id=run_id,
            story=story,
            session=self.session,
            router=self.router,
        )

        logger.info(
            "Starting story analysis",
            story_id=story.id,
            headline=story.headline[:50],
            pipeline_run=run_id,
        )

        try:
            # Update story status
            story.status = StoryStatus.ANALYZING
            await self.session.commit()

            # Pass 1: Foundation
            await self._pass_foundation(context)

            # Pass 2: Core Analysis
            await self._pass_analysis(context)

            # Pass 3: Adversarial (simplified for now)
            await self._pass_adversarial(context)

            # Pass 4: Production (simplified for now)
            await self._pass_production(context)

            # Update story with analysis results
            story.status = StoryStatus.ANALYZED
            story.analysis_data = self._compile_analysis_data(context)
            await self.session.commit()

            logger.info(
                "Story analysis completed",
                story_id=story.id,
                total_cost=context.total_cost,
            )

            return PipelineResult(
                success=True,
                story_id=story.id,
                quality_scores={
                    "motivation": context.motivation_result.metadata.quality_score or 0
                    if context.motivation_result
                    else 0,
                    "chains": context.chains_result.metadata.quality_score or 0
                    if context.chains_result
                    else 0,
                },
                total_cost=context.total_cost,
                total_tokens=context.total_tokens,
            )

        except QualityGateFailure as e:
            logger.warning(
                "Quality gate failure",
                story_id=story.id,
                gate=e.gate_name,
                score=e.score,
            )
            story.status = StoryStatus.REJECTED
            await self.session.commit()

            return PipelineResult(
                success=False,
                story_id=story.id,
                error=f"Quality gate '{e.gate_name}' failed: {e.score:.2f} < {e.threshold:.2f}",
            )

        except HumanEscalationRequired as e:
            logger.warning(
                "Human escalation required",
                story_id=story.id,
                reason=e.reason,
            )
            # Keep story in analyzing state for human review
            return PipelineResult(
                success=False,
                story_id=story.id,
                error=f"Human escalation: {e.reason}",
            )

        except Exception as e:
            logger.error(
                "Pipeline error",
                story_id=story.id,
                error=str(e),
            )
            story.status = StoryStatus.PENDING  # Allow retry
            await self.session.commit()

            return PipelineResult(
                success=False,
                story_id=story.id,
                error=str(e),
            )

    async def _pass_foundation(self, context: PipelineContext) -> None:
        """
        Pass 1: Foundation.

        - Fact reconstruction
        - Context analysis
        - Actor profiling
        """
        logger.debug("Pass 1: Foundation", story_id=context.story.id)

        # For now, we extract foundation from the story itself
        # In full implementation, this would use dedicated agents
        context.foundation_data = {
            "facts_verified": len(context.story.key_events),
            "facts_total": len(context.story.key_events),
            "sources_count": 1,  # Simplified
            "key_events": context.story.key_events,
            "actors": context.story.primary_actors,
            "context_completeness": 0.8,  # Placeholder
        }

    async def _pass_analysis(self, context: PipelineContext) -> None:
        """
        Pass 2: Core Analysis.

        - Motivation analysis (4 layers)
        - Chain mapping
        - Subtlety analysis
        """
        logger.debug("Pass 2: Analysis", story_id=context.story.id)

        # Build input for motivation analysis
        story_context = StoryContext(
            headline=context.story.headline,
            summary=context.story.summary,
            key_events=context.story.key_events or ["Event not specified"],
            primary_actors=context.story.primary_actors or ["Actor not specified"],
            zones_affected=[context.story.primary_zone.value]
            + (context.story.secondary_zones or []),
        )

        analysis_context = AnalysisContext(
            historical_context="",  # Would come from foundation
            regional_context="",
            relevant_theories=[],
        )

        motivation_input = MotivationInput(
            story=story_context,
            context=analysis_context,
        )

        # Run motivation analysis
        context.motivation_result = await self.motivation_agent.run(motivation_input)

        if context.motivation_result.is_failure:
            raise PipelineError(f"Motivation analysis failed: {context.motivation_result.error}")

        # Track costs
        context.total_cost += context.motivation_result.metadata.cost_usd
        context.total_tokens += (
            context.motivation_result.metadata.input_tokens
            + context.motivation_result.metadata.output_tokens
        )

        # Record execution
        await self._record_execution(context, context.motivation_result.metadata)

        # Run chain mapping
        motivation_synthesis = ""
        if context.motivation_result.output:
            motivation_synthesis = (
                f"Primary driver: {context.motivation_result.output.synthesis.primary_driver}. "
                f"{context.motivation_result.output.synthesis.primary_driver_explanation}"
            )

        chains_input = ChainsInput(
            story=story_context,
            context=analysis_context,
            motivation_synthesis=motivation_synthesis,
        )

        context.chains_result = await self.chains_agent.run(chains_input)

        if context.chains_result.is_failure:
            raise PipelineError(f"Chain mapping failed: {context.chains_result.error}")

        # Track costs
        context.total_cost += context.chains_result.metadata.cost_usd
        context.total_tokens += (
            context.chains_result.metadata.input_tokens
            + context.chains_result.metadata.output_tokens
        )

        # Record execution
        await self._record_execution(context, context.chains_result.metadata)

    async def _pass_adversarial(self, context: PipelineContext) -> None:
        """
        Pass 3: Adversarial.

        - Debate protocol
        - Fact checking
        - Bias detection
        - Logic audit
        """
        logger.debug("Pass 3: Adversarial", story_id=context.story.id)

        # Simplified adversarial pass - in full implementation,
        # this would run debate agents, fact checkers, etc.
        context.adversarial_data = {
            "fact_check_score": 0.95,  # Placeholder
            "debate_resolution_score": 0.85,
            "bias_detection_score": 0.9,
            "logic_audit_score": 0.88,
            "unresolved_challenges": 0,
        }

    async def _pass_production(self, context: PipelineContext) -> None:
        """
        Pass 4: Production.

        - Article writing
        - Voice calibration
        - Final editing
        """
        logger.debug("Pass 4: Production", story_id=context.story.id)

        # Simplified production pass - in full implementation,
        # this would run writer agents, voice calibration, etc.
        context.production_data = {
            "writing_quality_score": 0.85,
            "voice_consistency_score": 0.88,
            "readability_score": 0.82,
        }

    async def _record_execution(
        self,
        context: PipelineContext,
        metadata: Any,
    ) -> None:
        """Record agent execution in database."""
        execution = AgentExecution(
            pipeline_run_id=context.pipeline_run_id,
            story_id=context.story.id,
            agent_name=metadata.agent_name,
            agent_version=metadata.agent_version,
            started_at=metadata.started_at,
            completed_at=metadata.completed_at,
            duration_ms=metadata.duration_ms,
            model_used=metadata.model_used,
            input_tokens=metadata.input_tokens,
            output_tokens=metadata.output_tokens,
            cost_usd=metadata.cost_usd,
            success=True,
            quality_score=metadata.quality_score,
        )
        context.session.add(execution)
        await context.session.flush()

    def _compile_analysis_data(self, context: PipelineContext) -> dict[str, Any]:
        """Compile all analysis data for storage."""
        data: dict[str, Any] = {
            "foundation": context.foundation_data,
            "adversarial": context.adversarial_data,
            "production": context.production_data,
        }

        if context.motivation_result and context.motivation_result.output:
            data["motivation"] = context.motivation_result.output.model_dump()

        if context.chains_result and context.chains_result.output:
            data["chains"] = context.chains_result.output.model_dump()

        return data

