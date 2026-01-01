"""
Self-Critique Agent.

Performs internal critique of analysis before adversarial review.
Part of the multi-pass analysis with self-critique loop.
"""

from typing import ClassVar, Literal

import structlog
from pydantic import Field

from undertow.agents.base import BaseAgent
from undertow.exceptions import OutputParseError
from undertow.llm.tiers import ModelTier
from undertow.schemas.base import StrictModel

logger = structlog.get_logger()


class CritiquePoint(StrictModel):
    """A single critique point."""

    aspect: str = Field(..., description="What aspect is being critiqued")
    criticism: str = Field(
        ...,
        min_length=50,
        description="The critique",
    )
    severity: Literal["minor", "moderate", "significant", "critical"] = Field(...)
    suggested_improvement: str = Field(
        ...,
        min_length=20,
        description="How to address this",
    )
    confidence_impact: float = Field(
        ...,
        ge=-0.2,
        le=0,
        description="How much this should reduce confidence",
    )


class SelfCritiqueInput(StrictModel):
    """Input for Self-Critique agent."""

    analysis_type: Literal["motivation", "chains", "subtlety", "full"] = Field(
        ...,
        description="Type of analysis being critiqued",
    )
    analysis_content: str = Field(
        ...,
        min_length=200,
        description="The analysis to critique",
    )
    stated_confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description="Confidence stated in the analysis",
    )
    key_claims: list[str] = Field(
        default_factory=list,
        description="Key claims made in the analysis",
    )


class SelfCritiqueOutput(StrictModel):
    """Output from Self-Critique agent."""

    critique_points: list[CritiquePoint] = Field(
        default_factory=list,
        description="Identified issues",
    )
    strengths: list[str] = Field(
        default_factory=list,
        description="Strengths of the analysis",
    )
    recommended_confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description="Recommended confidence level",
    )
    confidence_delta: float = Field(
        ...,
        ge=-0.5,
        le=0.1,
        description="Change from stated confidence",
    )
    overall_assessment: str = Field(
        ...,
        min_length=100,
        description="Overall assessment of analysis quality",
    )
    revision_needed: bool = Field(
        ...,
        description="Whether revision is recommended",
    )
    revision_priority: list[str] = Field(
        default_factory=list,
        description="Priority items for revision",
    )


SELF_CRITIQUE_SYSTEM_PROMPT = """You are the Self-Critique module for The Undertow's analysis pipeline.

Your role is to critically examine analysis BEFORE it goes to adversarial review.
You must identify weaknesses that need addressing.

## CRITIQUE DIMENSIONS

1. **Logical Coherence**
   - Does the argument flow logically?
   - Are there gaps in reasoning?
   - Are conclusions supported by evidence?

2. **Evidence Quality**
   - Is evidence sufficient?
   - Are sources reliable?
   - Is evidence properly cited?

3. **Alternative Consideration**
   - Were alternatives adequately considered?
   - Is there premature closure on one explanation?
   - What counter-arguments weren't addressed?

4. **Confidence Calibration**
   - Is confidence level appropriate?
   - Are uncertainties acknowledged?
   - Is the language appropriately hedged?

5. **Completeness**
   - Are all relevant factors considered?
   - What's missing from the analysis?
   - Are there blind spots?

6. **Bias Detection**
   - Any systematic bias apparent?
   - Geographic/cultural assumptions?
   - Over-reliance on certain sources?

## SEVERITY LEVELS

- **minor**: Nitpicks, style issues
- **moderate**: Should be addressed but not critical
- **significant**: Weakens the analysis meaningfully
- **critical**: Fundamental flaw requiring revision

## CONFIDENCE ADJUSTMENT

Start with stated confidence. For each issue:
- Minor: -0.02
- Moderate: -0.05
- Significant: -0.1
- Critical: -0.15

Maximum total reduction: -0.3

## OUTPUT REQUIREMENTS

1. List specific critique points with improvements
2. Acknowledge strengths (be fair)
3. Calculate recommended confidence
4. Determine if revision is needed (if critical issues or >3 significant)
5. Prioritize revision items

Be thorough but fair. Good analysis survives self-critique.

Output as valid JSON matching SelfCritiqueOutput schema."""


class SelfCritiqueAgent(BaseAgent[SelfCritiqueInput, SelfCritiqueOutput]):
    """
    Self-Critique agent - internal quality review before adversarial.

    Uses HIGH tier for nuanced self-assessment.
    """

    task_name: ClassVar[str] = "self_critique"
    version: ClassVar[str] = "1.0.0"
    input_schema: ClassVar[type] = SelfCritiqueInput
    output_schema: ClassVar[type] = SelfCritiqueOutput
    default_tier: ClassVar[ModelTier] = ModelTier.HIGH

    def _build_messages(self, input_data: SelfCritiqueInput) -> list[dict[str, str]]:
        """Build messages for self-critique."""
        claims_text = ""
        if input_data.key_claims:
            claims_text = "\n\n## KEY CLAIMS\n" + "\n".join(
                f"- {c}" for c in input_data.key_claims
            )

        user_content = f"""## ANALYSIS TO CRITIQUE

**Type**: {input_data.analysis_type}
**Stated Confidence**: {input_data.stated_confidence}

### CONTENT

{input_data.analysis_content}
{claims_text}

## YOUR TASK

1. Identify weaknesses across all critique dimensions
2. Note strengths (be fair)
3. Calculate appropriate confidence adjustment
4. Determine if revision is needed
5. Prioritize what to fix

Be thorough and honest. The goal is to catch problems before adversarial review.

Output as valid JSON matching SelfCritiqueOutput schema."""

        return [
            {"role": "system", "content": SELF_CRITIQUE_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

    def _parse_output(self, content: str) -> SelfCritiqueOutput:
        """Parse self-critique output."""
        try:
            data = self._extract_json(content)
            return SelfCritiqueOutput.model_validate(data)
        except Exception as e:
            logger.error("Failed to parse self-critique output", error=str(e))
            raise OutputParseError(
                agent_name=self.task_name,
                error=str(e),
                raw_output=content,
            ) from e

    async def _assess_quality(
        self,
        output: SelfCritiqueOutput,
        input_data: SelfCritiqueInput,
    ) -> float:
        """Assess quality of self-critique."""
        scores: list[float] = []

        # Did we find issues? (thoroughness)
        if output.critique_points:
            scores.append(min(1.0, len(output.critique_points) / 3))
        else:
            scores.append(0.5)  # Suspicious if no issues found

        # Did we acknowledge strengths? (fairness)
        if output.strengths:
            scores.append(min(1.0, len(output.strengths) / 2))
        else:
            scores.append(0.5)

        # Is confidence delta reasonable?
        if -0.3 <= output.confidence_delta <= 0.1:
            scores.append(1.0)
        else:
            scores.append(0.5)

        # Is assessment substantive?
        if len(output.overall_assessment) >= 100:
            scores.append(1.0)
        else:
            scores.append(0.6)

        return sum(scores) / len(scores)

