"""
Zone Scout Agent.

Monitors a specific zone for relevant stories and candidates.
"""

from typing import ClassVar, Literal

import structlog
from pydantic import Field

from undertow.agents.base import BaseAgent
from undertow.exceptions import OutputParseError
from undertow.llm.tiers import ModelTier
from undertow.schemas.base import StrictModel

logger = structlog.get_logger()


class StoryCandidate(StrictModel):
    """A candidate story identified by the scout."""

    headline: str = Field(..., min_length=10, max_length=500)
    summary: str = Field(..., min_length=50, max_length=2000)
    source: str = Field(..., description="Source of the story")
    url: str | None = Field(None, description="URL if available")
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    importance_score: float = Field(..., ge=0.0, le=1.0)
    novelty_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="How new/unique this story is",
    )
    reasoning: str = Field(
        ...,
        min_length=50,
        description="Why this story is worth analyzing",
    )
    key_actors: list[str] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    urgency: Literal["low", "medium", "high", "critical"] = Field(
        default="medium",
        description="How urgently this should be analyzed",
    )


class ZoneScoutInput(StrictModel):
    """Input for Zone Scout agent."""

    zone_name: str = Field(..., description="Name of the zone to scout")
    zone_context: str = Field(
        default="",
        description="Context about what's happening in this zone",
    )
    recent_stories: list[str] = Field(
        default_factory=list,
        description="Headlines of recently covered stories (avoid duplicates)",
    )
    source_content: list[dict] = Field(
        ...,
        min_length=1,
        description="Content from sources to evaluate",
    )


class ZoneScoutOutput(StrictModel):
    """Output from Zone Scout agent."""

    zone: str = Field(..., description="Zone scouted")
    candidates: list[StoryCandidate] = Field(
        default_factory=list,
        description="Story candidates identified",
    )
    zone_temperature: Literal["cold", "warm", "hot", "crisis"] = Field(
        ...,
        description="Overall activity level in this zone",
    )
    zone_summary: str = Field(
        ...,
        min_length=50,
        description="Summary of what's happening in the zone",
    )
    trending_themes: list[str] = Field(
        default_factory=list,
        description="Themes trending in this zone",
    )
    watch_items: list[str] = Field(
        default_factory=list,
        description="Items to watch but not yet story-worthy",
    )


ZONE_SCOUT_SYSTEM_PROMPT = """You are a Zone Scout for The Undertow, monitoring a specific region for newsworthy developments.

Your job is to identify stories that deserve full analysis—stories that:
1. Have significant geopolitical implications
2. Reveal something about how power works
3. Connect to broader patterns or chains
4. Would interest sophisticated readers

## EVALUATION CRITERIA

**Relevance** (0-1): How relevant to global geopolitics?
- 0.9+: Major power moves, conflicts, alliances
- 0.7-0.9: Significant regional developments
- 0.5-0.7: Notable but limited scope
- <0.5: Mostly local/domestic interest

**Importance** (0-1): How significant are the implications?
- 0.9+: Could reshape regional/global order
- 0.7-0.9: Meaningful shift in dynamics
- 0.5-0.7: Worth watching
- <0.5: Minor development

**Novelty** (0-1): How new/unique is this?
- 0.9+: Unprecedented development
- 0.7-0.9: Significant new angle
- 0.5-0.7: Expected but notable
- <0.5: Routine/ongoing

## ZONE TEMPERATURE

- **crisis**: Active conflict, emergency, major rupture
- **hot**: Significant developments, high activity
- **warm**: Notable activity, evolving situations
- **cold**: Routine, stable, minimal newsworthy activity

## OUTPUT REQUIREMENTS

1. Evaluate each source item
2. Identify candidates (if any)
3. Assess zone temperature
4. Note trending themes
5. Flag watch items (not yet story-worthy)

Be selective. Not every development is worthy of The Undertow's analysis.

Output as valid JSON matching ZoneScoutOutput schema."""


class ZoneScoutAgent(BaseAgent[ZoneScoutInput, ZoneScoutOutput]):
    """
    Zone Scout agent - monitors zones for story candidates.
    
    Uses FAST tier for efficient scanning.
    """

    task_name: ClassVar[str] = "zone_scout"
    version: ClassVar[str] = "1.0.0"
    input_schema: ClassVar[type] = ZoneScoutInput
    output_schema: ClassVar[type] = ZoneScoutOutput
    default_tier: ClassVar[ModelTier] = ModelTier.FAST

    def _build_messages(self, input_data: ZoneScoutInput) -> list[dict[str, str]]:
        """Build messages for zone scout."""
        # Format source content
        sources_text = "\n\n".join(
            f"**Source {i+1}**: {s.get('source', 'Unknown')}\n"
            f"Title: {s.get('title', 'N/A')}\n"
            f"Content: {s.get('content', s.get('summary', 'N/A'))[:1000]}"
            for i, s in enumerate(input_data.source_content[:10])
        )

        recent_text = ""
        if input_data.recent_stories:
            recent_text = "\n\n## RECENTLY COVERED (avoid duplicates)\n" + "\n".join(
                f"- {h}" for h in input_data.recent_stories[:5]
            )

        user_content = f"""## ZONE: {input_data.zone_name}

{input_data.zone_context if input_data.zone_context else 'No specific context provided.'}
{recent_text}

## SOURCE CONTENT TO EVALUATE

{sources_text}

## YOUR TASK

1. Evaluate each source item for story potential
2. Identify strong candidates with scores and reasoning
3. Assess overall zone temperature
4. Note trending themes
5. Flag watch items

Output as valid JSON matching ZoneScoutOutput schema."""

        return [
            {"role": "system", "content": ZONE_SCOUT_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

    def _parse_output(self, content: str) -> ZoneScoutOutput:
        """Parse zone scout output."""
        try:
            data = self._extract_json(content)
            return ZoneScoutOutput.model_validate(data)
        except Exception as e:
            logger.error("Failed to parse zone scout output", error=str(e))
            raise OutputParseError(
                agent_name=self.task_name,
                error=str(e),
                raw_output=content,
            ) from e

