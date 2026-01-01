"""
Synthesis Agent.

Combines all analysis layers into a coherent whole.
This is the final analytical step before writing.
"""

from typing import ClassVar

import structlog

from undertow.agents.base import BaseAgent
from undertow.exceptions import OutputParseError
from undertow.llm.tiers import ModelTier
from undertow.schemas.agents.synthesis import SynthesisInput, SynthesisOutput

logger = structlog.get_logger()


SYNTHESIS_SYSTEM_PROMPT = """You are the Synthesis Agent for The Undertow.

Your role is to COMBINE all analysis layers into a coherent, insightful whole.
You receive outputs from multiple specialized agents and must weave them together.

## YOUR INPUTS

You will receive analyses from:
1. **Motivation Analysis**: Four-layer motivation (individual, institutional, structural, opportunistic)
2. **Chains Analysis**: Forward/backward consequence chains
3. **Subtlety Analysis**: Diplomatic signaling, silences, timing
4. **Geometry Analysis**: Strategic geography
5. **Deep Context Analysis**: Historical grievances, elite networks, strategic culture
6. **Connections Analysis**: Non-obvious links, strange bedfellows
7. **Uncertainty Analysis**: What we know vs. don't know

## YOUR TASK

1. **Executive Summary**: 2-3 paragraphs capturing the essential story
2. **Key Findings**: The most important insights, with sources
3. **Narrative Threads**: How different analyses connect
4. **Contradictions**: Any tensions between analyses and how to resolve them
5. **The Real Story**: What game is actually being played?
6. **Reader Takeaways**: What should readers remember?
7. **Monitoring Recommendations**: What to watch going forward

## SYNTHESIS PRINCIPLES

- **Integration over Aggregation**: Don't just list findings; weave them together
- **Hierarchy of Importance**: Some findings matter more than others
- **Resolve Tensions**: When analyses conflict, explain how
- **The "So What"**: Always answer why this matters
- **Calibrated Confidence**: Reflect appropriate uncertainty

## VOICE

The synthesis should read like the conclusion of a brilliant briefing:
- Confident but not arrogant
- Dense with insight
- Clear about uncertainty
- Memorable

## OUTPUT REQUIREMENTS

Produce a synthesis that:
1. Could stand alone as a briefing
2. Integrates (not just lists) findings from all analyses
3. Answers "what's really going on?"
4. Tells readers what to watch
5. Is appropriately uncertain

Output as valid JSON matching SynthesisOutput schema."""


class SynthesisAgent(BaseAgent[SynthesisInput, SynthesisOutput]):
    """
    Synthesis agent - combines all analyses into coherent whole.

    Uses FRONTIER tier for highest quality synthesis.
    """

    task_name: ClassVar[str] = "synthesis"
    version: ClassVar[str] = "1.0.0"
    input_schema: ClassVar[type] = SynthesisInput
    output_schema: ClassVar[type] = SynthesisOutput
    default_tier: ClassVar[ModelTier] = ModelTier.FRONTIER

    def _build_messages(self, input_data: SynthesisInput) -> list[dict[str, str]]:
        """Build messages for synthesis."""
        analyses = []

        if input_data.motivation_analysis:
            analyses.append(f"## MOTIVATION ANALYSIS\n{input_data.motivation_analysis}")

        if input_data.chains_analysis:
            analyses.append(f"## CHAINS ANALYSIS\n{input_data.chains_analysis}")

        if input_data.subtlety_analysis:
            analyses.append(f"## SUBTLETY ANALYSIS\n{input_data.subtlety_analysis}")

        if input_data.geometry_analysis:
            analyses.append(f"## GEOMETRY ANALYSIS\n{input_data.geometry_analysis}")

        if input_data.deep_context_analysis:
            analyses.append(f"## DEEP CONTEXT ANALYSIS\n{input_data.deep_context_analysis}")

        if input_data.connections_analysis:
            analyses.append(f"## CONNECTIONS ANALYSIS\n{input_data.connections_analysis}")

        if input_data.uncertainty_analysis:
            analyses.append(f"## UNCERTAINTY ANALYSIS\n{input_data.uncertainty_analysis}")

        analyses_text = "\n\n".join(analyses) if analyses else "No analyses provided."

        user_content = f"""## STORY

**Headline**: {input_data.story_headline}

**Summary**: {input_data.story_summary}

## ANALYSES TO SYNTHESIZE

{analyses_text}

## YOUR TASK

Synthesize these analyses into a coherent whole:
1. Write an executive summary (2-3 paragraphs)
2. Identify the key findings with sources and confidence
3. Find narrative threads connecting the analyses
4. Resolve any contradictions
5. State what's really going on (the game being played)
6. Provide reader takeaways
7. Recommend what to monitor

Target word count: {input_data.target_word_count}

Output as valid JSON matching SynthesisOutput schema."""

        return [
            {"role": "system", "content": SYNTHESIS_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

    def _parse_output(self, content: str) -> SynthesisOutput:
        """Parse synthesis output."""
        try:
            data = self._extract_json(content)
            return SynthesisOutput.model_validate(data)
        except Exception as e:
            logger.error("Failed to parse synthesis output", error=str(e))
            raise OutputParseError(
                agent_name=self.task_name,
                error=str(e),
                raw_output=content,
            ) from e

    async def _assess_quality(
        self,
        output: SynthesisOutput,
        input_data: SynthesisInput,
    ) -> float:
        """Assess quality of synthesis."""
        scores: list[float] = []

        # Executive summary length
        if len(output.executive_summary) >= 300:
            scores.append(1.0)
        elif len(output.executive_summary) >= 200:
            scores.append(0.7)
        else:
            scores.append(0.4)

        # Key findings quality
        if len(output.key_findings) >= 3:
            scores.append(1.0)
            # Check if findings cite multiple sources
            multi_source = sum(
                1 for f in output.key_findings if len(f.sources) >= 2
            )
            scores.append(min(1.0, multi_source / 2))
        else:
            scores.append(0.5)

        # Narrative threads
        if len(output.narrative_threads) >= 2:
            scores.append(1.0)
        elif output.narrative_threads:
            scores.append(0.7)
        else:
            scores.append(0.4)

        # The real story depth
        if len(output.the_real_story) >= 150:
            scores.append(1.0)
        elif len(output.the_real_story) >= 100:
            scores.append(0.7)
        else:
            scores.append(0.5)

        # Monitoring recommendations
        if len(output.monitoring_recommendations) >= 2:
            scores.append(1.0)
        else:
            scores.append(0.6)

        return sum(scores) / len(scores)

