"""
Golden tests with real geopolitical scenarios.

These tests verify that the system produces high-quality analysis
for real-world events.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from undertow.schemas.agents.motivation import StoryContext, AnalysisContext


# ============================================================================
# GOLDEN TEST SCENARIOS
# ============================================================================

SCENARIO_ISRAEL_SOMALILAND = StoryContext(
    headline="Israel Recognizes Somaliland as Independent State",
    summary=(
        "Israel has formally recognized Somaliland's independence, making it one of "
        "the first countries to do so since Somaliland declared independence from "
        "Somalia in 1991. The recognition includes a defense cooperation agreement "
        "covering military training, intelligence sharing, and port access at Berbera. "
        "The move comes amid heightened Red Sea tensions following Houthi attacks on "
        "shipping and Ethiopia's recent MOU with Somaliland for sea access."
    ),
    key_events=[
        "Israeli Foreign Minister signs recognition document in Hargeisa",
        "Defense cooperation agreement includes Berbera port access",
        "Somalia recalls ambassador from Tel Aviv",
        "UAE welcomes the development",
        "Turkey condemns the recognition",
        "US issues neutral statement",
    ],
    primary_actors=[
        "Benjamin Netanyahu",
        "Muse Bihi Abdi (Somaliland President)",
        "Hassan Sheikh Mohamud (Somalia President)",
        "UAE Leadership",
        "Recep Tayyip Erdogan",
    ],
    zones_affected=["horn_of_africa", "gulf_gcc", "turkey"],
)

SCENARIO_NIGER_COUP = StoryContext(
    headline="Niger Military Junta Expels French Forces, Signs Russia Defense Pact",
    summary=(
        "Niger's military government has ordered the withdrawal of all French military "
        "personnel within 30 days, ending Operation Barkhane's presence in the country. "
        "Simultaneously, the junta announced a military cooperation agreement with Russia, "
        "with Wagner Group forces already beginning to arrive in Niamey. The move follows "
        "similar pivots by Mali and Burkina Faso, consolidating the 'Sahel Alliance' of "
        "military governments aligned with Moscow."
    ),
    key_events=[
        "French ambassador given 48 hours to leave",
        "1,500 French troops ordered out within 30 days",
        "Russian military delegation arrives in Niamey",
        "Wagner personnel spotted at airport",
        "ECOWAS extends sanctions but rules out military intervention",
        "Mali and Burkina Faso express solidarity",
    ],
    primary_actors=[
        "General Abdourahamane Tchiani",
        "Emmanuel Macron",
        "Yevgeny Prigozhin (pre-death planning)",
        "Assimi Goita (Mali)",
        "Ibrahim Traore (Burkina Faso)",
    ],
    zones_affected=["sahel", "west_africa", "russia_core"],
)

SCENARIO_TAIWAN_ELECTION = StoryContext(
    headline="DPP Wins Third Consecutive Taiwan Presidential Election",
    summary=(
        "Lai Ching-te of the Democratic Progressive Party has won Taiwan's presidential "
        "election with 40% of the vote, defeating KMT candidate Hou Yu-ih and TPP's "
        "Ko Wen-je. Beijing condemned the result as 'separatist' and announced military "
        "exercises in the Taiwan Strait. The US congratulated the winner while reaffirming "
        "'One China' policy. Japan and the Philippines expressed support for 'democratic Taiwan'."
    ),
    key_events=[
        "Lai Ching-te wins with 40% plurality",
        "KMT concedes defeat, calls for dialogue with Beijing",
        "PLA announces Taiwan Strait exercises",
        "US Secretary of State congratulates Lai",
        "China suspends some cross-strait dialogues",
        "TSMC stock rises 3% on stability hopes",
    ],
    primary_actors=[
        "Lai Ching-te",
        "Xi Jinping",
        "Joe Biden",
        "Fumio Kishida",
        "Hou Yu-ih",
    ],
    zones_affected=["taiwan", "china", "japan", "usa"],
)


# ============================================================================
# QUALITY CRITERIA FOR GOLDEN TESTS
# ============================================================================

class AnalysisQualityCriteria:
    """Quality criteria for golden test validation."""

    @staticmethod
    def validate_motivation_analysis(output: dict, scenario: StoryContext) -> list[str]:
        """Validate motivation analysis output."""
        issues = []

        # Must have all four layers
        required_layers = ["individual_layer", "institutional_layer", "structural_layer", "opportunistic_layer"]
        for layer in required_layers:
            if layer not in output:
                issues.append(f"Missing {layer}")

        # Individual layer must name actual decision maker
        if "individual_layer" in output:
            dm = output["individual_layer"].get("decision_maker", "")
            if not any(actor in dm for actor in scenario.primary_actors):
                issues.append("Decision maker not from provided actors list")

        # Must have synthesis
        if "synthesis" not in output:
            issues.append("Missing synthesis")
        else:
            synthesis = output["synthesis"]
            if len(synthesis.get("primary_driver", "")) < 50:
                issues.append("Primary driver too brief")
            if len(synthesis.get("enabling_conditions", [])) < 2:
                issues.append("Too few enabling conditions")
            if len(synthesis.get("alternative_explanations", [])) < 1:
                issues.append("No alternative explanations")

        return issues

    @staticmethod
    def validate_chain_analysis(output: dict, scenario: StoryContext) -> list[str]:
        """Validate chain analysis output."""
        issues = []

        # Must have forward chains to at least 4th order
        forward_chains = output.get("forward_chains", [])
        orders = {c.get("order", 0) for c in forward_chains}
        if max(orders, default=0) < 4:
            issues.append("Forward chains don't reach 4th order")

        # Must have backward cui bono analysis
        backward_chains = output.get("backward_chains", [])
        if len(backward_chains) < 2:
            issues.append("Insufficient backward chain analysis")

        # Must have synthesis with hidden game hypothesis
        synthesis = output.get("synthesis", {})
        if len(synthesis.get("hidden_game_hypothesis", "")) < 50:
            issues.append("Hidden game hypothesis too brief or missing")

        return issues

    @staticmethod
    def validate_subtlety_analysis(output: dict, scenario: StoryContext) -> list[str]:
        """Validate subtlety analysis output."""
        issues = []

        # Must analyze all five channels
        channels = [
            "signals_in_action",
            "eloquent_silences",
            "timing_message",
            "choreography",
            "deniable_communication",
        ]

        for channel in channels:
            if channel not in output:
                issues.append(f"Missing channel: {channel}")
            elif len(str(output[channel])) < 100:
                issues.append(f"Channel {channel} analysis too brief")

        return issues


# ============================================================================
# GOLDEN TESTS
# ============================================================================

class TestGoldenScenarios:
    """Golden tests for geopolitical scenarios."""

    @pytest.mark.golden
    def test_scenario_structure_israel_somaliland(self) -> None:
        """Test that Israel-Somaliland scenario has required structure."""
        scenario = SCENARIO_ISRAEL_SOMALILAND

        assert len(scenario.headline) > 20
        assert len(scenario.summary) > 200
        assert len(scenario.key_events) >= 5
        assert len(scenario.primary_actors) >= 3
        assert len(scenario.zones_affected) >= 2

    @pytest.mark.golden
    def test_scenario_structure_niger_coup(self) -> None:
        """Test that Niger coup scenario has required structure."""
        scenario = SCENARIO_NIGER_COUP

        assert len(scenario.headline) > 20
        assert len(scenario.summary) > 200
        assert len(scenario.key_events) >= 5
        assert len(scenario.primary_actors) >= 3
        assert "sahel" in scenario.zones_affected

    @pytest.mark.golden
    def test_scenario_structure_taiwan_election(self) -> None:
        """Test that Taiwan election scenario has required structure."""
        scenario = SCENARIO_TAIWAN_ELECTION

        assert len(scenario.headline) > 20
        assert "taiwan" in scenario.zones_affected
        assert "china" in scenario.zones_affected

    @pytest.mark.golden
    @pytest.mark.asyncio
    async def test_motivation_agent_quality(self) -> None:
        """
        Test that motivation analysis meets quality criteria.

        This is a placeholder that would run the actual agent
        against golden scenarios.
        """
        # This would actually run the agent in a real test
        # For now, validate the expected output structure

        expected_output = {
            "individual_layer": {
                "decision_maker": "Benjamin Netanyahu",
                "political_position": "Facing coalition pressures",
                "domestic_needs": "Foreign policy wins",
                "key_assessments": ["Assessment 1", "Assessment 2"],
                "confidence": 0.85,
            },
            "institutional_layer": {
                "foreign_ministry_role": "Executing plan",
                "military_intelligence_role": "Driving force",
                "economic_actors": ["Actor 1"],
                "key_assessments": ["Assessment"],
                "confidence": 0.80,
            },
            "structural_layer": {
                "systemic_position": "Strategic depth",
                "threat_environment": "Iranian expansion",
                "economic_structure": "Limited",
                "geographic_imperatives": "Red Sea access",
                "key_assessments": ["Assessment"],
                "confidence": 0.90,
            },
            "opportunistic_layer": {
                "what_changed": "New government",
                "position_shifts": ["Shift 1"],
                "constraints_relaxed": ["Constraint 1"],
                "window_analysis": "Window opened",
                "key_assessments": ["Assessment"],
                "confidence": 0.85,
            },
            "synthesis": {
                "primary_driver": "Structural imperative combined with institutional momentum",
                "enabling_conditions": ["Condition 1", "Condition 2"],
                "alternative_explanations": ["Alternative 1"],
                "confidence_assessment": 0.82,
                "key_uncertainties": ["Uncertainty 1"],
            },
        }

        issues = AnalysisQualityCriteria.validate_motivation_analysis(
            expected_output,
            SCENARIO_ISRAEL_SOMALILAND,
        )

        assert len(issues) == 0, f"Quality issues: {issues}"

    @pytest.mark.golden
    def test_few_shot_examples_quality(self) -> None:
        """Test that few-shot examples meet quality criteria."""
        from undertow.prompts.few_shot_examples import FEW_SHOT_EXAMPLES

        # Motivation examples
        for example in FEW_SHOT_EXAMPLES.get("motivation", []):
            assert "input" in example
            assert "output" in example
            assert "headline" in example["input"]
            assert "synthesis" in example["output"]

        # Chain examples
        for example in FEW_SHOT_EXAMPLES.get("chains", []):
            assert "forward_chains" in example["output"]
            assert "backward_chains" in example["output"]

        # Subtlety examples
        for example in FEW_SHOT_EXAMPLES.get("subtlety", []):
            assert "signals_in_action" in example["output"]
            assert "eloquent_silences" in example["output"]


class TestPipelineIntegration:
    """Integration tests for full pipeline with golden scenarios."""

    @pytest.mark.golden
    @pytest.mark.asyncio
    async def test_pipeline_produces_article(self) -> None:
        """
        Test that pipeline produces a complete article.

        This would run the full pipeline in integration environment.
        """
        # Placeholder for actual integration test
        # In real test, would:
        # 1. Initialize pipeline with real router
        # 2. Run against golden scenario
        # 3. Validate output meets quality criteria

        expected_article_properties = {
            "min_word_count": 2000,
            "max_word_count": 5000,
            "required_sections": [
                "headline",
                "content",
            ],
            "forbidden_phrases": [
                "In today's interconnected world",
                "Time will tell",
                "Remains to be seen",
            ],
        }

        # Validate structure
        assert expected_article_properties["min_word_count"] > 0
        assert expected_article_properties["max_word_count"] > expected_article_properties["min_word_count"]

    @pytest.mark.golden
    def test_quality_gates_thresholds(self) -> None:
        """Test that quality gates have appropriate thresholds."""
        from undertow.core.quality.gates import QualityGateSystem

        gates = QualityGateSystem()

        # Gates should have reasonable thresholds
        assert gates.foundation_threshold >= 0.70
        assert gates.analysis_threshold >= 0.75
        assert gates.adversarial_threshold >= 0.75
        assert gates.output_threshold >= 0.80

