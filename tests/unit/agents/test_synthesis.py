"""
Unit tests for Synthesis Agent.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from undertow.agents.production.synthesis import SynthesisAgent
from undertow.agents.result import AgentResult, AgentMetadata
from undertow.schemas.agents.synthesis import (
    SynthesisInput,
    SynthesisOutput,
    KeyFinding,
    NarrativeThread,
    ReaderTakeaway,
    MonitoringRecommendation,
)


@pytest.fixture
def mock_router() -> MagicMock:
    """Create a mock router."""
    router = MagicMock()
    router.complete = AsyncMock()
    return router


@pytest.fixture
def sample_input() -> SynthesisInput:
    """Create sample synthesis input."""
    return SynthesisInput(
        story_headline="Major Defense Agreement Signed",
        story_summary=(
            "Two nations have signed a comprehensive defense agreement "
            "that includes military training, equipment transfers, and "
            "port access rights, marking a significant shift in regional dynamics."
        ),
        motivation_analysis=(
            "Four-layer analysis reveals the decision was driven primarily by "
            "structural pressures (need for sea access) combined with opportunistic "
            "timing (new receptive government in partner nation)."
        ),
        chains_analysis=(
            "Forward chains extend to fifth order: regional rivals will respond, "
            "creating pressure on neighboring states, eventually affecting global "
            "shipping routes and great power competition."
        ),
        subtlety_analysis=(
            "Key signals: the eloquent silence from traditionally vocal powers "
            "suggests tacit approval. Timing before major summit is deliberate."
        ),
        geometry_analysis=(
            "Strategic geography is central: this provides access to critical "
            "chokepoint, bypassing current bottleneck."
        ),
        deep_context_analysis=(
            "Historical grievances play a role: partner nation has memories "
            "of past abandonment that make this relationship appealing."
        ),
        connections_analysis=(
            "Non-obvious connection: this mirrors a similar agreement 30 years ago "
            "that reshaped regional order for a generation."
        ),
        target_word_count=500,
    )


@pytest.fixture
def sample_output() -> SynthesisOutput:
    """Create sample synthesis output."""
    return SynthesisOutput(
        executive_summary=(
            "This defense agreement represents far more than a bilateral deal—it's "
            "a strategic repositioning that will reshape regional dynamics for years "
            "to come. The combination of structural pressures (need for sea access) "
            "and opportunistic timing (new government) created a window that skilled "
            "diplomats exploited effectively. The real significance lies not in what "
            "was signed but in the chains of consequences it sets in motion."
        ),
        key_findings=[
            KeyFinding(
                finding=(
                    "The agreement was driven primarily by structural geographic "
                    "imperatives—the need for chokepoint access—rather than the "
                    "stated rationale of enhanced security cooperation."
                ),
                sources=["motivation_analysis", "geometry_analysis"],
                confidence=0.85,
                importance="critical",
            ),
            KeyFinding(
                finding=(
                    "Major powers' silence constitutes tacit approval and suggests "
                    "this was coordinated in advance through back channels."
                ),
                sources=["subtlety_analysis"],
                confidence=0.75,
                importance="high",
            ),
            KeyFinding(
                finding=(
                    "Fourth and fifth-order consequences will reshape regional "
                    "shipping patterns and affect great power competition."
                ),
                sources=["chains_analysis"],
                confidence=0.70,
                importance="high",
            ),
        ],
        narrative_threads=[
            NarrativeThread(
                thread_name="Geographic Imperative",
                description=(
                    "The thread connecting motivation, chains, and geometry all "
                    "points to sea access as the underlying driver. This is not "
                    "about defense cooperation—it's about chokepoint control."
                ),
                elements=[
                    "Structural pressure for sea access (motivation)",
                    "Chokepoint strategic value (geometry)",
                    "Shipping route implications (chains)",
                ],
                significance=(
                    "Understanding this as a geographic play rather than "
                    "diplomatic achievement explains both the action and "
                    "likely consequences."
                ),
            ),
        ],
        contradictions_resolved=[],
        the_real_story=(
            "The game being played is not defense cooperation—it's chokepoint "
            "positioning in anticipation of great power competition intensifying. "
            "The stated rationale (security partnership) is cover for the actual "
            "objective (strategic geography). Major powers' silence is permission, "
            "not indifference."
        ),
        reader_takeaways=[
            ReaderTakeaway(
                takeaway=(
                    "When a bilateral deal provokes regional silence rather than "
                    "regional protest, the deal was pre-coordinated with key powers."
                ),
                why_it_matters=(
                    "This pattern helps identify genuine surprises from "
                    "orchestrated moves in future developments."
                ),
                confidence=0.80,
            ),
            ReaderTakeaway(
                takeaway=(
                    "Geographic imperatives outlast governments—this access "
                    "advantage will persist through future political changes."
                ),
                why_it_matters=(
                    "Helps distinguish durable strategic shifts from "
                    "transient diplomatic achievements."
                ),
                confidence=0.85,
            ),
        ],
        monitoring_recommendations=[
            MonitoringRecommendation(
                indicator="Regional rival military posture changes",
                why="First signal of counter-balancing response",
                timeframe="3-6 months",
                what_it_would_mean=(
                    "Rapid response suggests rival sees this as major threat; "
                    "delayed response suggests rival is constrained."
                ),
            ),
            MonitoringRecommendation(
                indicator="Shipping route usage patterns",
                why="Commercial response reveals market assessment of durability",
                timeframe="6-12 months",
                what_it_would_mean=(
                    "Significant route shifts confirm strategic value; "
                    "minimal change suggests symbolic over substantive."
                ),
            ),
        ],
        overall_confidence=0.78,
        word_count=487,
    )


class TestSynthesisAgent:
    """Tests for SynthesisAgent."""

    def test_agent_initialization(self, mock_router: MagicMock) -> None:
        """Test agent initializes correctly."""
        agent = SynthesisAgent(mock_router)

        assert agent.task_name == "synthesis"
        assert agent.version == "1.0.0"

    def test_build_messages(
        self,
        mock_router: MagicMock,
        sample_input: SynthesisInput,
    ) -> None:
        """Test message building includes all analyses."""
        agent = SynthesisAgent(mock_router)
        messages = agent._build_messages(sample_input)

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

        user_content = messages[1]["content"]
        assert "Major Defense Agreement" in user_content
        assert "MOTIVATION ANALYSIS" in user_content
        assert "CHAINS ANALYSIS" in user_content
        assert "SUBTLETY ANALYSIS" in user_content

    @pytest.mark.asyncio
    async def test_quality_assessment(
        self,
        mock_router: MagicMock,
        sample_input: SynthesisInput,
        sample_output: SynthesisOutput,
    ) -> None:
        """Test quality assessment scoring."""
        agent = SynthesisAgent(mock_router)
        score = await agent._assess_quality(sample_output, sample_input)

        # High quality output should score well
        assert score >= 0.8

    @pytest.mark.asyncio
    async def test_quality_assessment_low_quality(
        self,
        mock_router: MagicMock,
        sample_input: SynthesisInput,
    ) -> None:
        """Test quality assessment penalizes low quality."""
        agent = SynthesisAgent(mock_router)

        low_quality_output = SynthesisOutput(
            executive_summary="Short summary.",  # Too short
            key_findings=[
                KeyFinding(
                    finding="Short finding without much substance here.",
                    sources=["one"],  # Only one source
                    confidence=0.5,
                    importance="low",
                ),
            ],
            narrative_threads=[],  # Empty
            contradictions_resolved=[],
            the_real_story="Brief.",  # Too short
            reader_takeaways=[
                ReaderTakeaway(
                    takeaway="Brief takeaway without substance.",
                    why_it_matters="Brief.",
                    confidence=0.5,
                ),
            ],
            monitoring_recommendations=[
                MonitoringRecommendation(
                    indicator="One thing",
                    why="Reason",
                    timeframe="Soon",
                    what_it_would_mean="Something.",
                ),
            ],
            overall_confidence=0.5,
            word_count=50,
        )

        score = await agent._assess_quality(low_quality_output, sample_input)

        # Low quality output should score poorly
        assert score < 0.7


class TestSynthesisSchemas:
    """Tests for synthesis schemas."""

    def test_key_finding_validation(self) -> None:
        """Test KeyFinding validation."""
        finding = KeyFinding(
            finding="This is a finding that meets the minimum length requirement for validation.",
            sources=["motivation_analysis", "chains_analysis"],
            confidence=0.85,
            importance="high",
        )

        assert finding.confidence == 0.85
        assert len(finding.sources) == 2

    def test_synthesis_output_validation(self, sample_output: SynthesisOutput) -> None:
        """Test SynthesisOutput validation."""
        assert len(sample_output.key_findings) >= 3
        assert len(sample_output.narrative_threads) >= 1
        assert len(sample_output.reader_takeaways) >= 2
        assert sample_output.overall_confidence >= 0
        assert sample_output.overall_confidence <= 1

