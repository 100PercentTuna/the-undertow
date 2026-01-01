"""
End-to-end pipeline tests.

These tests verify the complete pipeline flow from story to article.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from undertow.agents.analysis.motivation import MotivationAnalysisAgent
from undertow.agents.analysis.chains import ChainMappingAgent
from undertow.agents.adversarial.debate import ChallengerAgent
from undertow.core.pipeline.orchestrator import PipelineOrchestrator
from undertow.core.quality.gates import QualityGateSystem
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
from undertow.schemas.agents.chains import (
    ChainsOutput,
    ForwardChain,
    ChainSynthesis,
)


@pytest.fixture
def sample_story() -> StoryContext:
    """Create a sample story for testing."""
    return StoryContext(
        headline="Test Country Announces Major Policy Shift",
        summary=(
            "Test Country has announced a significant shift in its foreign policy, "
            "moving closer to Regional Power while distancing from Traditional Ally. "
            "The move comes amid economic pressures and security concerns."
        ),
        key_events=[
            "Foreign minister visits Regional Power capital",
            "Trade agreement signed",
            "Traditional Ally ambassador recalled for consultations",
        ],
        primary_actors=[
            "Test Country President",
            "Test Country Foreign Minister",
            "Regional Power",
            "Traditional Ally",
        ],
        zones_affected=["test_zone_1", "test_zone_2"],
    )


@pytest.fixture
def mock_motivation_output() -> MotivationOutput:
    """Create mock motivation analysis output."""
    return MotivationOutput(
        individual_layer=IndividualLayerAnalysis(
            decision_maker="Test Country President",
            political_position="Secure, but facing economic challenges",
            domestic_needs="Economic relief for population",
            key_assessments=[
                "Leader is seeking to diversify economic partnerships",
                "Political capital is high but economic situation is dire",
            ],
            confidence=0.8,
        ),
        institutional_layer=InstitutionalLayerAnalysis(
            foreign_ministry_role="Driving force behind the shift",
            military_intelligence_role="Supportive of security cooperation",
            economic_actors=["State energy company", "Export industries"],
            key_assessments=[
                "Foreign ministry has been advocating this for years",
                "Military sees opportunity for equipment deals",
            ],
            confidence=0.75,
        ),
        structural_layer=StructuralLayerAnalysis(
            systemic_position="Middle power seeking strategic autonomy",
            threat_environment="Growing pressure from Traditional Ally",
            economic_structure="Resource-dependent, seeking diversification",
            geographic_imperatives="Need for regional trade routes",
            key_assessments=[
                "Structural pressures make pivot logical",
                "Geography favors regional integration",
            ],
            confidence=0.85,
        ),
        opportunistic_layer=OpportunisticLayerAnalysis(
            what_changed="Traditional Ally imposed new sanctions",
            position_shifts=["Regional Power offered better terms"],
            constraints_relaxed=["Previous security concerns addressed"],
            window_analysis="Window created by Traditional Ally's distraction elsewhere",
            key_assessments=[
                "Timing is opportunistic",
                "Window may close if Traditional Ally refocuses",
            ],
            confidence=0.7,
        ),
        synthesis=MotivationSynthesis(
            primary_driver="Economic pressure combined with opportunistic timing",
            enabling_conditions=[
                "Regional Power readiness to engage",
                "Traditional Ally's distraction",
            ],
            alternative_explanations=[
                "Pure economic necessity driving all decisions",
                "Long-planned strategic reorientation",
            ],
            confidence_assessment=0.78,
            key_uncertainties=[
                "True extent of leader's commitment to shift",
                "Whether this is tactical or strategic",
            ],
        ),
    )


@pytest.fixture
def mock_chains_output() -> ChainsOutput:
    """Create mock chains analysis output."""
    return ChainsOutput(
        forward_chains=[
            ForwardChain(
                order=1,
                description="Traditional Ally responds with diplomatic pressure",
                affected_actors=["Traditional Ally", "Test Country"],
                probability="high",
                timeframe="1-3 months",
            ),
            ForwardChain(
                order=2,
                description="Regional Power increases support",
                affected_actors=["Regional Power", "Test Country"],
                probability="medium",
                timeframe="3-6 months",
            ),
        ],
        backward_chains=[],
        synthesis=ChainSynthesis(
            primary_chain_logic="Economic necessity drives regional realignment",
            hidden_game_hypothesis=(
                "The real play may be leveraging Regional Power interest "
                "to extract concessions from Traditional Ally"
            ),
            key_tipping_points=["Traditional Ally response", "Economic outcomes"],
            recommended_monitoring=[
                "Trade flow data",
                "Diplomatic statements",
            ],
            confidence=0.75,
        ),
    )


class TestQualityGateSystem:
    """Tests for the quality gate system."""

    def test_gate_pass(self) -> None:
        """Test that high quality passes gates."""
        gates = QualityGateSystem()

        result = gates.check_foundation_gate(0.80)
        assert result.passed

        result = gates.check_analysis_gate(0.85)
        assert result.passed

    def test_gate_fail(self) -> None:
        """Test that low quality fails gates."""
        gates = QualityGateSystem()

        result = gates.check_foundation_gate(0.60)
        assert not result.passed

        result = gates.check_analysis_gate(0.70)
        assert not result.passed

    def test_marginal_pass(self) -> None:
        """Test marginal pass with remediation."""
        gates = QualityGateSystem()

        result = gates.check_foundation_gate(0.76)
        assert result.passed
        # Should be marginal pass


class TestPipelineOrchestrator:
    """Tests for the pipeline orchestrator."""

    @pytest.fixture
    def mock_router(self) -> MagicMock:
        """Create mock router."""
        router = MagicMock()
        router.complete = AsyncMock()
        router.get_cost_summary = MagicMock(return_value={
            "total_cost": 0.50,
            "calls": 10,
        })
        return router

    @pytest.mark.asyncio
    async def test_orchestrator_initialization(
        self,
        mock_router: MagicMock,
    ) -> None:
        """Test orchestrator initializes correctly."""
        orchestrator = PipelineOrchestrator(mock_router)
        assert orchestrator is not None
        assert orchestrator.router == mock_router

    @pytest.mark.asyncio
    async def test_full_pipeline_with_mocks(
        self,
        mock_router: MagicMock,
        sample_story: StoryContext,
        mock_motivation_output: MotivationOutput,
        mock_chains_output: ChainsOutput,
    ) -> None:
        """Test full pipeline with mocked agent outputs."""
        # This test verifies the pipeline structure
        # Actual LLM calls would require integration testing

        from undertow.agents.result import AgentResult, AgentMetadata

        # Create mock agent results
        mock_motivation_result = AgentResult(
            success=True,
            output=mock_motivation_output,
            metadata=AgentMetadata(
                quality_score=0.85,
                cost_usd=0.10,
                input_tokens=1000,
                output_tokens=500,
                model_used="claude-sonnet-4-20250514",
                duration_ms=2000,
            ),
        )

        mock_chains_result = AgentResult(
            success=True,
            output=mock_chains_output,
            metadata=AgentMetadata(
                quality_score=0.82,
                cost_usd=0.08,
                input_tokens=800,
                output_tokens=400,
                model_used="claude-sonnet-4-20250514",
                duration_ms=1800,
            ),
        )

        orchestrator = PipelineOrchestrator(mock_router)

        # Patch the agents to return our mock results
        with patch.object(
            orchestrator.motivation_agent, "run", return_value=mock_motivation_result
        ), patch.object(
            orchestrator.chains_agent, "run", return_value=mock_chains_result
        ):
            result = await orchestrator.run(
                story_context=sample_story,
                analysis_context=AnalysisContext(),
            )

            # Verify result structure
            assert result is not None
            assert result.success
            assert result.motivation == mock_motivation_output
            assert result.chains == mock_chains_output
            assert result.total_cost > 0


class TestAnalysisAgentIntegration:
    """Integration tests for analysis agents."""

    @pytest.fixture
    def mock_router(self) -> MagicMock:
        """Create mock router."""
        router = MagicMock()
        router.complete = AsyncMock()
        return router

    def test_motivation_agent_message_building(
        self,
        mock_router: MagicMock,
        sample_story: StoryContext,
    ) -> None:
        """Test motivation agent builds correct messages."""
        agent = MotivationAnalysisAgent(mock_router)

        from undertow.schemas.agents.motivation import MotivationInput

        input_data = MotivationInput(
            story=sample_story,
            context=AnalysisContext(),
        )

        messages = agent._build_messages(input_data)

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert sample_story.headline in messages[1]["content"]

    def test_chains_agent_message_building(
        self,
        mock_router: MagicMock,
        sample_story: StoryContext,
    ) -> None:
        """Test chains agent builds correct messages."""
        agent = ChainMappingAgent(mock_router)

        from undertow.schemas.agents.chains import ChainsInput

        input_data = ChainsInput(
            story=sample_story,
            context=AnalysisContext(),
        )

        messages = agent._build_messages(input_data)

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "fourth" in messages[0]["content"].lower()  # Fourth-order thinking


class TestDebateProtocol:
    """Tests for the debate protocol."""

    @pytest.fixture
    def mock_router(self) -> MagicMock:
        """Create mock router."""
        router = MagicMock()
        router.complete = AsyncMock()
        return router

    def test_challenger_message_building(
        self,
        mock_router: MagicMock,
    ) -> None:
        """Test challenger agent builds correct messages."""
        agent = ChallengerAgent(mock_router)

        from undertow.schemas.agents.debate import ChallengerInput

        input_data = ChallengerInput(
            analysis_summary="The leader acted primarily due to domestic pressure.",
            key_claims=[
                "Domestic politics was the primary driver",
                "Timing was dictated by election cycle",
            ],
        )

        messages = agent._build_messages(input_data)

        assert len(messages) == 2
        assert "challenger" in messages[0]["content"].lower()
        assert "domestic" in messages[1]["content"].lower()

