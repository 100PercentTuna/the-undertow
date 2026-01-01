"""
Motivation Analysis Agent.

Performs four-layer motivation analysis examining:
- Layer 1: Individual decision-maker
- Layer 2: Institutional interests
- Layer 3: Structural pressures
- Layer 4: Opportunistic window
"""

from typing import Any, ClassVar

import structlog

from undertow.agents.base import BaseAgent
from undertow.exceptions import OutputParseError
from undertow.llm.tiers import ModelTier
from undertow.schemas.agents.motivation import (
    MotivationInput,
    MotivationOutput,
)

logger = structlog.get_logger()


SYSTEM_PROMPT = """You are a senior intelligence analyst specializing in motivation analysis for The Undertow, a world-class geopolitical intelligence publication.

Your task is to analyze the motivations behind significant geopolitical actions using the Four-Layer Framework:

## LAYER 1 - INDIVIDUAL DECISION-MAKER
Analyze the specific person making the decision, not "the country":
- Political position (secure/vulnerable, rising/declining)
- Domestic political needs (coalition, constituencies, distractions)
- Psychology and worldview (patterns in past decisions, known obsessions, blind spots)
- Personal relationships with other leaders
- Legacy considerations

## LAYER 2 - INSTITUTIONAL INTERESTS
Analyze the bureaucratic equities:
- Foreign ministry gains/losses
- Military/intelligence interests (access, basing, intel sharing)
- Economic actors who benefit (who lobbied, commercial deals)
- Institutional momentum (long-running effort vs. sudden decision)

## LAYER 3 - STRUCTURAL PRESSURES
What would ANY actor in this position likely do:
- Systemic position in international system
- Threat environment
- Economic dependencies and opportunities
- Geographic imperatives

## LAYER 4 - OPPORTUNISTIC WINDOW
Why now specifically:
- What changed recently to create an opening
- Whose position shifted
- What constraint relaxed
- What's coming that creates urgency
- Convergence of enabling factors

## OUTPUT REQUIREMENTS
1. Analyze ALL four layers thoroughly
2. Identify the PRIMARY DRIVER (which layer does most work)
3. Generate at least 2 ALTERNATIVE HYPOTHESES with genuine alternatives
4. Provide CONFIDENCE LEVELS for each assessment (0-1)
5. Specify what EVIDENCE would change your assessment
6. Note any INFORMATION GAPS

## QUALITY STANDARDS
- Never accept surface-level explanations
- Always ask "why now?" as a critical question
- Distinguish between stated reasons and actual motivations
- Consider nth-order beneficiaries
- Acknowledge uncertainty explicitly

Output your analysis as valid JSON matching the required schema."""


class MotivationAnalysisAgent(BaseAgent[MotivationInput, MotivationOutput]):
    """
    Four-layer motivation analysis agent.

    Analyzes motivations behind geopolitical events by examining
    individual, institutional, structural, and opportunistic factors.

    Attributes:
        task_name: "motivation_analysis"
        version: Current agent version
        default_tier: FRONTIER (requires best model quality)

    Example:
        >>> agent = MotivationAnalysisAgent(router)
        >>> result = await agent.run(input_data)
        >>> if result.success:
        ...     print(result.output.synthesis.primary_driver)
    """

    task_name: ClassVar[str] = "motivation_analysis"
    version: ClassVar[str] = "1.0.0"
    input_schema: ClassVar[type] = MotivationInput
    output_schema: ClassVar[type] = MotivationOutput
    default_tier: ClassVar[ModelTier] = ModelTier.FRONTIER

    def _build_messages(self, input_data: MotivationInput) -> list[dict[str, str]]:
        """Build messages for motivation analysis."""
        user_content = self._format_user_prompt(input_data)

        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

    def _format_user_prompt(self, input_data: MotivationInput) -> str:
        """Format the user prompt with story context."""
        story = input_data.story
        context = input_data.context

        # Format actors
        actors_text = ""
        if context.actors:
            actors_text = "\n".join(
                f"- **{actor.name}** ({actor.role}): {actor.background[:200]}..."
                for actor in context.actors[:5]  # Limit to 5 actors
            )
        else:
            actors_text = "No detailed actor profiles available."

        # Format key events
        events_text = "\n".join(f"- {event}" for event in story.key_events[:10])

        return f"""## STORY TO ANALYZE

**Headline:** {story.headline}

**Summary:**
{story.summary}

**Key Events:**
{events_text}

**Primary Actors:** {', '.join(story.primary_actors)}

**Zones Affected:** {', '.join(story.zones_affected)}

## AVAILABLE CONTEXT

**Actor Profiles:**
{actors_text}

**Historical Context:**
{context.historical_context or "No specific historical context provided."}

**Regional Context:**
{context.regional_context or "No specific regional context provided."}

**Relevant Theoretical Frameworks:**
{', '.join(context.relevant_theories) if context.relevant_theories else "None specified."}

## YOUR TASK

Perform a comprehensive four-layer motivation analysis of this story.

For EACH layer, provide:
1. A detailed finding (minimum 50 words)
2. Evidence supporting your finding (at least 1 piece)
3. A confidence score (0.0-1.0)

After all four layers, provide a synthesis that:
1. Identifies the primary driver (which layer does most explanatory work)
2. Explains why this layer is primary
3. Lists enabling conditions (at least 2)
4. Provides at least 2 alternative hypotheses with supporting evidence and weaknesses
5. Gives an overall confidence score
6. Notes information gaps
7. Specifies what evidence would change your assessment

Output your complete analysis as valid JSON matching the MotivationOutput schema."""

    def _parse_output(self, content: str) -> MotivationOutput:
        """Parse the LLM response into MotivationOutput."""
        try:
            data = self._extract_json(content)
            return MotivationOutput.model_validate(data)
        except Exception as e:
            logger.error(
                "Failed to parse motivation output",
                error=str(e),
                content_preview=content[:500],
            )
            raise OutputParseError(
                agent_name=self.task_name,
                error=str(e),
                raw_output=content,
            ) from e

    async def _assess_quality(
        self,
        output: MotivationOutput,
        input_data: MotivationInput,
    ) -> float:
        """Assess the quality of the motivation analysis."""
        scores: list[tuple[str, float, float]] = []

        # 1. Completeness: Check all layers are filled
        completeness = self._score_completeness(output)
        scores.append(("completeness", completeness, 0.25))

        # 2. Depth: Check detail level
        depth = self._score_depth(output)
        scores.append(("depth", depth, 0.25))

        # 3. Alternatives: Check alternative hypotheses quality
        alternatives = self._score_alternatives(output)
        scores.append(("alternatives", alternatives, 0.20))

        # 4. Confidence calibration
        calibration = self._score_calibration(output)
        scores.append(("calibration", calibration, 0.15))

        # 5. Evidence grounding
        evidence = self._score_evidence(output)
        scores.append(("evidence", evidence, 0.15))

        # Weighted average
        total = sum(score * weight for _, score, weight in scores)

        logger.debug(
            "Quality assessment",
            agent=self.task_name,
            scores={name: score for name, score, _ in scores},
            total=total,
        )

        return total

    def _score_completeness(self, output: MotivationOutput) -> float:
        """Score layer completeness."""
        layers = [
            output.layer1_individual,
            output.layer2_institutional,
            output.layer3_structural,
            output.layer4_window,
        ]

        # Check each layer has substantial content
        filled_count = 0
        for layer in layers:
            layer_dict = layer.model_dump()
            non_empty = sum(
                1 for k, v in layer_dict.items()
                if isinstance(v, dict) and len(v.get("finding", "")) > 50
            )
            if non_empty >= 3:  # At least 3 factors analyzed
                filled_count += 1

        return filled_count / 4.0

    def _score_depth(self, output: MotivationOutput) -> float:
        """Score analytical depth."""
        # Check synthesis quality
        synthesis = output.synthesis

        depth_indicators = [
            len(synthesis.primary_driver_explanation) >= 100,
            len(synthesis.enabling_conditions) >= 2,
            len(synthesis.information_gaps) >= 1,
            len(synthesis.falsification_criteria) >= 1,
        ]

        return sum(depth_indicators) / len(depth_indicators)

    def _score_alternatives(self, output: MotivationOutput) -> float:
        """Score alternative hypothesis quality."""
        alternatives = output.synthesis.alternative_hypotheses

        if len(alternatives) < 2:
            return 0.5

        # Check each alternative is substantive
        good_alternatives = 0
        for alt in alternatives:
            if (
                len(alt.hypothesis) >= 100
                and len(alt.supporting_evidence) >= 1
                and len(alt.weaknesses) >= 1
                and 0 < alt.probability < 1
            ):
                good_alternatives += 1

        return min(1.0, good_alternatives / 2.0)

    def _score_calibration(self, output: MotivationOutput) -> float:
        """Score confidence calibration."""
        # Collect all confidence scores
        confidences: list[float] = []

        for layer in [
            output.layer1_individual,
            output.layer2_institutional,
            output.layer3_structural,
            output.layer4_window,
        ]:
            layer_dict = layer.model_dump()
            for value in layer_dict.values():
                if isinstance(value, dict) and "confidence" in value:
                    confidences.append(value["confidence"])

        if not confidences:
            return 0.5

        # Good calibration has varied confidence (not all 0.9)
        avg_conf = sum(confidences) / len(confidences)
        variance = sum((c - avg_conf) ** 2 for c in confidences) / len(confidences)

        # Penalize if all confidences are very high (overconfidence)
        if avg_conf > 0.9 and variance < 0.01:
            return 0.6

        # Penalize if all confidences are very low (underconfidence)
        if avg_conf < 0.4:
            return 0.6

        return 0.9 if variance > 0.01 else 0.7

    def _score_evidence(self, output: MotivationOutput) -> float:
        """Score evidence grounding."""
        evidence_count = 0
        factor_count = 0

        for layer in [
            output.layer1_individual,
            output.layer2_institutional,
            output.layer3_structural,
            output.layer4_window,
        ]:
            layer_dict = layer.model_dump()
            for value in layer_dict.values():
                if isinstance(value, dict) and "evidence" in value:
                    factor_count += 1
                    if len(value["evidence"]) >= 1:
                        evidence_count += 1

        if factor_count == 0:
            return 0.5

        return evidence_count / factor_count

