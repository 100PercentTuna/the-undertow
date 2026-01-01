"""
Schemas for Geometry Analysis Agent.

The map always matters - strategic geography analysis.
"""

from typing import Literal

from pydantic import Field

from undertow.schemas.base import StrictModel
from undertow.schemas.agents.motivation import StoryContext, AnalysisContext


class ChokepointAnalysis(StrictModel):
    """Analysis of relevant chokepoints."""

    chokepoint_name: str = Field(..., description="Name of chokepoint")
    proximity: Literal["direct", "near", "regional", "distant"] = Field(
        ...,
        description="Proximity to event",
    )
    current_controller: str = Field(..., description="Who controls it?")
    strategic_significance: str = Field(
        ...,
        min_length=30,
        description="Why it matters",
    )
    affected_flows: list[str] = Field(
        default_factory=list,
        description="What flows through it (oil, goods, military)",
    )


class AccessAnalysis(StrictModel):
    """Analysis of access implications."""

    access_type: Literal["maritime", "land", "air", "cyber", "economic"] = Field(
        ...,
        description="Type of access",
    )
    access_gained: list[str] = Field(
        default_factory=list,
        description="What access is gained?",
    )
    access_denied: list[str] = Field(
        default_factory=list,
        description="What access is denied to others?",
    )
    range_implications: str = Field(
        default="",
        description="What's now in range?",
    )


class NetworkPosition(StrictModel):
    """Analysis of network positioning."""

    actor: str = Field(..., description="Actor in network")
    other_positions: list[str] = Field(
        default_factory=list,
        description="Other positions this actor holds",
    )
    pattern_building: str = Field(
        default="",
        description="Larger positioning strategy?",
    )
    redundancy_created: bool = Field(
        default=False,
        description="Does this create alternatives?",
    )
    network_interference: str = Field(
        default="",
        description="How does this affect rival networks?",
    )


class ResourceProximity(StrictModel):
    """Analysis of resource geography."""

    resource_type: str = Field(..., description="Type of resource")
    proximity: str = Field(..., description="How close?")
    control_implications: str = Field(
        ...,
        min_length=20,
        description="Control implications",
    )
    supply_chain_effects: list[str] = Field(
        default_factory=list,
        description="Effects on supply chains",
    )


class BufferZoneAnalysis(StrictModel):
    """Analysis of buffer zone dynamics."""

    zone_description: str = Field(..., description="The buffer zone")
    between_powers: list[str] = Field(
        ...,
        min_length=2,
        description="Powers being buffered",
    )
    buffer_status: Literal[
        "intact",
        "eroding",
        "eliminated",
        "expanding",
        "contested",
    ] = Field(..., description="Status of buffer")
    implications: str = Field(
        ...,
        min_length=30,
        description="Strategic implications",
    )


class GeometrySynthesis(StrictModel):
    """Synthesis of geographic analysis."""

    primary_geographic_logic: str = Field(
        ...,
        min_length=50,
        description="Main geographic rationale",
    )
    what_map_reveals: str = Field(
        ...,
        min_length=50,
        description="What does the map show that words don't?",
    )
    access_equation_change: str = Field(
        ...,
        min_length=30,
        description="How has access changed?",
    )
    denial_dimension: str = Field(
        default="",
        description="What's denied to adversaries?",
    )
    long_term_positioning: str = Field(
        ...,
        min_length=30,
        description="Long-term geographic strategy",
    )
    confidence: float = Field(..., ge=0, le=1)


class GeometryInput(StrictModel):
    """Input for Geometry Analysis Agent."""

    story: StoryContext = Field(..., description="Story context")
    context: AnalysisContext = Field(
        default_factory=AnalysisContext,
        description="Analysis context",
    )
    location_details: str = Field(
        default="",
        description="Specific location information",
    )
    relevant_infrastructure: list[str] = Field(
        default_factory=list,
        description="Relevant infrastructure (ports, bases, pipelines)",
    )


class GeometryOutput(StrictModel):
    """Output from Geometry Analysis Agent."""

    chokepoints: list[ChokepointAnalysis] = Field(
        default_factory=list,
        description="Relevant chokepoints",
    )
    access_analysis: list[AccessAnalysis] = Field(
        default_factory=list,
        description="Access implications",
    )
    network_positions: list[NetworkPosition] = Field(
        default_factory=list,
        description="Network positioning",
    )
    resource_proximity: list[ResourceProximity] = Field(
        default_factory=list,
        description="Resource geography",
    )
    buffer_zones: list[BufferZoneAnalysis] = Field(
        default_factory=list,
        description="Buffer zone analysis",
    )
    synthesis: GeometrySynthesis = Field(
        ...,
        description="Overall synthesis",
    )

