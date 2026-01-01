"""
Schemas for Synthesis Agent.

Combines all analysis layers into a coherent whole.
"""

from typing import Literal

from pydantic import Field

from undertow.schemas.base import StrictModel


class KeyFinding(StrictModel):
    """A key finding from the analysis."""

    finding: str = Field(..., min_length=50, description="The finding")
    sources: list[str] = Field(
        ...,
        min_length=1,
        description="Which analyses contributed to this",
    )
    confidence: float = Field(..., ge=0, le=1)
    importance: Literal["critical", "high", "medium", "low"] = Field(
        ...,
        description="How important is this finding",
    )


class NarrativeThread(StrictModel):
    """A narrative thread connecting multiple analyses."""

    thread_name: str = Field(..., description="Name of the thread")
    description: str = Field(
        ...,
        min_length=100,
        description="Description of the thread",
    )
    elements: list[str] = Field(
        ...,
        min_length=2,
        description="Elements from different analyses that connect",
    )
    significance: str = Field(
        ...,
        min_length=50,
        description="Why this thread matters",
    )


class Contradiction(StrictModel):
    """A contradiction or tension between analyses."""

    analysis_a: str = Field(..., description="First analysis")
    claim_a: str = Field(..., description="Claim from first analysis")
    analysis_b: str = Field(..., description="Second analysis")
    claim_b: str = Field(..., description="Contradicting claim")
    resolution: str = Field(
        ...,
        min_length=50,
        description="How we resolve this tension",
    )


class ReaderTakeaway(StrictModel):
    """What the reader should take away."""

    takeaway: str = Field(
        ...,
        min_length=50,
        description="The takeaway",
    )
    why_it_matters: str = Field(
        ...,
        min_length=30,
        description="Why this matters beyond the news cycle",
    )
    confidence: float = Field(..., ge=0, le=1)


class MonitoringRecommendation(StrictModel):
    """What to watch going forward."""

    indicator: str = Field(..., description="What to monitor")
    why: str = Field(..., min_length=30, description="Why this matters")
    timeframe: str = Field(..., description="Expected timeframe")
    what_it_would_mean: str = Field(
        ...,
        min_length=30,
        description="Implications if this happens",
    )


class SynthesisInput(StrictModel):
    """Input for Synthesis Agent."""

    story_headline: str = Field(..., description="Story headline")
    story_summary: str = Field(..., min_length=50, description="Story summary")

    # All the analysis outputs as text summaries
    motivation_analysis: str = Field(
        default="",
        description="Motivation analysis summary",
    )
    chains_analysis: str = Field(
        default="",
        description="Chains analysis summary",
    )
    subtlety_analysis: str = Field(
        default="",
        description="Subtlety analysis summary",
    )
    geometry_analysis: str = Field(
        default="",
        description="Geometry analysis summary",
    )
    deep_context_analysis: str = Field(
        default="",
        description="Deep context analysis summary",
    )
    connections_analysis: str = Field(
        default="",
        description="Connections analysis summary",
    )
    uncertainty_analysis: str = Field(
        default="",
        description="Uncertainty analysis summary",
    )

    target_word_count: int = Field(
        default=500,
        ge=200,
        le=2000,
        description="Target word count for synthesis",
    )


class SynthesisOutput(StrictModel):
    """Output from Synthesis Agent."""

    executive_summary: str = Field(
        ...,
        min_length=200,
        description="Executive summary (2-3 paragraphs)",
    )
    key_findings: list[KeyFinding] = Field(
        ...,
        min_length=3,
        description="Top findings from the analysis",
    )
    narrative_threads: list[NarrativeThread] = Field(
        ...,
        min_length=1,
        description="Threads connecting the analyses",
    )
    contradictions_resolved: list[Contradiction] = Field(
        default_factory=list,
        description="Any contradictions and their resolutions",
    )
    the_real_story: str = Field(
        ...,
        min_length=100,
        description="What's really going on (the game being played)",
    )
    reader_takeaways: list[ReaderTakeaway] = Field(
        ...,
        min_length=2,
        description="What readers should remember",
    )
    monitoring_recommendations: list[MonitoringRecommendation] = Field(
        ...,
        min_length=2,
        description="What to watch going forward",
    )
    overall_confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description="Overall confidence in synthesis",
    )
    word_count: int = Field(..., ge=0, description="Actual word count")

