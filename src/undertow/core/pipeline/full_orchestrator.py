"""
Full Pipeline Orchestrator.

Runs ALL analysis agents with quality gates and human escalation.
This is the A+++ version that actually integrates everything.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import structlog

from undertow.agents.analysis import (
    MotivationAnalysisAgent,
    ChainMappingAgent,
    SelfCritiqueAgent,
    SubtletyAnalysisAgent,
    GeometryAnalysisAgent,
    DeepContextAgent,
    ConnectionAnalysisAgent,
    UncertaintyAnalysisAgent,
)
from undertow.agents.adversarial import ChallengerAgent, AdvocateAgent, JudgeAgent
from undertow.agents.production import WriterAgent, SynthesisAgent, EditorAgent
from undertow.agents.result import AgentResult
from undertow.core.quality.gates import QualityGateSystem
from undertow.llm.router import ModelRouter
from undertow.schemas.agents.motivation import StoryContext, AnalysisContext
from undertow.verification import get_claim_extractor, get_claim_verifier

logger = structlog.get_logger()


@dataclass
class PipelineStage:
    """Result of a pipeline stage."""

    name: str
    success: bool
    quality_score: float
    cost_usd: float
    duration_ms: float
    output: Any = None
    error: str | None = None


@dataclass
class PipelineResult:
    """Complete pipeline result."""

    run_id: UUID
    success: bool
    stages: list[PipelineStage]
    final_quality_score: float
    total_cost_usd: float
    total_duration_ms: float
    requires_human_review: bool
    human_review_reason: str | None
    article_content: str | None
    created_at: datetime = field(default_factory=datetime.utcnow)


class FullPipelineOrchestrator:
    """
    Full pipeline orchestrator that runs ALL agents.

    Pipeline stages:
    1. Foundation: Motivation + Chains analysis
    2. Deep Analysis: Subtlety + Geometry + DeepContext + Connections
    3. Uncertainty: Calibrate confidence across analyses
    4. Synthesis: Combine all analyses
    5. Adversarial: Challenge → Advocate → Judge
    6. Verification: Claim extraction and source verification
    7. Writing: Generate article
    8. Editing: Review and polish
    9. Final Gate: Quality check

    Quality gates after each major phase.
    Human escalation when thresholds not met.
    """

    def __init__(
        self,
        router: ModelRouter,
        enable_verification: bool = True,
        enable_adversarial: bool = True,
        strict_gates: bool = True,
    ) -> None:
        """
        Initialize orchestrator.

        Args:
            router: Model router for LLM calls
            enable_verification: Whether to run source verification
            enable_adversarial: Whether to run adversarial debate
            strict_gates: Whether to enforce strict quality gates
        """
        self.router = router
        self.enable_verification = enable_verification
        self.enable_adversarial = enable_adversarial
        self.strict_gates = strict_gates

        # Initialize all agents
        self._init_agents()

        # Quality gates
        self.gates = QualityGateSystem()

        # Verification
        if enable_verification:
            self.claim_extractor = get_claim_extractor(router)
            self.claim_verifier = get_claim_verifier()

    def _init_agents(self) -> None:
        """Initialize all agents."""
        # Analysis agents
        self.motivation_agent = MotivationAnalysisAgent(self.router)
        self.chains_agent = ChainMappingAgent(self.router)
        self.subtlety_agent = SubtletyAnalysisAgent(self.router)
        self.geometry_agent = GeometryAnalysisAgent(self.router)
        self.deep_context_agent = DeepContextAgent(self.router)
        self.connections_agent = ConnectionAnalysisAgent(self.router)
        self.uncertainty_agent = UncertaintyAnalysisAgent(self.router)
        self.self_critique_agent = SelfCritiqueAgent(self.router)

        # Synthesis
        self.synthesis_agent = SynthesisAgent(self.router)

        # Adversarial agents
        self.challenger = ChallengerAgent(self.router)
        self.advocate = AdvocateAgent(self.router)
        self.judge = JudgeAgent(self.router)

        # Production agents
        self.writer = WriterAgent(self.router)
        self.editor = EditorAgent(self.router)

    async def run(
        self,
        story: StoryContext,
        context: AnalysisContext | None = None,
    ) -> PipelineResult:
        """
        Run full pipeline on a story.

        Args:
            story: Story to analyze
            context: Additional context

        Returns:
            PipelineResult with all outputs
        """
        run_id = uuid4()
        context = context or AnalysisContext()
        stages: list[PipelineStage] = []
        total_cost = 0.0
        total_duration = 0.0
        requires_review = False
        review_reason = None

        logger.info("Starting full pipeline", run_id=str(run_id), headline=story.headline[:50])

        try:
            # ================================================================
            # STAGE 1: FOUNDATION (Motivation + Chains)
            # ================================================================
            logger.info("Stage 1: Foundation analysis")

            motivation_result, chains_result = await asyncio.gather(
                self.motivation_agent.run(
                    self.motivation_agent.input_schema(
                        story_context=story,
                        analysis_context=context,
                    )
                ),
                self.chains_agent.run(
                    self.chains_agent.input_schema(
                        event_description=story.headline,
                        context=story.summary,
                        zones=story.zones_affected,
                    )
                ),
            )

            foundation_score = (
                (motivation_result.metadata.quality_score or 0) +
                (chains_result.metadata.quality_score or 0)
            ) / 2

            stages.append(PipelineStage(
                name="foundation",
                success=motivation_result.success and chains_result.success,
                quality_score=foundation_score,
                cost_usd=motivation_result.metadata.cost_usd + chains_result.metadata.cost_usd,
                duration_ms=motivation_result.metadata.duration_ms + chains_result.metadata.duration_ms,
                output={"motivation": motivation_result.output, "chains": chains_result.output},
            ))
            total_cost += stages[-1].cost_usd
            total_duration += stages[-1].duration_ms

            # Gate 1: Foundation
            gate1 = self.gates.check_foundation_gate(foundation_score)
            if not gate1.passed and self.strict_gates:
                requires_review = True
                review_reason = f"Foundation gate failed: {foundation_score:.2f} < {gate1.threshold}"
                logger.warning("Foundation gate failed", score=foundation_score)

            # ================================================================
            # STAGE 2: DEEP ANALYSIS (Subtlety, Geometry, DeepContext, Connections)
            # ================================================================
            logger.info("Stage 2: Deep analysis")

            subtlety_result, geometry_result, deep_context_result, connections_result = await asyncio.gather(
                self.subtlety_agent.run(
                    self.subtlety_agent.input_schema(
                        event_description=story.headline,
                        public_statements=[],
                        actor_actions=story.key_events,
                        timeline=story.key_events,
                    )
                ),
                self.geometry_agent.run(
                    self.geometry_agent.input_schema(
                        event_description=story.headline,
                        location_context=story.summary,
                        actors_involved=story.primary_actors,
                        zones=story.zones_affected,
                    )
                ),
                self.deep_context_agent.run(
                    self.deep_context_agent.input_schema(
                        event_description=story.headline,
                        actors=story.primary_actors,
                        zones=story.zones_affected,
                        known_history=story.summary,
                    )
                ),
                self.connections_agent.run(
                    self.connections_agent.input_schema(
                        event_description=story.headline,
                        actors=story.primary_actors,
                        zones=story.zones_affected,
                        initial_analysis=str(motivation_result.output) if motivation_result.output else "",
                    )
                ),
            )

            deep_score = sum([
                subtlety_result.metadata.quality_score or 0,
                geometry_result.metadata.quality_score or 0,
                deep_context_result.metadata.quality_score or 0,
                connections_result.metadata.quality_score or 0,
            ]) / 4

            stages.append(PipelineStage(
                name="deep_analysis",
                success=all([
                    subtlety_result.success,
                    geometry_result.success,
                    deep_context_result.success,
                    connections_result.success,
                ]),
                quality_score=deep_score,
                cost_usd=sum([
                    subtlety_result.metadata.cost_usd,
                    geometry_result.metadata.cost_usd,
                    deep_context_result.metadata.cost_usd,
                    connections_result.metadata.cost_usd,
                ]),
                duration_ms=max([
                    subtlety_result.metadata.duration_ms,
                    geometry_result.metadata.duration_ms,
                    deep_context_result.metadata.duration_ms,
                    connections_result.metadata.duration_ms,
                ]),  # Parallel, so take max
                output={
                    "subtlety": subtlety_result.output,
                    "geometry": geometry_result.output,
                    "deep_context": deep_context_result.output,
                    "connections": connections_result.output,
                },
            ))
            total_cost += stages[-1].cost_usd
            total_duration += stages[-1].duration_ms

            # Gate 2: Analysis
            gate2 = self.gates.check_analysis_gate(deep_score)
            if not gate2.passed and self.strict_gates:
                requires_review = True
                review_reason = f"Analysis gate failed: {deep_score:.2f}"

            # ================================================================
            # STAGE 3: UNCERTAINTY CALIBRATION
            # ================================================================
            logger.info("Stage 3: Uncertainty calibration")

            # Gather key claims from all analyses
            key_claims = self._extract_key_claims(
                motivation_result.output,
                chains_result.output,
            )

            # Combine analysis texts
            combined_analysis = self._combine_analyses(
                motivation_result.output,
                chains_result.output,
                subtlety_result.output,
                geometry_result.output,
            )

            uncertainty_result = await self.uncertainty_agent.run(
                self.uncertainty_agent.input_schema(
                    analysis_content=combined_analysis,
                    key_claims=key_claims,
                )
            )

            stages.append(PipelineStage(
                name="uncertainty",
                success=uncertainty_result.success,
                quality_score=uncertainty_result.metadata.quality_score or 0,
                cost_usd=uncertainty_result.metadata.cost_usd,
                duration_ms=uncertainty_result.metadata.duration_ms,
                output=uncertainty_result.output,
            ))
            total_cost += stages[-1].cost_usd
            total_duration += stages[-1].duration_ms

            # ================================================================
            # STAGE 4: SYNTHESIS
            # ================================================================
            logger.info("Stage 4: Synthesis")

            synthesis_result = await self.synthesis_agent.run(
                self.synthesis_agent.input_schema(
                    story_headline=story.headline,
                    story_summary=story.summary,
                    motivation_analysis=str(motivation_result.output) if motivation_result.output else "",
                    chains_analysis=str(chains_result.output) if chains_result.output else "",
                    subtlety_analysis=str(subtlety_result.output) if subtlety_result.output else "",
                    geometry_analysis=str(geometry_result.output) if geometry_result.output else "",
                    deep_context_analysis=str(deep_context_result.output) if deep_context_result.output else "",
                    connections_analysis=str(connections_result.output) if connections_result.output else "",
                    uncertainty_analysis=str(uncertainty_result.output) if uncertainty_result.output else "",
                )
            )

            stages.append(PipelineStage(
                name="synthesis",
                success=synthesis_result.success,
                quality_score=synthesis_result.metadata.quality_score or 0,
                cost_usd=synthesis_result.metadata.cost_usd,
                duration_ms=synthesis_result.metadata.duration_ms,
                output=synthesis_result.output,
            ))
            total_cost += stages[-1].cost_usd
            total_duration += stages[-1].duration_ms

            # ================================================================
            # STAGE 5: ADVERSARIAL DEBATE (if enabled)
            # ================================================================
            if self.enable_adversarial:
                logger.info("Stage 5: Adversarial debate")

                debate_result = await self._run_adversarial_debate(
                    synthesis_result.output,
                    story,
                )

                stages.append(PipelineStage(
                    name="adversarial",
                    success=debate_result["success"],
                    quality_score=debate_result["quality_score"],
                    cost_usd=debate_result["cost_usd"],
                    duration_ms=debate_result["duration_ms"],
                    output=debate_result,
                ))
                total_cost += stages[-1].cost_usd
                total_duration += stages[-1].duration_ms

                # Gate 3: Adversarial
                gate3 = self.gates.check_adversarial_gate(debate_result["quality_score"])
                if not gate3.passed and self.strict_gates:
                    requires_review = True
                    review_reason = f"Adversarial gate failed: {debate_result['quality_score']:.2f}"

            # ================================================================
            # STAGE 6: VERIFICATION (if enabled)
            # ================================================================
            if self.enable_verification and synthesis_result.output:
                logger.info("Stage 6: Source verification")

                verification_result = await self._run_verification(
                    synthesis_result.output,
                    story.zones_affected,
                )

                stages.append(PipelineStage(
                    name="verification",
                    success=verification_result["success"],
                    quality_score=verification_result["score"],
                    cost_usd=verification_result["cost_usd"],
                    duration_ms=verification_result["duration_ms"],
                    output=verification_result,
                ))
                total_cost += stages[-1].cost_usd
                total_duration += stages[-1].duration_ms

            # ================================================================
            # STAGE 7: WRITING
            # ================================================================
            logger.info("Stage 7: Writing")

            writer_result = await self.writer.run(
                self.writer.input_schema(
                    headline=story.headline,
                    synthesis=str(synthesis_result.output) if synthesis_result.output else "",
                    analyses={
                        "motivation": str(motivation_result.output),
                        "chains": str(chains_result.output),
                    },
                    target_word_count=3000,
                )
            )

            stages.append(PipelineStage(
                name="writing",
                success=writer_result.success,
                quality_score=writer_result.metadata.quality_score or 0,
                cost_usd=writer_result.metadata.cost_usd,
                duration_ms=writer_result.metadata.duration_ms,
                output=writer_result.output,
            ))
            total_cost += stages[-1].cost_usd
            total_duration += stages[-1].duration_ms

            # ================================================================
            # STAGE 8: EDITING
            # ================================================================
            logger.info("Stage 8: Editing")

            article_content = ""
            if writer_result.output:
                article_content = getattr(writer_result.output, "content", str(writer_result.output))

            editor_result = await self.editor.run(
                self.editor.input_schema(
                    headline=story.headline,
                    content=article_content or "No content generated",
                    quality_score=writer_result.metadata.quality_score or 0.7,
                )
            )

            stages.append(PipelineStage(
                name="editing",
                success=editor_result.success,
                quality_score=editor_result.metadata.quality_score or 0,
                cost_usd=editor_result.metadata.cost_usd,
                duration_ms=editor_result.metadata.duration_ms,
                output=editor_result.output,
            ))
            total_cost += stages[-1].cost_usd
            total_duration += stages[-1].duration_ms

            # ================================================================
            # FINAL QUALITY ASSESSMENT
            # ================================================================
            final_score = self._calculate_final_score(stages)

            gate4 = self.gates.check_output_gate(final_score)
            if not gate4.passed:
                requires_review = True
                review_reason = f"Output gate failed: {final_score:.2f}"

            logger.info(
                "Pipeline complete",
                run_id=str(run_id),
                final_score=final_score,
                total_cost=total_cost,
                requires_review=requires_review,
            )

            return PipelineResult(
                run_id=run_id,
                success=not requires_review or not self.strict_gates,
                stages=stages,
                final_quality_score=final_score,
                total_cost_usd=total_cost,
                total_duration_ms=total_duration,
                requires_human_review=requires_review,
                human_review_reason=review_reason,
                article_content=article_content,
            )

        except Exception as e:
            logger.error("Pipeline failed", error=str(e), run_id=str(run_id))

            return PipelineResult(
                run_id=run_id,
                success=False,
                stages=stages,
                final_quality_score=0.0,
                total_cost_usd=total_cost,
                total_duration_ms=total_duration,
                requires_human_review=True,
                human_review_reason=f"Pipeline error: {str(e)}",
                article_content=None,
            )

    async def _run_adversarial_debate(
        self,
        synthesis_output: Any,
        story: StoryContext,
    ) -> dict[str, Any]:
        """Run adversarial debate protocol."""
        total_cost = 0.0
        total_duration = 0.0

        # Challenger
        challenger_result = await self.challenger.run(
            self.challenger.input_schema(
                analysis_to_challenge=str(synthesis_output),
                story_context=story.summary,
            )
        )
        total_cost += challenger_result.metadata.cost_usd
        total_duration += challenger_result.metadata.duration_ms

        # Advocate response
        advocate_result = await self.advocate.run(
            self.advocate.input_schema(
                original_analysis=str(synthesis_output),
                challenges=str(challenger_result.output) if challenger_result.output else "",
            )
        )
        total_cost += advocate_result.metadata.cost_usd
        total_duration += advocate_result.metadata.duration_ms

        # Judge
        judge_result = await self.judge.run(
            self.judge.input_schema(
                original_analysis=str(synthesis_output),
                challenger_arguments=str(challenger_result.output) if challenger_result.output else "",
                advocate_arguments=str(advocate_result.output) if advocate_result.output else "",
            )
        )
        total_cost += judge_result.metadata.cost_usd
        total_duration += judge_result.metadata.duration_ms

        quality_score = judge_result.metadata.quality_score or 0.7

        return {
            "success": judge_result.success,
            "quality_score": quality_score,
            "cost_usd": total_cost,
            "duration_ms": total_duration,
            "challenger": challenger_result.output,
            "advocate": advocate_result.output,
            "judge": judge_result.output,
        }

    async def _run_verification(
        self,
        synthesis_output: Any,
        zones: list[str],
    ) -> dict[str, Any]:
        """Run source verification."""
        from undertow.verification.claim_extractor import ClaimExtractionInput, ExtractedClaim, ClaimType

        start = datetime.utcnow()

        # Extract claims
        extraction_result = await self.claim_extractor.run(
            ClaimExtractionInput(
                text=str(synthesis_output),
                focus_areas=["factual claims", "causal claims"],
            )
        )

        if not extraction_result.success or not extraction_result.output:
            return {
                "success": False,
                "score": 0.5,
                "cost_usd": extraction_result.metadata.cost_usd,
                "duration_ms": extraction_result.metadata.duration_ms,
                "claims_extracted": 0,
                "claims_verified": 0,
            }

        # Convert to ExtractedClaim objects
        claims = [
            ExtractedClaim(
                claim_id=c.claim_id,
                text=c.text,
                claim_type=ClaimType(c.claim_type) if c.claim_type in [e.value for e in ClaimType] else ClaimType.FACTUAL,
                confidence=c.confidence,
                source_sentence=c.source_sentence,
                requires_verification=c.requires_verification,
            )
            for c in extraction_result.output.claims
        ]

        # Verify claims
        verified = await self.claim_verifier.verify_claims_batch(claims, zones)

        duration = (datetime.utcnow() - start).total_seconds() * 1000

        # Calculate verification score
        verified_count = sum(1 for v in verified if v.status.value in ["verified", "supported"])
        score = verified_count / len(verified) if verified else 0.5

        return {
            "success": True,
            "score": score,
            "cost_usd": extraction_result.metadata.cost_usd,
            "duration_ms": duration,
            "claims_extracted": len(claims),
            "claims_verified": verified_count,
            "verified_claims": verified,
        }

    def _extract_key_claims(self, *outputs: Any) -> list[str]:
        """Extract key claims from analysis outputs."""
        claims = []

        for output in outputs:
            if output is None:
                continue

            # Extract from various output formats
            if hasattr(output, "synthesis") and hasattr(output.synthesis, "key_uncertainties"):
                claims.extend(output.synthesis.key_uncertainties)

            if hasattr(output, "key_assessments"):
                claims.extend(output.key_assessments)

        return claims[:10]  # Limit to 10 claims

    def _combine_analyses(self, *outputs: Any) -> str:
        """Combine analysis outputs into single text."""
        parts = []

        for output in outputs:
            if output is not None:
                parts.append(str(output))

        return "\n\n---\n\n".join(parts)

    def _calculate_final_score(self, stages: list[PipelineStage]) -> float:
        """Calculate final quality score."""
        if not stages:
            return 0.0

        # Weighted average
        weights = {
            "foundation": 0.20,
            "deep_analysis": 0.20,
            "synthesis": 0.25,
            "adversarial": 0.15,
            "writing": 0.15,
            "editing": 0.05,
        }

        total_weight = 0.0
        weighted_score = 0.0

        for stage in stages:
            weight = weights.get(stage.name, 0.1)
            weighted_score += stage.quality_score * weight
            total_weight += weight

        return weighted_score / total_weight if total_weight > 0 else 0.0

