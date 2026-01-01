"""
Schemas for Deep Context Agent.

The deep well - hidden context that loads the situation.
Historical grievances, elite networks, strategic culture.
"""

from typing import Literal

from pydantic import Field

from undertow.schemas.base import StrictModel
from undertow.schemas.agents.motivation import StoryContext, AnalysisContext


class HistoricalGrievance(StrictModel):
    """A historical grievance or remembered wrong."""

    grievance: str = Field(..., min_length=20, description="The grievance")
    parties: list[str] = Field(..., min_length=1, description="Parties involved")
    time_period: str = Field(..., description="When this occurred")
    ongoing_salience: Literal["high", "medium", "low"] = Field(
        ...,
        description="How salient is this today?",
    )
    how_it_loads_present: str = Field(
        ...,
        min_length=30,
        description="How it affects current situation",
    )


class UnpaidDebt(StrictModel):
    """An unpaid political debt or favor."""

    debtor: str = Field(..., description="Who owes")
    creditor: str = Field(..., description="Who is owed")
    nature_of_debt: str = Field(..., min_length=20, description="What's owed")
    context: str = Field(..., description="When/how debt was incurred")
    collection_pressure: Literal["active", "dormant", "expired"] = Field(
        ...,
        description="Is this being called in?",
    )


class PatternRecognition(StrictModel):
    """A relevant historical pattern."""

    pattern: str = Field(..., min_length=30, description="The pattern")
    historical_instances: list[str] = Field(
        ...,
        min_length=1,
        description="Past instances of this pattern",
    )
    current_echo: str = Field(
        ...,
        min_length=30,
        description="How it echoes in current situation",
    )
    lessons_actors_draw: str = Field(
        ...,
        min_length=30,
        description="What lessons do actors draw from this?",
    )


class EliteNetwork(StrictModel):
    """An elite network relevant to the situation."""

    network_name: str = Field(..., description="Network identifier")
    key_members: list[str] = Field(
        default_factory=list,
        description="Key figures in network",
    )
    basis_of_connection: Literal[
        "education",
        "military",
        "family",
        "business",
        "ideology",
        "regional",
        "institutional",
    ] = Field(..., description="What connects them")
    relevance_to_situation: str = Field(
        ...,
        min_length=30,
        description="How this network matters here",
    )


class StrategicCultureElement(StrictModel):
    """An element of strategic culture."""

    actor: str = Field(..., description="Actor/country")
    cultural_element: str = Field(
        ...,
        min_length=30,
        description="The strategic culture element",
    )
    historical_roots: str = Field(
        ...,
        min_length=20,
        description="Where this comes from",
    )
    behavioral_implication: str = Field(
        ...,
        min_length=30,
        description="How it shapes behavior",
    )


class InstitutionalMemory(StrictModel):
    """Institutional memory element."""

    institution: str = Field(..., description="The institution")
    memory: str = Field(..., min_length=30, description="What they 'remember'")
    origin_event: str = Field(..., description="Formative event")
    current_influence: str = Field(
        ...,
        min_length=30,
        description="How it influences current behavior",
    )


class DeepContextSynthesis(StrictModel):
    """Synthesis of deep context analysis."""

    most_salient_historical_factor: str = Field(
        ...,
        min_length=50,
        description="The key historical factor loading this situation",
    )
    key_elite_dynamics: str = Field(
        ...,
        min_length=50,
        description="Key elite network dynamics at play",
    )
    strategic_culture_insight: str = Field(
        ...,
        min_length=50,
        description="What strategic culture tells us",
    )
    what_outsiders_miss: str = Field(
        ...,
        min_length=50,
        description="What external analysts typically miss",
    )
    hidden_constraints: list[str] = Field(
        default_factory=list,
        description="Invisible constraints on actors",
    )
    confidence: float = Field(..., ge=0, le=1)


class DeepContextInput(StrictModel):
    """Input for Deep Context Agent."""

    story: StoryContext = Field(..., description="Story context")
    context: AnalysisContext = Field(
        default_factory=AnalysisContext,
        description="Analysis context",
    )
    actors_to_analyze: list[str] = Field(
        default_factory=list,
        description="Specific actors to deep-dive",
    )
    time_horizon: str = Field(
        default="50 years",
        description="How far back to look",
    )


class DeepContextOutput(StrictModel):
    """Output from Deep Context Agent."""

    historical_grievances: list[HistoricalGrievance] = Field(
        default_factory=list,
        description="Relevant historical grievances",
    )
    unpaid_debts: list[UnpaidDebt] = Field(
        default_factory=list,
        description="Political debts in play",
    )
    pattern_recognitions: list[PatternRecognition] = Field(
        default_factory=list,
        description="Historical patterns echoing",
    )
    elite_networks: list[EliteNetwork] = Field(
        default_factory=list,
        description="Relevant elite networks",
    )
    strategic_culture: list[StrategicCultureElement] = Field(
        default_factory=list,
        description="Strategic culture elements",
    )
    institutional_memories: list[InstitutionalMemory] = Field(
        default_factory=list,
        description="Institutional memories at play",
    )
    synthesis: DeepContextSynthesis = Field(
        ...,
        description="Overall synthesis",
    )

