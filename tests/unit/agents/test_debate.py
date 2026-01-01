"""
Tests for debate agents.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from undertow.agents.adversarial.debate import (
    ChallengerAgent,
    AdvocateAgent,
    JudgeAgent,
)
from undertow.schemas.agents.debate import (
    ChallengerInput,
    ChallengerOutput,
    AdvocateInput,
    AdvocateOutput,
    JudgeInput,
    JudgeOutput,
    DebateChallenge,
    AdvocateResponse,
)


class TestChallengerAgent:
    """Tests for ChallengerAgent."""

    @pytest.fixture
    def mock_router(self) -> MagicMock:
        """Create mock router."""
        router = MagicMock()
        router.complete = AsyncMock()
        return router

    @pytest.fixture
    def challenger(self, mock_router: MagicMock) -> ChallengerAgent:
        """Create challenger with mock router."""
        return ChallengerAgent(mock_router)

    def test_task_name(self, challenger: ChallengerAgent) -> None:
        """Test task name is correct."""
        assert challenger.task_name == "challenger"

    def test_build_messages(self, challenger: ChallengerAgent) -> None:
        """Test message building."""
        input_data = ChallengerInput(
            analysis_summary="The leader acted to shore up domestic support.",
            key_claims=[
                "Primary motivation was domestic politics",
                "Timing driven by election cycle",
            ],
        )

        messages = challenger._build_messages(input_data)

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "domestic politics" in messages[1]["content"]

    @pytest.mark.asyncio
    async def test_parse_output(self, challenger: ChallengerAgent) -> None:
        """Test output parsing."""
        raw_output = """{
            "challenges": [
                {
                    "challenge_id": "c1",
                    "challenge_type": "alternative_explanation",
                    "target_claim": "Primary motivation was domestic politics",
                    "challenge_text": "The analysis overlooks significant international pressure that preceded this action, suggesting external factors may have been equally or more important than domestic considerations.",
                    "severity": "medium",
                    "evidence_requested": ["Timeline of international events", "Statements from foreign governments"]
                }
            ],
            "overall_assessment": "The analysis presents a coherent argument but may underweight external factors.",
            "analysis_strength_rating": 0.7
        }"""

        output = challenger._parse_output(raw_output)

        assert isinstance(output, ChallengerOutput)
        assert len(output.challenges) == 1
        assert output.challenges[0].challenge_type == "alternative_explanation"
        assert output.analysis_strength_rating == 0.7


class TestAdvocateAgent:
    """Tests for AdvocateAgent."""

    @pytest.fixture
    def mock_router(self) -> MagicMock:
        """Create mock router."""
        router = MagicMock()
        router.complete = AsyncMock()
        return router

    @pytest.fixture
    def advocate(self, mock_router: MagicMock) -> AdvocateAgent:
        """Create advocate with mock router."""
        return AdvocateAgent(mock_router)

    def test_task_name(self, advocate: AdvocateAgent) -> None:
        """Test task name is correct."""
        assert advocate.task_name == "advocate"

    def test_build_messages(self, advocate: AdvocateAgent) -> None:
        """Test message building."""
        challenge = DebateChallenge(
            challenge_id="c1",
            challenge_type="alternative_explanation",
            target_claim="Primary motivation was domestic",
            challenge_text="External factors may have been more important than domestic considerations in this decision.",
            severity="medium",
        )

        input_data = AdvocateInput(
            original_analysis="The leader acted to shore up domestic support.",
            challenge=challenge,
        )

        messages = advocate._build_messages(input_data)

        assert len(messages) == 2
        assert "alternative_explanation" in messages[1]["content"]

    @pytest.mark.asyncio
    async def test_parse_output(self, advocate: AdvocateAgent) -> None:
        """Test output parsing."""
        raw_output = """{
            "response": {
                "challenge_id": "c1",
                "response_type": "partial_concede",
                "response_text": "The challenge has merit in noting external factors, but domestic considerations remain primary based on the timeline of events and public statements.",
                "evidence_provided": ["Pre-election polling data", "Leader's campaign speeches"],
                "suggested_modification": "Add paragraph acknowledging external pressure while maintaining domestic as primary driver"
            },
            "defense_strength": 0.7
        }"""

        output = advocate._parse_output(raw_output)

        assert isinstance(output, AdvocateOutput)
        assert output.response.response_type == "partial_concede"
        assert output.defense_strength == 0.7


class TestJudgeAgent:
    """Tests for JudgeAgent."""

    @pytest.fixture
    def mock_router(self) -> MagicMock:
        """Create mock router."""
        router = MagicMock()
        router.complete = AsyncMock()
        return router

    @pytest.fixture
    def judge(self, mock_router: MagicMock) -> JudgeAgent:
        """Create judge with mock router."""
        return JudgeAgent(mock_router)

    def test_task_name(self, judge: JudgeAgent) -> None:
        """Test task name is correct."""
        assert judge.task_name == "judge"

    def test_build_messages(self, judge: JudgeAgent) -> None:
        """Test message building."""
        challenge = DebateChallenge(
            challenge_id="c1",
            challenge_type="alternative_explanation",
            target_claim="Primary motivation was domestic",
            challenge_text="External factors may have been more important.",
            severity="medium",
        )

        response = AdvocateResponse(
            challenge_id="c1",
            response_type="partial_concede",
            response_text="The challenge has merit but domestic remains primary.",
        )

        input_data = JudgeInput(
            original_claim="Primary motivation was domestic",
            challenge=challenge,
            response=response,
        )

        messages = judge._build_messages(input_data)

        assert len(messages) == 2
        assert "THE DISPUTE" in messages[1]["content"]

    @pytest.mark.asyncio
    async def test_parse_output(self, judge: JudgeAgent) -> None:
        """Test output parsing."""
        raw_output = """{
            "ruling": {
                "challenge_id": "c1",
                "ruling": "partial_sustain",
                "reasoning": "Both sides present valid points. External factors warrant mention but the domestic interpretation remains supported by evidence.",
                "required_action": "minor_revision",
                "action_details": "Add brief acknowledgment of external factors without changing primary conclusion"
            },
            "confidence_in_ruling": 0.8
        }"""

        output = judge._parse_output(raw_output)

        assert isinstance(output, JudgeOutput)
        assert output.ruling.ruling == "partial_sustain"
        assert output.ruling.required_action == "minor_revision"
        assert output.confidence_in_ruling == 0.8

