"""
Tests for Motivation Analysis Agent.
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from undertow.agents.analysis.motivation import MotivationAnalysisAgent
from undertow.llm.providers.base import LLMResponse
from undertow.llm.router import ModelRouter
from undertow.schemas.agents.motivation import (
    MotivationInput,
    StoryContext,
    AnalysisContext,
)


@pytest.fixture
def sample_motivation_output():
    """Create sample motivation analysis output."""
    return {
        "layer1_individual": {
            "political_position": {
                "finding": "The leader is in a vulnerable position facing upcoming elections "
                "and needs a foreign policy win to shore up domestic support.",
                "evidence": ["Recent polling shows declining approval", "Coalition partners restless"],
                "confidence": 0.8,
            },
            "domestic_needs": {
                "finding": "The action plays to nationalist constituency while distracting "
                "from economic problems at home.",
                "evidence": ["Economic indicators declining", "Nationalist base energized"],
                "confidence": 0.75,
            },
            "psychology_worldview": {
                "finding": "Pattern of bold moves when cornered, views world through lens "
                "of zero-sum competition.",
                "evidence": ["Previous similar decisions under pressure"],
                "confidence": 0.7,
            },
            "personal_relationships": {
                "finding": "Close relationship with counterpart leader developed over "
                "multiple summits creates trust foundation.",
                "evidence": ["Summit meetings", "Personal communications"],
                "confidence": 0.65,
            },
            "legacy_considerations": {
                "finding": "Leader sees this as defining achievement for historical legacy, "
                "positioning as transformational figure.",
                "evidence": ["Public statements about legacy", "Memoir focus"],
                "confidence": 0.7,
            },
        },
        "layer2_institutional": {
            "foreign_ministry": {
                "finding": "Foreign ministry was driving this for years, finally got "
                "political cover to move forward.",
                "evidence": ["Long diplomatic groundwork", "Ministry advocacy"],
                "confidence": 0.8,
            },
            "military_intelligence": {
                "finding": "Intelligence services gain new collection capabilities "
                "and military gets strategic positioning.",
                "evidence": ["Intelligence sharing agreements", "Military access deals"],
                "confidence": 0.75,
            },
            "economic_actors": {
                "finding": "Major corporate interests lobbied extensively for this "
                "opening to access new markets.",
                "evidence": ["Lobby registration", "Corporate statements"],
                "confidence": 0.7,
            },
            "institutional_momentum": {
                "finding": "This represents culmination of decade-long institutional "
                "effort rather than sudden political decision.",
                "evidence": ["Policy papers over time", "Working group history"],
                "confidence": 0.85,
            },
        },
        "layer3_structural": {
            "systemic_position": {
                "finding": "As a middle power seeking influence, actor needs to find "
                "niche advantages in great power competition.",
                "evidence": ["Regional dynamics", "Great power positioning"],
                "confidence": 0.75,
            },
            "threat_environment": {
                "finding": "Rising threat from regional adversary creates pressure "
                "to seek new alliances and partnerships.",
                "evidence": ["Threat assessments", "Military buildup data"],
                "confidence": 0.8,
            },
            "economic_structure": {
                "finding": "Export-dependent economy needs diversification away from "
                "traditional markets that are becoming unreliable.",
                "evidence": ["Trade statistics", "Economic vulnerability studies"],
                "confidence": 0.7,
            },
            "geographic_imperatives": {
                "finding": "Location at key chokepoint creates both opportunities and "
                "vulnerabilities that drive strategic behavior.",
                "evidence": ["Geographic analysis", "Historical patterns"],
                "confidence": 0.85,
            },
        },
        "layer4_window": {
            "what_changed": {
                "finding": "Recent shift in great power attention created window "
                "where action could proceed without interference.",
                "evidence": ["Great power distraction", "Policy vacuum"],
                "confidence": 0.75,
            },
            "position_shifts": {
                "finding": "Key regional player changed stance after leadership "
                "transition, removing previous obstacle.",
                "evidence": ["Leadership change", "New policy signals"],
                "confidence": 0.8,
            },
            "constraint_relaxation": {
                "finding": "Domestic opposition weakened after recent scandals, "
                "reducing political cost of action.",
                "evidence": ["Opposition polling", "Media coverage"],
                "confidence": 0.7,
            },
            "upcoming_events": {
                "finding": "Approaching international summit created deadline for "
                "having something to announce.",
                "evidence": ["Summit calendar", "Negotiation timing"],
                "confidence": 0.8,
            },
            "factor_convergence": {
                "finding": "Rare alignment of domestic politics, regional dynamics, "
                "and great power distraction opened window.",
                "evidence": ["Multiple factor analysis"],
                "confidence": 0.75,
            },
        },
        "synthesis": {
            "primary_driver": "layer2_institutional",
            "primary_driver_explanation": "This was primarily an institutional initiative that "
            "had been building for years, finally enabled by a political leader who saw "
            "personal advantage in letting it proceed. The institutional momentum was "
            "the necessary condition; the leader's political situation was the sufficient "
            "condition that determined timing.",
            "enabling_conditions": [
                "Political leader facing election pressure",
                "Great power distraction creating permissive environment",
                "Regional partner leadership change",
            ],
            "alternative_hypotheses": [
                {
                    "hypothesis": "This was primarily a great power proxy move, with the "
                    "regional actor acting on behalf of or with encouragement from major power, "
                    "rather than indigenous initiative.",
                    "supporting_evidence": [
                        "Major power benefits from outcome",
                        "Similar moves by major power allies",
                    ],
                    "weaknesses": [
                        "Long history predates current great power interest",
                        "Actor has shown independence in other matters",
                    ],
                    "probability": 0.25,
                },
                {
                    "hypothesis": "Leader is primarily motivated by legacy considerations and "
                    "personal history, with institutional factors secondary.",
                    "supporting_evidence": [
                        "Leader's public statements about legacy",
                        "Personal involvement in negotiations",
                    ],
                    "weaknesses": [
                        "Institution was pushing this long before leader arrived",
                        "Similar initiatives in other domains without personal involvement",
                    ],
                    "probability": 0.2,
                },
            ],
            "overall_confidence": 0.75,
            "information_gaps": [
                "Private communications between leaders",
                "Internal deliberations within foreign ministry",
                "Great power private signals or encouragement",
            ],
            "falsification_criteria": [
                "Evidence of great power direct involvement would raise alternative hypothesis",
                "Evidence institution opposed but leader pushed through would change assessment",
            ],
        },
    }


@pytest.fixture
def sample_input():
    """Create sample motivation input."""
    return MotivationInput(
        story=StoryContext(
            headline="Country A Announces Surprise Recognition of Territory B",
            summary="In a surprise move, Country A officially recognized Territory B's "
            "independence, breaking with decades of international consensus. The move "
            "has significant implications for regional stability and great power competition.",
            key_events=[
                "Official recognition announced",
                "Embassy opening planned",
                "Trade agreement signed",
            ],
            primary_actors=["Leader of Country A", "Government of Territory B"],
            zones_affected=["region_x", "region_y"],
        ),
        context=AnalysisContext(),
    )


class TestMotivationAnalysisAgent:
    """Tests for MotivationAnalysisAgent."""

    @pytest.mark.asyncio
    async def test_agent_configuration(self, mock_router):
        """Test agent is properly configured."""
        agent = MotivationAnalysisAgent(mock_router)

        assert agent.task_name == "motivation_analysis"
        assert agent.version == "1.0.0"
        assert agent.input_schema == MotivationInput

    @pytest.mark.asyncio
    async def test_build_messages(self, mock_router, sample_input):
        """Test message building."""
        agent = MotivationAnalysisAgent(mock_router)
        messages = agent._build_messages(sample_input)

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "Country A" in messages[1]["content"]

    @pytest.mark.asyncio
    async def test_parse_output(self, mock_router, sample_motivation_output):
        """Test output parsing."""
        agent = MotivationAnalysisAgent(mock_router)

        output = agent._parse_output(json.dumps(sample_motivation_output))

        assert output.synthesis.primary_driver == "layer2_institutional"
        assert output.synthesis.overall_confidence == 0.75
        assert len(output.synthesis.alternative_hypotheses) == 2

    @pytest.mark.asyncio
    async def test_quality_assessment(self, mock_router, sample_motivation_output):
        """Test quality assessment."""
        agent = MotivationAnalysisAgent(mock_router)

        # Parse to get proper output
        from undertow.schemas.agents.motivation import MotivationOutput

        output = MotivationOutput.model_validate(sample_motivation_output)
        sample_input = MotivationInput(
            story=StoryContext(
                headline="Test",
                summary="Test summary for testing purposes",
                key_events=["Event 1"],
                primary_actors=["Actor 1"],
                zones_affected=["zone1"],
            ),
            context=AnalysisContext(),
        )

        quality = await agent._assess_quality(output, sample_input)

        # Quality should be reasonable for this well-formed output
        assert 0.5 <= quality <= 1.0

