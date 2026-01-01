"""
Unit tests for Editor Agent.
"""

import pytest
from unittest.mock import MagicMock

from undertow.agents.production.editor import EditorAgent, EditorInput, EditorOutput, EditSuggestion


@pytest.fixture
def mock_router() -> MagicMock:
    """Create a mock router."""
    router = MagicMock()
    return router


@pytest.fixture
def sample_article() -> EditorInput:
    """Create sample article for editing."""
    return EditorInput(
        headline="Major Power Announces Defense Agreement with Small Nation",
        subhead="A strategic shift in the region's balance of power",
        content="""
        In a significant development that will reshape regional dynamics for years to come,
        Major Power has signed a comprehensive defense agreement with Small Nation, a
        strategically located country that has historically maintained neutrality.
        
        The agreement, announced Tuesday at a ceremony in Small Nation's capital, includes
        provisions for military training, equipment transfers, and—most significantly—port
        access rights that give Major Power a foothold at a critical maritime chokepoint.
        
        Why This Matters
        
        The timing is not coincidental. Major Power has been seeking expanded maritime access
        for years, constrained by geography and regional opposition. Small Nation's new
        government, which took office six months ago, has proven more receptive to such
        overtures than its predecessor.
        
        What's particularly striking is the eloquent silence from Regional Rival, which
        traditionally protests any Major Power expansion in the region. This silence—neither
        endorsement nor condemnation—suggests the deal was coordinated in advance through
        back channels.
        
        The Chains of Consequence
        
        First-order effects are straightforward: Major Power gains strategic access, Small
        Nation gains security guarantees and economic investment. But trace the chains further:
        
        Second order: Regional Rival must respond, likely by deepening ties with Major
        Power's adversaries.
        
        Third order: Other small states in the region recalibrate their neutrality calculations.
        
        Fourth order: Global shipping patterns may shift as the chokepoint's strategic
        importance increases.
        
        Fifth order: Great power competition intensifies in a region previously considered
        peripheral to major rivalry.
        
        What We Don't Know
        
        Several questions remain unanswered:
        - What are the unpublished provisions of the agreement?
        - Was there a quid pro quo involving Regional Rival's silence?
        - How will this affect ongoing negotiations in adjacent disputes?
        
        The Takeaway
        
        This agreement represents a significant shift in regional power dynamics. Watch
        for Regional Rival's response in the coming weeks—the nature of that response
        will reveal whether this was a surprise or an orchestrated move in a larger game.
        """,
        quality_score=0.82,
        word_count=350,
        target_word_count=500,
    )


@pytest.fixture
def sample_editor_output() -> EditorOutput:
    """Create sample editor output."""
    return EditorOutput(
        overall_assessment=(
            "This is a solid piece that demonstrates The Undertow's analytical depth. "
            "The multi-order chain analysis is excellent, and the voice is consistent. "
            "A few minor issues prevent it from being publication-ready as is."
        ),
        quality_rating="good",
        ready_for_publication=False,
        edit_suggestions=[
            EditSuggestion(
                location="Opening paragraph",
                issue_type="style",
                original_text="In a significant development that will reshape",
                suggested_text="A defense agreement signed Tuesday will reshape",
                rationale="Avoid 'significant development' - show don't tell",
                priority="recommended",
            ),
            EditSuggestion(
                location="Third paragraph",
                issue_type="voice",
                original_text="Why This Matters",
                suggested_text="[Remove subhead, integrate into narrative]",
                rationale="The Undertow doesn't use section headers in articles",
                priority="required",
            ),
        ],
        voice_consistency=0.85,
        strengths=[
            "Chain analysis is thorough and well-reasoned",
            "Uncertainty acknowledged appropriately",
            "Avoids passive voice throughout",
            "Concrete details rather than abstractions",
        ],
        weaknesses=[
            "Section headers break the narrative flow",
            "Opening could be sharper",
            "Could use one more non-obvious connection",
        ],
        revised_quality_score=0.88,
    )


class TestEditorAgent:
    """Tests for EditorAgent."""

    def test_agent_initialization(self, mock_router: MagicMock) -> None:
        """Test agent initializes correctly."""
        agent = EditorAgent(mock_router)

        assert agent.task_name == "editor"
        assert agent.version == "1.0.0"

    def test_build_messages(
        self,
        mock_router: MagicMock,
        sample_article: EditorInput,
    ) -> None:
        """Test message building includes article content."""
        agent = EditorAgent(mock_router)
        messages = agent._build_messages(sample_article)

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

        user_content = messages[1]["content"]
        assert "Major Power Announces" in user_content
        assert "regional dynamics" in user_content.lower()

        system_content = messages[0]["content"]
        assert "FORBIDDEN PHRASES" in system_content
        assert "Time will tell" in system_content

    @pytest.mark.asyncio
    async def test_quality_assessment(
        self,
        mock_router: MagicMock,
        sample_article: EditorInput,
        sample_editor_output: EditorOutput,
    ) -> None:
        """Test quality assessment scoring."""
        agent = EditorAgent(mock_router)
        score = await agent._assess_quality(sample_editor_output, sample_article)

        # Good output should score well
        assert score >= 0.8

    @pytest.mark.asyncio
    async def test_quality_assessment_minimal(
        self,
        mock_router: MagicMock,
        sample_article: EditorInput,
    ) -> None:
        """Test quality assessment penalizes minimal review."""
        agent = EditorAgent(mock_router)

        minimal_output = EditorOutput(
            overall_assessment="It's fine.",  # Too short
            quality_rating="good",
            ready_for_publication=True,
            edit_suggestions=[],  # No suggestions
            voice_consistency=0.9,
            strengths=[],  # No strengths listed
            weaknesses=[],  # No weaknesses listed
            revised_quality_score=0.9,
        )

        score = await agent._assess_quality(minimal_output, sample_article)

        # Minimal review should score poorly
        assert score < 0.6


class TestEditorSchemas:
    """Tests for editor schemas."""

    def test_edit_suggestion_validation(self) -> None:
        """Test EditSuggestion validation."""
        suggestion = EditSuggestion(
            location="First paragraph",
            issue_type="clarity",
            original_text="The text to replace",
            suggested_text="Better text",
            rationale="This improves clarity for readers",
            priority="recommended",
        )

        assert suggestion.issue_type == "clarity"
        assert suggestion.priority == "recommended"

    def test_editor_output_validation(self, sample_editor_output: EditorOutput) -> None:
        """Test EditorOutput validation."""
        assert sample_editor_output.quality_rating in [
            "excellent", "good", "acceptable", "needs_work", "major_revision"
        ]
        assert 0 <= sample_editor_output.voice_consistency <= 1
        assert 0 <= sample_editor_output.revised_quality_score <= 1

    def test_issue_types(self) -> None:
        """Test all issue types are valid."""
        valid_types = [
            "factual", "clarity", "voice", "structure",
            "length", "missing_context", "overconfidence", "style"
        ]

        for issue_type in valid_types:
            suggestion = EditSuggestion(
                location="Test",
                issue_type=issue_type,
                original_text="Original",
                suggested_text="New",
                rationale="Valid rationale here",
                priority="optional",
            )
            assert suggestion.issue_type == issue_type

