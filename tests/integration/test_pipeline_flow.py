"""
Integration tests for the full pipeline flow.

These tests verify that components work together correctly.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from undertow.core.pipeline.orchestrator import PipelineOrchestrator
from undertow.core.pipeline.debate_orchestrator import DebateOrchestrator
from undertow.core.quality.gates import QualityGateSystem
from undertow.agents.result import AgentResult, AgentMetadata
from undertow.schemas.agents.motivation import (
    StoryContext,
    AnalysisContext,
    MotivationOutput,
    IndividualLayerAnalysis,
    InstitutionalLayerAnalysis,
    StructuralLayerAnalysis,
    OpportunisticLayerAnalysis,
    MotivationSynthesis,
)


@pytest.fixture
def mock_router() -> MagicMock:
    """Create mock router for tests."""
    router = MagicMock()
    router.complete = AsyncMock()
    router.get_cost_summary = MagicMock(return_value={"total_cost": 1.0, "calls": 5})
    return router


@pytest.fixture
def sample_story() -> StoryContext:
    """Create sample story for tests."""
    return StoryContext(
        headline="Major Power Announces Defense Agreement with Small Nation",
        summary=(
            "In a significant development, Major Power has signed a defense "
            "cooperation agreement with Small Nation, a strategically located "
            "country that has historically maintained neutrality. The agreement "
            "includes training, equipment transfers, and port access rights."
        ),
        key_events=[
            "Defense ministers met in Small Nation capital",
            "Agreement signed with 10-year term",
            "Regional powers expressed concern",
            "Traditional ally issued statement of disappointment",
        ],
        primary_actors=[
            "Major Power President",
            "Small Nation Prime Minister",
            "Regional Power",
            "Traditional Ally",
        ],
        zones_affected=["test_zone_1", "test_zone_2"],
    )


@pytest.fixture
def high_quality_motivation_output() -> MotivationOutput:
    """Create high-quality motivation output for testing."""
    return MotivationOutput(
        individual_layer=IndividualLayerAnalysis(
            decision_maker="Major Power President",
            political_position="Consolidating power in election year",
            domestic_needs="Demonstrating foreign policy wins to nationalist base",
            key_assessments=[
                "Leader is seeking to expand regional influence",
                "Domestic audience is the primary target",
            ],
            confidence=0.85,
        ),
        institutional_layer=InstitutionalLayerAnalysis(
            foreign_ministry_role="Executing long-planned pivot",
            military_intelligence_role="Driving force behind agreement",
            economic_actors=["Defense industry", "Port operators"],
            key_assessments=[
                "Military has been pushing for this access for years",
                "Commercial interests are secondary but aligned",
            ],
            confidence=0.80,
        ),
        structural_layer=StructuralLayerAnalysis(
            systemic_position="Rising power seeking regional dominance",
            threat_environment="Competition with Traditional Ally intensifying",
            economic_structure="Resource-hungry, seeking supply chain security",
            geographic_imperatives="Need for warm-water port access",
            key_assessments=[
                "Structural pressures make expansion logical",
                "Geography dictates the target",
            ],
            confidence=0.90,
        ),
        opportunistic_layer=OpportunisticLayerAnalysis(
            what_changed="Small Nation government changed, new PM more receptive",
            position_shifts=["Traditional Ally distracted by internal issues"],
            constraints_relaxed=["International scrutiny reduced"],
            window_analysis="Window opened by global attention elsewhere",
            key_assessments=[
                "Timing is explicitly opportunistic",
                "Window may close after Traditional Ally stabilizes",
            ],
            confidence=0.75,
        ),
        synthesis=MotivationSynthesis(
            primary_driver="Military-institutional push combined with leadership's domestic political needs",
            enabling_conditions=[
                "New receptive government in Small Nation",
                "Traditional Ally's distraction",
                "Reduced international scrutiny",
            ],
            alternative_explanations=[
                "Purely defensive posture against rising regional threat",
                "Economic access as primary rather than strategic",
            ],
            confidence_assessment=0.82,
            key_uncertainties=[
                "Extent of secret provisions in agreement",
                "Whether this is first step in larger plan",
            ],
        ),
    )


class TestPipelineOrchestration:
    """Tests for pipeline orchestration."""

    @pytest.mark.asyncio
    async def test_orchestrator_creates_agents(
        self,
        mock_router: MagicMock,
    ) -> None:
        """Test that orchestrator creates required agents."""
        orchestrator = PipelineOrchestrator(mock_router)

        assert orchestrator.motivation_agent is not None
        assert orchestrator.chains_agent is not None

    @pytest.mark.asyncio
    async def test_orchestrator_runs_with_mocked_agents(
        self,
        mock_router: MagicMock,
        sample_story: StoryContext,
        high_quality_motivation_output: MotivationOutput,
    ) -> None:
        """Test full pipeline run with mocked agent responses."""
        from undertow.schemas.agents.chains import ChainsOutput, ChainSynthesis

        # Create mock outputs
        mock_motivation_result = AgentResult(
            success=True,
            output=high_quality_motivation_output,
            metadata=AgentMetadata(
                quality_score=0.85,
                cost_usd=0.15,
                input_tokens=2000,
                output_tokens=1000,
                model_used="claude-sonnet-4-20250514",
                duration_ms=3000,
            ),
        )

        mock_chains_output = ChainsOutput(
            forward_chains=[],
            backward_chains=[],
            synthesis=ChainSynthesis(
                primary_chain_logic="Defense agreement is the first move in larger containment strategy",
                hidden_game_hypothesis="The real target is not Small Nation but Regional Power",
                key_tipping_points=["Regional Power response", "Traditional Ally counter-move"],
                recommended_monitoring=["Military movements", "Diplomatic statements"],
                confidence=0.78,
            ),
        )

        mock_chains_result = AgentResult(
            success=True,
            output=mock_chains_output,
            metadata=AgentMetadata(
                quality_score=0.82,
                cost_usd=0.12,
                input_tokens=1800,
                output_tokens=900,
                model_used="claude-sonnet-4-20250514",
                duration_ms=2500,
            ),
        )

        orchestrator = PipelineOrchestrator(mock_router)

        with patch.object(
            orchestrator.motivation_agent, "run", return_value=mock_motivation_result
        ), patch.object(
            orchestrator.chains_agent, "run", return_value=mock_chains_result
        ):
            result = await orchestrator.run(
                story_context=sample_story,
                analysis_context=AnalysisContext(),
            )

            assert result.success
            assert result.motivation is not None
            assert result.chains is not None
            assert result.total_cost > 0
            assert result.final_quality_score >= 0.8


class TestQualityGates:
    """Tests for quality gate integration."""

    def test_gates_enforce_thresholds(self) -> None:
        """Test that quality gates enforce thresholds correctly."""
        gates = QualityGateSystem()

        # Test passing
        high_result = gates.check_foundation_gate(0.85)
        assert high_result.passed

        # Test failing
        low_result = gates.check_foundation_gate(0.60)
        assert not low_result.passed

        # Test marginal
        marginal_result = gates.check_foundation_gate(0.76)
        assert marginal_result.passed

    def test_all_gates_have_thresholds(self) -> None:
        """Test all gate methods exist and work."""
        gates = QualityGateSystem()

        # All gates should be callable
        gates.check_foundation_gate(0.8)
        gates.check_analysis_gate(0.8)
        gates.check_adversarial_gate(0.8)
        gates.check_output_gate(0.8)


class TestDebateOrchestration:
    """Tests for debate orchestration."""

    @pytest.mark.asyncio
    async def test_debate_orchestrator_initialization(
        self,
        mock_router: MagicMock,
    ) -> None:
        """Test debate orchestrator initializes correctly."""
        orchestrator = DebateOrchestrator(mock_router)

        assert orchestrator.challenger is not None
        assert orchestrator.advocate is not None
        assert orchestrator.judge is not None
        assert orchestrator.max_rounds == 3

    @pytest.mark.asyncio
    async def test_quick_challenge(
        self,
        mock_router: MagicMock,
    ) -> None:
        """Test quick challenge functionality."""
        from undertow.schemas.agents.debate import ChallengerOutput, DebateChallenge

        mock_challenge_output = ChallengerOutput(
            challenges=[
                DebateChallenge(
                    challenge_id="c1",
                    challenge_type="alternative_explanation",
                    target_claim="Primary motivation was domestic politics",
                    challenge_text="The analysis underweights the military-institutional drivers that have been pushing for this for years. This may be military-led, not politically-led.",
                    severity="medium",
                    evidence_requested=["Military leadership statements", "Timing of military requests"],
                ),
            ],
            overall_assessment="Analysis is solid but may underweight institutional factors",
            analysis_strength_rating=0.75,
        )

        mock_result = AgentResult(
            success=True,
            output=mock_challenge_output,
            metadata=AgentMetadata(
                quality_score=0.80,
                cost_usd=0.10,
                input_tokens=1500,
                output_tokens=700,
                model_used="claude-sonnet-4-20250514",
                duration_ms=2000,
            ),
        )

        orchestrator = DebateOrchestrator(mock_router)

        with patch.object(
            orchestrator.challenger, "run", return_value=mock_result
        ):
            result = await orchestrator.quick_challenge(
                claim="The leader's primary motivation was domestic politics",
                context="Analysis of defense agreement",
            )

            assert result["success"]
            assert len(result["challenges"]) == 1


class TestBatchProcessing:
    """Tests for batch processing utilities."""

    @pytest.mark.asyncio
    async def test_batch_processor(self) -> None:
        """Test batch processor handles items correctly."""
        from undertow.core.batch import BatchProcessor

        async def process_item(x: int) -> int:
            return x * 2

        processor = BatchProcessor(
            process_func=process_item,
            concurrency=3,
        )

        items = list(range(10))
        result = await processor.process(items)

        assert result.total == 10
        assert result.successful == 10
        assert result.failed == 0
        assert len(result.results) == 10

    @pytest.mark.asyncio
    async def test_batch_processor_handles_errors(self) -> None:
        """Test batch processor continues on errors."""
        from undertow.core.batch import BatchProcessor

        async def process_item(x: int) -> int:
            if x == 5:
                raise ValueError("Test error")
            return x * 2

        processor = BatchProcessor(
            process_func=process_item,
            concurrency=3,
            continue_on_error=True,
        )

        items = list(range(10))
        result = await processor.process(items)

        assert result.total == 10
        assert result.successful == 9
        assert result.failed == 1
        assert len(result.errors) == 1


class TestLLMCaching:
    """Tests for LLM caching."""

    @pytest.mark.asyncio
    async def test_cache_miss_then_hit(self) -> None:
        """Test cache stores and retrieves correctly."""
        from undertow.infrastructure.llm_cache import LLMCache
        from unittest.mock import AsyncMock

        # Mock the cache backend
        mock_cache = MagicMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()

        llm_cache = LLMCache()
        llm_cache._cache = mock_cache

        messages = [{"role": "user", "content": "Test message"}]
        model = "test-model"

        # First call should be miss
        result = await llm_cache.get(messages, model)
        assert result is None
        assert llm_cache.misses == 1

        # Store response
        await llm_cache.set(
            messages, model, "Test response", 100, 50
        )
        mock_cache.set.assert_called_once()

    def test_cache_stats(self) -> None:
        """Test cache statistics tracking."""
        from undertow.infrastructure.llm_cache import LLMCache

        cache = LLMCache()
        cache.hits = 10
        cache.misses = 5

        stats = cache.get_stats()

        assert stats["hits"] == 10
        assert stats["misses"] == 5
        assert stats["total"] == 15
        assert abs(stats["hit_rate"] - 0.667) < 0.01

