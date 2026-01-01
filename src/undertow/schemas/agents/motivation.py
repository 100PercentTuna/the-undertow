"""
Schemas for Motivation Analysis Agent.

Four-layer motivation analysis examining:
- Layer 1: Individual decision-maker
- Layer 2: Institutional interests
- Layer 3: Structural pressures
- Layer 4: Opportunistic window
"""

from typing import Literal

from pydantic import Field, field_validator, model_validator

from undertow.schemas.base import StrictModel


class AssessedFactor(StrictModel):
    """A single assessed factor within a motivation layer."""

    finding: str = Field(
        ...,
        min_length=50,
        max_length=2000,
        description="Detailed finding for this factor",
    )
    evidence: list[str] = Field(
        ...,
        min_length=1,
        description="Evidence supporting the finding",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence level (0-1)",
    )

    @field_validator("confidence")
    @classmethod
    def round_confidence(cls, v: float) -> float:
        """Round confidence to nearest 0.05 for consistency."""
        return round(v * 20) / 20


class MotivationLayer1(StrictModel):
    """
    Layer 1: Individual Decision-Maker Analysis.

    Analyzes the specific person making the decision, not "the country".
    """

    political_position: AssessedFactor = Field(
        ...,
        description="Political position: secure/vulnerable, rising/declining",
    )
    domestic_needs: AssessedFactor = Field(
        ...,
        description="Domestic political needs: coalition, constituencies, distractions",
    )
    psychology_worldview: AssessedFactor = Field(
        ...,
        description="Psychology and worldview: patterns, obsessions, blind spots",
    )
    personal_relationships: AssessedFactor = Field(
        ...,
        description="Personal relationships with other leaders",
    )
    legacy_considerations: AssessedFactor = Field(
        ...,
        description="Legacy considerations: how they want to be remembered",
    )


class MotivationLayer2(StrictModel):
    """
    Layer 2: Institutional Interests Analysis.

    Analyzes the bureaucratic equities involved.
    """

    foreign_ministry: AssessedFactor = Field(
        ...,
        description="Foreign ministry gains/losses",
    )
    military_intelligence: AssessedFactor = Field(
        ...,
        description="Military/intelligence interests: access, basing, intel sharing",
    )
    economic_actors: AssessedFactor = Field(
        ...,
        description="Economic actors who benefit: lobbying, commercial deals",
    )
    institutional_momentum: AssessedFactor = Field(
        ...,
        description="Institutional momentum: long-running effort vs. sudden decision",
    )


class MotivationLayer3(StrictModel):
    """
    Layer 3: Structural Pressures Analysis.

    What would ANY actor in this position likely do?
    """

    systemic_position: AssessedFactor = Field(
        ...,
        description="Systemic position in international system",
    )
    threat_environment: AssessedFactor = Field(
        ...,
        description="Threat environment forcing certain moves",
    )
    economic_structure: AssessedFactor = Field(
        ...,
        description="Economic dependencies and opportunities",
    )
    geographic_imperatives: AssessedFactor = Field(
        ...,
        description="Geographic imperatives: eternal interests from location",
    )


class MotivationLayer4(StrictModel):
    """
    Layer 4: Opportunistic Window Analysis.

    Why now specifically?
    """

    what_changed: AssessedFactor = Field(
        ...,
        description="What changed recently to create an opening",
    )
    position_shifts: AssessedFactor = Field(
        ...,
        description="Whose position shifted to enable this",
    )
    constraint_relaxation: AssessedFactor = Field(
        ...,
        description="What constraint relaxed",
    )
    upcoming_events: AssessedFactor = Field(
        ...,
        description="What's coming that creates urgency",
    )
    factor_convergence: AssessedFactor = Field(
        ...,
        description="Convergence of enabling factors",
    )


class AlternativeHypothesis(StrictModel):
    """An alternative explanation for the observed action."""

    hypothesis: str = Field(
        ...,
        min_length=100,
        max_length=1000,
        description="The alternative hypothesis",
    )
    supporting_evidence: list[str] = Field(
        ...,
        min_length=1,
        description="Evidence supporting this alternative",
    )
    weaknesses: list[str] = Field(
        ...,
        min_length=1,
        description="Weaknesses in this alternative",
    )
    probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Estimated probability (0-1)",
    )


class MotivationSynthesis(StrictModel):
    """
    Synthesis of the four-layer motivation analysis.

    Identifies the primary driver and alternative hypotheses.
    """

    primary_driver: Literal[
        "layer1_individual",
        "layer2_institutional",
        "layer3_structural",
        "layer4_window",
    ] = Field(
        ...,
        description="Which layer does most of the explanatory work",
    )
    primary_driver_explanation: str = Field(
        ...,
        min_length=100,
        max_length=1500,
        description="Explanation of why this layer is primary",
    )
    enabling_conditions: list[str] = Field(
        ...,
        min_length=2,
        description="Conditions that made the primary driver actionable",
    )
    alternative_hypotheses: list[AlternativeHypothesis] = Field(
        ...,
        min_length=2,
        description="Alternative explanations considered",
    )
    overall_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall confidence in this analysis",
    )
    information_gaps: list[str] = Field(
        ...,
        description="Key information gaps affecting confidence",
    )
    falsification_criteria: list[str] = Field(
        ...,
        min_length=1,
        description="What evidence would change this assessment",
    )


class StoryContext(StrictModel):
    """Context about the story being analyzed."""

    headline: str = Field(..., min_length=10, max_length=500)
    summary: str = Field(..., min_length=100, max_length=5000)
    key_events: list[str] = Field(..., min_length=1)
    primary_actors: list[str] = Field(..., min_length=1)
    zones_affected: list[str] = Field(..., min_length=1)


class ActorProfile(StrictModel):
    """Profile of an actor involved in the story."""

    name: str = Field(..., min_length=1, max_length=200)
    role: str = Field(..., min_length=1, max_length=500)
    background: str = Field(..., min_length=50, max_length=2000)
    known_positions: list[str] = Field(default_factory=list)
    relationships: list[str] = Field(default_factory=list)


class AnalysisContext(StrictModel):
    """Context for analysis agents."""

    actors: list[ActorProfile] = Field(default_factory=list)
    historical_context: str = Field(default="")
    regional_context: str = Field(default="")
    relevant_theories: list[str] = Field(default_factory=list)


class MotivationInput(StrictModel):
    """Input schema for Motivation Analysis Agent."""

    story: StoryContext = Field(..., description="Story to analyze")
    context: AnalysisContext = Field(..., description="Analysis context")


class MotivationOutput(StrictModel):
    """Output schema for Motivation Analysis Agent."""

    layer1_individual: MotivationLayer1 = Field(
        ...,
        description="Layer 1: Individual decision-maker analysis",
    )
    layer2_institutional: MotivationLayer2 = Field(
        ...,
        description="Layer 2: Institutional interests analysis",
    )
    layer3_structural: MotivationLayer3 = Field(
        ...,
        description="Layer 3: Structural pressures analysis",
    )
    layer4_window: MotivationLayer4 = Field(
        ...,
        description="Layer 4: Opportunistic window analysis",
    )
    synthesis: MotivationSynthesis = Field(
        ...,
        description="Synthesis and primary driver identification",
    )

    @model_validator(mode="after")
    def validate_synthesis_references_layers(self) -> "MotivationOutput":
        """Ensure synthesis primary driver references a valid layer."""
        valid_drivers = {
            "layer1_individual",
            "layer2_institutional",
            "layer3_structural",
            "layer4_window",
        }
        if self.synthesis.primary_driver not in valid_drivers:
            raise ValueError(
                f"primary_driver must be one of {valid_drivers}, "
                f"got {self.synthesis.primary_driver}"
            )
        return self

