"""
Editor Agent.

Reviews and improves articles before publication.
Ensures quality, voice consistency, and factual accuracy.
"""

from typing import ClassVar, Literal

import structlog
from pydantic import Field

from undertow.agents.base import BaseAgent
from undertow.exceptions import OutputParseError
from undertow.llm.tiers import ModelTier
from undertow.schemas.base import StrictModel

logger = structlog.get_logger()


class EditSuggestion(StrictModel):
    """A single edit suggestion."""

    location: str = Field(..., description="Where in the article")
    issue_type: Literal[
        "factual",
        "clarity",
        "voice",
        "structure",
        "length",
        "missing_context",
        "overconfidence",
        "style",
    ] = Field(..., description="Type of issue")
    original_text: str = Field(..., description="Original text (excerpt)")
    suggested_text: str = Field(..., description="Suggested revision")
    rationale: str = Field(..., min_length=20, description="Why this change")
    priority: Literal["required", "recommended", "optional"] = Field(
        ...,
        description="Priority of this edit",
    )


class EditorInput(StrictModel):
    """Input for Editor Agent."""

    headline: str = Field(..., description="Article headline")
    subhead: str = Field(default="", description="Article subhead")
    content: str = Field(..., min_length=500, description="Article content")
    quality_score: float = Field(
        default=0.8,
        ge=0,
        le=1,
        description="Current quality score",
    )
    word_count: int = Field(default=0, description="Current word count")
    target_word_count: int = Field(
        default=3000,
        description="Target word count",
    )


class EditorOutput(StrictModel):
    """Output from Editor Agent."""

    overall_assessment: str = Field(
        ...,
        min_length=100,
        description="Overall assessment of the article",
    )
    quality_rating: Literal[
        "excellent",
        "good",
        "acceptable",
        "needs_work",
        "major_revision",
    ] = Field(..., description="Quality rating")
    ready_for_publication: bool = Field(
        ...,
        description="Whether article is ready",
    )
    edit_suggestions: list[EditSuggestion] = Field(
        default_factory=list,
        description="Specific edit suggestions",
    )
    voice_consistency: float = Field(
        ...,
        ge=0,
        le=1,
        description="How consistent is the voice (0-1)",
    )
    strengths: list[str] = Field(
        default_factory=list,
        description="What works well",
    )
    weaknesses: list[str] = Field(
        default_factory=list,
        description="What needs improvement",
    )
    revised_quality_score: float = Field(
        ...,
        ge=0,
        le=1,
        description="Estimated quality after edits",
    )


EDITOR_SYSTEM_PROMPT = """You are the Editor for The Undertow.

Your role is to REVIEW and IMPROVE articles before publication.
You ensure quality, voice consistency, and analytical rigor.

## THE UNDERTOW VOICE

Articles should read like a brilliant friend explaining geopolitics:
- Serious but not solemn
- Witty but not flip
- Confident but not arrogant
- Dense but not impenetrable

## FORBIDDEN PHRASES

Flag any instances of:
- "In today's interconnected world..."
- "Time will tell..."
- "Remains to be seen..."
- "Violence erupted" (passive voice hiding agency)
- "Tensions escalated" (who escalated them?)

## REVIEW CRITERIA

1. **Factual Accuracy**: Are claims supported? Sources cited?
2. **Analytical Depth**: Does it go beyond surface analysis?
3. **Voice Consistency**: Does it sound like The Undertow?
4. **Structure**: Does it flow logically?
5. **Length**: Is it appropriately dense without padding?
6. **Uncertainty**: Are confidence levels appropriate?
7. **Insight**: Does it offer "wow" moments?

## ISSUE TYPES

- **factual**: Potential factual error or unsupported claim
- **clarity**: Unclear or confusing passage
- **voice**: Doesn't match The Undertow voice
- **structure**: Organizational issue
- **length**: Too long/short, padding, repetition
- **missing_context**: Reader needs more background
- **overconfidence**: Claim too certain given evidence
- **style**: Grammar, word choice, style issue

## PRIORITY LEVELS

- **required**: Must fix before publication
- **recommended**: Should fix, significantly improves article
- **optional**: Nice to have, minor improvement

## OUTPUT REQUIREMENTS

1. Provide overall assessment
2. Rate quality (excellent/good/acceptable/needs_work/major_revision)
3. State if ready for publication
4. List specific edit suggestions with location, type, and rationale
5. Note strengths and weaknesses
6. Estimate quality after edits

Output as valid JSON matching EditorOutput schema."""


class EditorAgent(BaseAgent[EditorInput, EditorOutput]):
    """
    Editor agent - reviews and improves articles.

    Uses HIGH tier for nuanced editorial judgment.
    """

    task_name: ClassVar[str] = "editor"
    version: ClassVar[str] = "1.0.0"
    input_schema: ClassVar[type] = EditorInput
    output_schema: ClassVar[type] = EditorOutput
    default_tier: ClassVar[ModelTier] = ModelTier.HIGH

    def _build_messages(self, input_data: EditorInput) -> list[dict[str, str]]:
        """Build messages for editor."""
        user_content = f"""## ARTICLE TO REVIEW

**Headline**: {input_data.headline}
**Subhead**: {input_data.subhead or 'None'}
**Word Count**: {input_data.word_count or 'Unknown'}
**Target Word Count**: {input_data.target_word_count}
**Current Quality Score**: {input_data.quality_score}

## CONTENT

{input_data.content}

## YOUR TASK

Review this article for The Undertow:
1. Assess overall quality
2. Check voice consistency
3. Identify specific issues with suggested fixes
4. Note strengths and weaknesses
5. Determine if ready for publication

Be rigorous but fair. Good articles should pass.

Output as valid JSON matching EditorOutput schema."""

        return [
            {"role": "system", "content": EDITOR_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

    def _parse_output(self, content: str) -> EditorOutput:
        """Parse editor output."""
        try:
            data = self._extract_json(content)
            return EditorOutput.model_validate(data)
        except Exception as e:
            logger.error("Failed to parse editor output", error=str(e))
            raise OutputParseError(
                agent_name=self.task_name,
                error=str(e),
                raw_output=content,
            ) from e

    async def _assess_quality(
        self,
        output: EditorOutput,
        input_data: EditorInput,
    ) -> float:
        """Assess quality of editorial review."""
        scores: list[float] = []

        # Assessment depth
        if len(output.overall_assessment) >= 150:
            scores.append(1.0)
        elif len(output.overall_assessment) >= 100:
            scores.append(0.7)
        else:
            scores.append(0.5)

        # Suggestions provided
        if output.edit_suggestions:
            scores.append(1.0)
        else:
            scores.append(0.5)

        # Balanced feedback (strengths and weaknesses)
        if output.strengths and output.weaknesses:
            scores.append(1.0)
        elif output.strengths or output.weaknesses:
            scores.append(0.6)
        else:
            scores.append(0.3)

        return sum(scores) / len(scores)

