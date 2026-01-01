"""
Story Scorer Agent.

Evaluates and scores stories for selection into the daily edition.
"""

from typing import ClassVar, Literal

import structlog
from pydantic import Field

from undertow.agents.base import BaseAgent
from undertow.exceptions import OutputParseError
from undertow.llm.tiers import ModelTier
from undertow.schemas.base import StrictModel

logger = structlog.get_logger()


class ScoringDimension(StrictModel):
    """Score for a single dimension."""

    dimension: str = Field(..., description="Dimension name")
    score: float = Field(..., ge=0.0, le=1.0)
    reasoning: str = Field(..., min_length=20)


class StoryScorerInput(StrictModel):
    """Input for Story Scorer agent."""

    headline: str = Field(..., min_length=10)
    summary: str = Field(..., min_length=50)
    content: str = Field(..., min_length=100)
    source_name: str = Field(...)
    zone: str = Field(...)
    existing_selection: list[str] = Field(
        default_factory=list,
        description="Headlines already selected for today (for diversity)",
    )


class StoryScorerOutput(StrictModel):
    """Output from Story Scorer agent."""

    dimensions: list[ScoringDimension] = Field(
        ...,
        min_length=5,
        description="Scores for each dimension",
    )
    overall_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Weighted overall score",
    )
    recommendation: Literal["strong_include", "include", "consider", "exclude"] = Field(
        ...,
        description="Recommendation for inclusion",
    )
    recommendation_reasoning: str = Field(
        ...,
        min_length=50,
        description="Why this recommendation",
    )
    complementarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="How well it complements existing selection",
    )
    estimated_complexity: Literal["low", "medium", "high", "very_high"] = Field(
        ...,
        description="Estimated analysis complexity",
    )
    key_angles: list[str] = Field(
        default_factory=list,
        description="Key analytical angles to pursue",
    )


STORY_SCORER_SYSTEM_PROMPT = """You are a Story Scorer for The Undertow, deciding which stories make it into the daily edition.

Your job is to score stories on multiple dimensions and recommend inclusion.

## SCORING DIMENSIONS

1. **Geopolitical Significance** (weight: 0.25)
   - Global/regional importance
   - Power dynamics implications
   - Precedent-setting potential

2. **Analytical Depth Potential** (weight: 0.25)
   - Can we trace meaningful chains?
   - Are there hidden motivations to uncover?
   - Is there non-obvious analysis to add?

3. **Reader Value** (weight: 0.20)
   - Will sophisticated readers care?
   - Does it illuminate how power works?
   - Is it more than news coverage can provide?

4. **Timeliness** (weight: 0.15)
   - Is this the right moment?
   - Is it developing or concluded?
   - Window for relevance?

5. **Source Quality** (weight: 0.15)
   - Reliable sources available?
   - Multiple perspectives accessible?
   - Can we verify key claims?

## RECOMMENDATIONS

- **strong_include**: Top tier, must cover (>0.8)
- **include**: Good candidate (0.65-0.8)
- **consider**: Possible but not essential (0.5-0.65)
- **exclude**: Not worth the analysis (<0.5)

## COMPLEMENTARITY

Consider existing selection:
- Different zones = higher complementarity
- Different themes = higher complementarity
- Similar to existing = lower complementarity

## COMPLEXITY ESTIMATE

- **low**: Straightforward analysis, 1-2 clear angles
- **medium**: Multiple angles, some research needed
- **high**: Complex chains, multiple actors, deep research
- **very_high**: Exceptional complexity, may need extra passes

Output as valid JSON matching StoryScorerOutput schema."""


class StoryScorerAgent(BaseAgent[StoryScorerInput, StoryScorerOutput]):
    """
    Story Scorer agent - scores stories for selection.
    
    Uses STANDARD tier for balanced evaluation.
    """

    task_name: ClassVar[str] = "story_scorer"
    version: ClassVar[str] = "1.0.0"
    input_schema: ClassVar[type] = StoryScorerInput
    output_schema: ClassVar[type] = StoryScorerOutput
    default_tier: ClassVar[ModelTier] = ModelTier.STANDARD

    def _build_messages(self, input_data: StoryScorerInput) -> list[dict[str, str]]:
        """Build messages for story scorer."""
        existing_text = ""
        if input_data.existing_selection:
            existing_text = "\n\n## ALREADY SELECTED FOR TODAY\n" + "\n".join(
                f"- {h}" for h in input_data.existing_selection
            )

        user_content = f"""## STORY TO SCORE

**Headline**: {input_data.headline}

**Source**: {input_data.source_name}

**Zone**: {input_data.zone}

**Summary**: {input_data.summary}

**Content**:
{input_data.content[:3000]}
{existing_text}

## YOUR TASK

1. Score on all 5 dimensions with reasoning
2. Calculate weighted overall score
3. Assess complementarity with existing selection
4. Estimate analysis complexity
5. Identify key analytical angles
6. Make inclusion recommendation

Output as valid JSON matching StoryScorerOutput schema."""

        return [
            {"role": "system", "content": STORY_SCORER_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

    def _parse_output(self, content: str) -> StoryScorerOutput:
        """Parse story scorer output."""
        try:
            data = self._extract_json(content)
            return StoryScorerOutput.model_validate(data)
        except Exception as e:
            logger.error("Failed to parse story scorer output", error=str(e))
            raise OutputParseError(
                agent_name=self.task_name,
                error=str(e),
                raw_output=content,
            ) from e

