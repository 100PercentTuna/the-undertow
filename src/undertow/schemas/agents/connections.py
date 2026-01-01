"""
Schemas for Connection Analysis Agent.

Non-obvious connections - the "wow" insights that link disparate events.
"""

from typing import Literal

from pydantic import Field

from undertow.schemas.base import StrictModel
from undertow.schemas.agents.motivation import StoryContext, AnalysisContext


class StructuralAnalogue(StrictModel):
    """A structural analogue from another context."""

    analogue_situation: str = Field(
        ...,
        min_length=30,
        description="The analogous situation",
    )
    actors_in_analogue: list[str] = Field(
        ...,
        min_length=1,
        description="Actors in the analogous situation",
    )
    structural_similarity: str = Field(
        ...,
        min_length=50,
        description="What makes these structurally similar",
    )
    key_difference: str = Field(
        ...,
        min_length=20,
        description="Important difference to note",
    )
    insight_derived: str = Field(
        ...,
        min_length=30,
        description="What we learn from the comparison",
    )
    confidence: float = Field(..., ge=0, le=1)


class HistoricalParallel(StrictModel):
    """A historical parallel not commonly cited."""

    historical_event: str = Field(..., description="The historical event")
    time_period: str = Field(..., description="When it occurred")
    parallels: list[str] = Field(
        ...,
        min_length=1,
        description="Specific parallels",
    )
    why_not_commonly_cited: str = Field(
        ...,
        min_length=30,
        description="Why this parallel is overlooked",
    )
    lessons_applicable: list[str] = Field(
        default_factory=list,
        description="Lessons that apply today",
    )


class StrangeBedfellow(StrictModel):
    """An unexpected alignment of actors."""

    actors: list[str] = Field(
        ...,
        min_length=2,
        description="The actors aligned",
    )
    why_unexpected: str = Field(
        ...,
        min_length=30,
        description="Why this alignment is surprising",
    )
    common_interest: str = Field(
        ...,
        min_length=30,
        description="What unites them despite differences",
    )
    durability_assessment: Literal["fragile", "tactical", "durable"] = Field(
        ...,
        description="How durable is this alignment",
    )
    implications: str = Field(
        ...,
        min_length=30,
        description="What this alignment implies",
    )


class InvisibleThirdParty(StrictModel):
    """An unmentioned party affected or signaled to."""

    party: str = Field(..., description="The invisible third party")
    why_invisible: str = Field(
        ...,
        min_length=20,
        description="Why they're not mentioned",
    )
    how_affected: str = Field(
        ...,
        min_length=30,
        description="How they're affected or signaled to",
    )
    likely_response: str = Field(
        ...,
        min_length=20,
        description="How they'll likely respond",
    )


class MoneyTrail(StrictModel):
    """Follow the money insight."""

    financial_flow: str = Field(
        ...,
        min_length=30,
        description="The financial flow or interest",
    )
    beneficiaries: list[str] = Field(
        ...,
        min_length=1,
        description="Who benefits financially",
    )
    connection_to_event: str = Field(
        ...,
        min_length=30,
        description="How this connects to the event",
    )
    publicly_acknowledged: bool = Field(
        ...,
        description="Is this connection publicly discussed?",
    )


class TheoreticalLens(StrictModel):
    """An IR theory lens that illuminates hidden dynamics."""

    theory: Literal[
        "realism",
        "liberalism",
        "constructivism",
        "power_transition",
        "network_theory",
        "political_economy",
        "historical_institutionalism",
        "other",
    ] = Field(..., description="The theoretical lens")
    theory_name: str = Field(
        default="",
        description="Specific theory name if 'other'",
    )
    insight_revealed: str = Field(
        ...,
        min_length=50,
        description="What this lens reveals",
    )
    why_useful_here: str = Field(
        ...,
        min_length=30,
        description="Why this lens is particularly useful",
    )


class ConnectionsSynthesis(StrictModel):
    """Synthesis of connection analysis."""

    most_illuminating_connection: str = Field(
        ...,
        min_length=50,
        description="The single most illuminating non-obvious connection",
    )
    pattern_across_connections: str = Field(
        ...,
        min_length=50,
        description="What pattern emerges from these connections",
    )
    what_conventional_analysis_misses: str = Field(
        ...,
        min_length=50,
        description="What conventional analysis would miss",
    )
    recommended_further_investigation: list[str] = Field(
        default_factory=list,
        description="What should be investigated further",
    )
    confidence: float = Field(..., ge=0, le=1)


class ConnectionsInput(StrictModel):
    """Input for Connections Analysis Agent."""

    story: StoryContext = Field(..., description="Story context")
    context: AnalysisContext = Field(
        default_factory=AnalysisContext,
        description="Analysis context",
    )
    motivation_synthesis: str = Field(
        default="",
        description="Motivation analysis if available",
    )
    chains_synthesis: str = Field(
        default="",
        description="Chains analysis if available",
    )


class ConnectionsOutput(StrictModel):
    """Output from Connections Analysis Agent."""

    structural_analogues: list[StructuralAnalogue] = Field(
        default_factory=list,
        description="Structural analogues from other contexts",
    )
    historical_parallels: list[HistoricalParallel] = Field(
        default_factory=list,
        description="Historical parallels",
    )
    strange_bedfellows: list[StrangeBedfellow] = Field(
        default_factory=list,
        description="Unexpected alignments",
    )
    invisible_third_parties: list[InvisibleThirdParty] = Field(
        default_factory=list,
        description="Unmentioned affected parties",
    )
    money_trails: list[MoneyTrail] = Field(
        default_factory=list,
        description="Financial connections",
    )
    theoretical_lenses: list[TheoreticalLens] = Field(
        default_factory=list,
        description="Useful theoretical perspectives",
    )
    synthesis: ConnectionsSynthesis = Field(
        ...,
        description="Overall synthesis",
    )

