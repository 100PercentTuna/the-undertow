"""
Uncertainty Analysis Agent.

Explicit uncertainty quantification and confidence calibration.
Ensures epistemic humility in all analysis.
"""

from typing import ClassVar

import structlog

from undertow.agents.base import BaseAgent
from undertow.exceptions import OutputParseError
from undertow.llm.tiers import ModelTier
from undertow.schemas.agents.uncertainty import UncertaintyInput, UncertaintyOutput

logger = structlog.get_logger()


UNCERTAINTY_SYSTEM_PROMPT = """You are the Uncertainty Analysis agent for The Undertow.

Your role is to ensure EPISTEMIC HUMILITY - we must be honest about what we
know, what we don't know, and how confident we should be.

## KNOWLEDGE CLASSIFICATION

Every claim falls into one of four categories:

1. **known_fact**: Verified facts from multiple independent sources
   - "The treaty was signed on [date]" (documented)
   - Confidence: 0.90-1.00

2. **assessed_inference**: Inferences from evidence, stated as inferences
   - "This suggests the motivation was..." (reasoned from evidence)
   - Confidence: 0.60-0.85

3. **informed_speculation**: Educated guesses about hidden factors
   - "One possibility is..." (plausible but uncertain)
   - Confidence: 0.30-0.60

4. **acknowledged_unknown**: Gaps honestly admitted
   - "We don't know whether..." (explicit uncertainty)
   - Confidence: N/A

## DISAGREEMENT HANDLING

When credible analysts disagree:
- Show the disagreement rather than pretending consensus
- Present both/all positions fairly
- Explain our view on the disagreement
- Identify what evidence would resolve it

## INFORMATION GAPS

Be specific about what we don't know:
- What information is missing?
- Why does this gap matter?
- How important is the gap for our conclusions?
- How might we fill it?

## FALSIFICATION CRITERIA

For each key assessment, identify:
- What evidence would prove it wrong?
- How likely is such evidence to emerge?
- What should we watch for?

## CONFIDENCE CALIBRATION

Confidence should reflect:
- Evidence quality and quantity
- Source reliability
- Logical certainty of inferences
- Historical base rates for similar assessments

Overconfidence is as bad as underconfidence. Aim for calibration.

## OUTPUT REQUIREMENTS

1. Classify all key claims into knowledge categories
2. Note any analyst disagreements
3. Identify information gaps
4. Provide falsification criteria
5. List confidence drivers
6. Synthesize overall uncertainty picture

Output as valid JSON matching UncertaintyOutput schema."""


class UncertaintyAnalysisAgent(BaseAgent[UncertaintyInput, UncertaintyOutput]):
    """
    Uncertainty Analysis agent - ensures epistemic humility.

    Uses HIGH tier for careful calibration.
    """

    task_name: ClassVar[str] = "uncertainty_analysis"
    version: ClassVar[str] = "1.0.0"
    input_schema: ClassVar[type] = UncertaintyInput
    output_schema: ClassVar[type] = UncertaintyOutput
    default_tier: ClassVar[ModelTier] = ModelTier.HIGH

    def _build_messages(self, input_data: UncertaintyInput) -> list[dict[str, str]]:
        """Build messages for uncertainty analysis."""
        claims_text = "\n".join(f"- {c}" for c in input_data.key_claims)

        user_content = f"""## ANALYSIS TO ASSESS

{input_data.analysis_content}

## KEY CLAIMS

{claims_text}

## STATED CONFIDENCE

Current stated confidence: {input_data.stated_confidence}

## YOUR TASK

1. Classify each claim (known_fact, assessed_inference, informed_speculation, acknowledged_unknown)
2. Identify disagreement points among analysts
3. Note information gaps
4. Provide falsification criteria for key assessments
5. List what drives confidence up or down
6. Synthesize the overall uncertainty picture

Be rigorous. Overconfidence is dangerous in geopolitical analysis.

Output as valid JSON matching UncertaintyOutput schema."""

        return [
            {"role": "system", "content": UNCERTAINTY_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

    def _parse_output(self, content: str) -> UncertaintyOutput:
        """Parse uncertainty analysis output."""
        try:
            data = self._extract_json(content)
            return UncertaintyOutput.model_validate(data)
        except Exception as e:
            logger.error("Failed to parse uncertainty output", error=str(e))
            raise OutputParseError(
                agent_name=self.task_name,
                error=str(e),
                raw_output=content,
            ) from e

    async def _assess_quality(
        self,
        output: UncertaintyOutput,
        input_data: UncertaintyInput,
    ) -> float:
        """Assess quality of uncertainty analysis."""
        scores: list[float] = []

        # Did we classify all claims?
        if len(output.knowledge_classifications) >= len(input_data.key_claims):
            scores.append(1.0)
        else:
            ratio = len(output.knowledge_classifications) / max(len(input_data.key_claims), 1)
            scores.append(ratio)

        # Did we identify information gaps?
        if output.information_gaps:
            scores.append(1.0)
        else:
            scores.append(0.5)

        # Did we provide falsification criteria?
        if output.falsification_criteria:
            scores.append(1.0)
        else:
            scores.append(0.5)

        # Is synthesis substantive?
        if len(output.synthesis.primary_uncertainty_source) >= 50:
            scores.append(1.0)
        else:
            scores.append(0.6)

        # Did we identify what we know well and don't know?
        if output.synthesis.what_we_know_well and output.synthesis.what_we_dont_know:
            scores.append(1.0)
        else:
            scores.append(0.5)

        return sum(scores) / len(scores)

