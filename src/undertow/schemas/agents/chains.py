"""
Schemas for Chain Mapping Agent.

Chain analysis traces consequences forward (ripple map) and
backward (cui bono at each order).
"""

from typing import Literal

from pydantic import Field, field_validator

from undertow.schemas.base import StrictModel
from undertow.schemas.agents.motivation import StoryContext, AnalysisContext


class ConsequenceNode(StrictModel):
    """A single node in the consequence chain."""

    description: str = Field(
        ...,
        min_length=50,
        max_length=1000,
        description="Description of this consequence",
    )
    affected_actors: list[str] = Field(
        ...,
        min_length=1,
        description="Actors affected by this consequence",
    )
    likelihood: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Likelihood of this consequence (0-1)",
    )
    time_horizon: str = Field(
        ...,
        description="Expected time horizon (days, weeks, months, years)",
    )
    evidence: list[str] = Field(
        default_factory=list,
        description="Evidence supporting this consequence",
    )


class ConsequenceOrder(StrictModel):
    """A single order of consequences."""

    order: int = Field(..., ge=1, le=5, description="Order number (1-5)")
    consequences: list[ConsequenceNode] = Field(
        ...,
        min_length=1,
        description="Consequences at this order",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in this order's analysis",
    )

    @field_validator("confidence")
    @classmethod
    def confidence_decreases_with_order(cls, v: float, info) -> float:
        """Higher orders should have lower confidence."""
        # This is validated at the output level
        return round(v * 20) / 20  # Round to nearest 0.05


class Beneficiary(StrictModel):
    """An identified beneficiary from the action."""

    actor: str = Field(..., min_length=1, description="The beneficiary actor")
    order: int = Field(
        ...,
        ge=1,
        le=5,
        description="At which order do they benefit",
    )
    benefit: str = Field(
        ...,
        min_length=50,
        max_length=1000,
        description="Description of the benefit",
    )
    means_to_influence: bool = Field(
        ...,
        description="Did they have means to influence the original action?",
    )
    influence_channels: list[str] = Field(
        default_factory=list,
        description="Channels through which they could influence",
    )
    suspicion_level: Literal["low", "medium", "high"] = Field(
        ...,
        description="How suspicious is this beneficiary pattern",
    )


class InteractionPoint(StrictModel):
    """A point where multiple causal chains interact."""

    chains: list[str] = Field(
        ...,
        min_length=2,
        description="Names/descriptions of interacting chains",
    )
    interaction_description: str = Field(
        ...,
        min_length=100,
        max_length=1500,
        description="How these chains interact",
    )
    emergent_effects: list[str] = Field(
        ...,
        min_length=1,
        description="Effects that emerge from the interaction",
    )
    time_horizon: str = Field(..., description="When this interaction manifests")


class RippleMap(StrictModel):
    """Forward-tracing consequence map."""

    first_order: ConsequenceOrder = Field(
        ...,
        description="First-order (direct) consequences",
    )
    second_order: ConsequenceOrder = Field(
        ...,
        description="Second-order (response) consequences",
    )
    third_order: ConsequenceOrder = Field(
        ...,
        description="Third-order (systemic adaptation) consequences",
    )
    fourth_order: ConsequenceOrder = Field(
        ...,
        description="Fourth-order (equilibrium shift) consequences",
    )
    fifth_order: ConsequenceOrder | None = Field(
        None,
        description="Fifth-order (distant ripples) consequences if relevant",
    )


class CuiBonoAnalysis(StrictModel):
    """Backward-tracing beneficiary analysis."""

    obvious_beneficiaries: list[Beneficiary] = Field(
        ...,
        min_length=1,
        description="First-order beneficiaries (obvious)",
    )
    second_order_beneficiaries: list[Beneficiary] = Field(
        ...,
        min_length=1,
        description="Second-order beneficiaries",
    )
    third_order_beneficiaries: list[Beneficiary] = Field(
        default_factory=list,
        description="Third-order beneficiaries",
    )
    hidden_beneficiaries: list[Beneficiary] = Field(
        default_factory=list,
        description="Potentially hidden beneficiaries (high suspicion)",
    )
    key_insight: str = Field(
        ...,
        min_length=100,
        max_length=1500,
        description="Key insight from cui bono analysis",
    )


class ChainInteractions(StrictModel):
    """Analysis of how this chain interacts with others."""

    parallel_chains: list[str] = Field(
        default_factory=list,
        description="Other significant chains running in parallel",
    )
    interaction_points: list[InteractionPoint] = Field(
        default_factory=list,
        description="Points where chains interact",
    )
    emergent_dynamics: str = Field(
        default="",
        description="Emergent dynamics from chain interactions",
    )


class ChainsSynthesis(StrictModel):
    """Synthesis of chain mapping analysis."""

    most_significant_consequence: str = Field(
        ...,
        min_length=100,
        max_length=1500,
        description="The single most significant consequence identified",
    )
    order_of_significance: int = Field(
        ...,
        ge=1,
        le=5,
        description="At which order is the most significant consequence",
    )
    hidden_game_hypothesis: str = Field(
        ...,
        min_length=100,
        max_length=1500,
        description="Hypothesis about what game is actually being played",
    )
    watch_indicators: list[str] = Field(
        ...,
        min_length=2,
        description="What to watch that would confirm/disconfirm the analysis",
    )
    confidence_decay_note: str = Field(
        ...,
        description="Note on confidence decay across orders",
    )
    information_gaps: list[str] = Field(
        ...,
        description="Key information gaps",
    )


class ChainsInput(StrictModel):
    """Input schema for Chain Mapping Agent."""

    story: StoryContext = Field(..., description="Story to analyze")
    context: AnalysisContext = Field(..., description="Analysis context")
    motivation_synthesis: str = Field(
        default="",
        description="Summary from motivation analysis (if available)",
    )


class ChainsOutput(StrictModel):
    """Output schema for Chain Mapping Agent."""

    ripple_map: RippleMap = Field(
        ...,
        description="Forward consequence mapping",
    )
    cui_bono: CuiBonoAnalysis = Field(
        ...,
        description="Backward beneficiary analysis",
    )
    interactions: ChainInteractions = Field(
        ...,
        description="Chain interaction analysis",
    )
    synthesis: ChainsSynthesis = Field(
        ...,
        description="Overall synthesis",
    )

