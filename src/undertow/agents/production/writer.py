"""
Writer Agent - transforms analysis into Undertow articles.

Produces the distinctive voice and structure defined in THE_UNDERTOW.md.
"""

from typing import ClassVar

import structlog

from undertow.agents.base import BaseAgent
from undertow.exceptions import OutputParseError
from undertow.llm.tiers import ModelTier
from undertow.schemas.base import StrictModel
from pydantic import Field

logger = structlog.get_logger()


class ArticleSection(StrictModel):
    """A single section of the article."""

    section_type: str = Field(..., description="Type (hook, what_happened, etc.)")
    heading: str = Field(..., description="Section heading")
    content: str = Field(..., min_length=100, description="Section content")
    word_count: int = Field(..., ge=0)


class WriterInput(StrictModel):
    """Input for Writer agent."""

    headline: str = Field(..., min_length=10, description="Story headline")
    subhead: str = Field(default="", description="Story subhead")
    summary: str = Field(..., min_length=50, description="Story summary")
    motivation_analysis: str = Field(default="", description="Motivation layer analysis")
    chains_analysis: str = Field(default="", description="Causal chains analysis")
    key_claims: list[str] = Field(default_factory=list, description="Key claims")
    zones: list[str] = Field(default_factory=list, description="Zones covered")
    quality_score: float = Field(default=0.8, ge=0, le=1, description="Analysis quality")


class WriterOutput(StrictModel):
    """Output from Writer agent."""

    headline: str = Field(..., min_length=10, description="Final headline")
    subhead: str = Field(..., min_length=10, description="Final subhead")
    sections: list[ArticleSection] = Field(..., min_length=4, description="Article sections")
    full_text: str = Field(..., min_length=1000, description="Complete article text")
    read_time_minutes: int = Field(..., ge=1, le=60)
    word_count: int = Field(..., ge=0)
    takeaway: str = Field(..., min_length=50, description="Key takeaway")


WRITER_SYSTEM_PROMPT = """You are the Writer for The Undertow, a geopolitical intelligence publication.

## THE UNDERTOW VOICE

The Undertow reads like a brilliant friend who happens to have spent twenty years thinking about how power works—someone who can explain complex geopolitics over dinner without making you feel stupid, but who's also willing to admit when something is genuinely confusing.

- **Serious but not solemn**: The stakes are real; self-importance is still the enemy.
- **Witty but not flip**: Well-placed observations make readers pay attention.
- **Confident but not arrogant**: We have views and argue them. We acknowledge when wrong.
- **Dense but not impenetrable**: Every sentence does work.

## FORBIDDEN PHRASES

NEVER use:
- "In today's interconnected world..."
- "Time will tell..."
- "Remains to be seen..."
- "Violence erupted" (violence doesn't erupt; people commit it)
- "Tensions escalated" (who escalated them?)

## ARTICLE STRUCTURE

1. **THE HOOK** (200-400 words)
   What makes this matter. Not the event; the significance.

2. **WHAT HAPPENED** (500-800 words)
   Forensic reconstruction. Sourced and verified.

3. **THE MOTIVATION ANALYSIS** (800-1,200 words)
   Four layers: individual, institutional, structural, opportunistic.

4. **THE CHAINS** (1,000-1,500 words)
   Forward tracing: consequences to fourth/fifth order.
   Backward tracing: cui bono at each level.

5. **WHAT WE DON'T KNOW** (300-400 words)
   Specific uncertainties. Confidence calibration.

6. **THE TAKEAWAY** (300-400 words)
   Why this matters beyond the news cycle.

## OUTPUT FORMAT

Generate a complete article with all sections. Make it sing.

Output as valid JSON matching WriterOutput schema."""


class WriterAgent(BaseAgent[WriterInput, WriterOutput]):
    """
    Writer agent - produces Undertow articles.

    Uses FRONTIER tier for voice quality.
    """

    task_name: ClassVar[str] = "writer"
    version: ClassVar[str] = "1.0.0"
    input_schema: ClassVar[type] = WriterInput
    output_schema: ClassVar[type] = WriterOutput
    default_tier: ClassVar[ModelTier] = ModelTier.FRONTIER

    def _build_messages(self, input_data: WriterInput) -> list[dict[str, str]]:
        """Build messages for writer."""
        zones_text = f"**Zones**: {', '.join(input_data.zones)}" if input_data.zones else ""
        claims_text = ""
        if input_data.key_claims:
            claims_text = "\n\n## KEY CLAIMS\n" + "\n".join(
                f"- {c}" for c in input_data.key_claims
            )

        user_content = f"""## STORY TO WRITE

**Headline**: {input_data.headline}
**Subhead**: {input_data.subhead or 'Generate one'}
{zones_text}

## SUMMARY

{input_data.summary}

## MOTIVATION ANALYSIS

{input_data.motivation_analysis or 'Not provided - infer from summary'}

## CAUSAL CHAINS ANALYSIS

{input_data.chains_analysis or 'Not provided - trace the likely chains'}
{claims_text}

## ANALYSIS QUALITY

Quality score: {input_data.quality_score:.2f}
(Adjust confidence in writing accordingly)

## YOUR TASK

Write a complete Undertow article. Follow the structure. Nail the voice.
Make every sentence do work.

Output as valid JSON matching WriterOutput schema."""

        return [
            {"role": "system", "content": WRITER_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

    def _parse_output(self, content: str) -> WriterOutput:
        """Parse writer output."""
        try:
            data = self._extract_json(content)
            return WriterOutput.model_validate(data)
        except Exception as e:
            logger.error("Failed to parse writer output", error=str(e))
            raise OutputParseError(
                agent_name=self.task_name,
                error=str(e),
                raw_output=content,
            ) from e

    async def _assess_quality(
        self,
        output: WriterOutput,
        input_data: WriterInput,
    ) -> float:
        """Assess quality of article."""
        scores: list[float] = []

        # Word count appropriate?
        if 2000 <= output.word_count <= 6000:
            scores.append(1.0)
        elif 1000 <= output.word_count <= 8000:
            scores.append(0.7)
        else:
            scores.append(0.4)

        # All required sections present?
        required_types = {"hook", "what_happened", "motivation", "chains", "takeaway"}
        present_types = {s.section_type.lower() for s in output.sections}
        coverage = len(required_types & present_types) / len(required_types)
        scores.append(coverage)

        # Sections substantive?
        section_scores = []
        for section in output.sections:
            if section.word_count >= 200:
                section_scores.append(1.0)
            elif section.word_count >= 100:
                section_scores.append(0.7)
            else:
                section_scores.append(0.4)
        if section_scores:
            scores.append(sum(section_scores) / len(section_scores))

        # Forbidden phrases check
        forbidden = [
            "in today's interconnected world",
            "time will tell",
            "remains to be seen",
            "violence erupted",
            "tensions escalated",
        ]
        text_lower = output.full_text.lower()
        violations = sum(1 for f in forbidden if f in text_lower)
        scores.append(max(0.5, 1.0 - violations * 0.15))

        return sum(scores) / len(scores)
