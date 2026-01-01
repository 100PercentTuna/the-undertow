"""
Schemas for Uncertainty Analysis Agent.

Explicit uncertainty quantification and confidence calibration.
"""

from typing import Literal

from pydantic import Field

from undertow.schemas.base import StrictModel


class KnowledgeClassification(StrictModel):
    """Classification of a knowledge claim."""

    claim: str = Field(..., min_length=20, description="The claim")
    classification: Literal[
        "known_fact",
        "assessed_inference",
        "informed_speculation",
        "acknowledged_unknown",
    ] = Field(..., description="How certain are we?")
    evidence_basis: str = Field(
        ...,
        min_length=20,
        description="What's the evidence basis?",
    )
    source_quality: Literal["high", "medium", "low", "unknown"] = Field(
        ...,
        description="Quality of underlying sources",
    )
    confidence: float = Field(..., ge=0, le=1)


class DisagreementPoint(StrictModel):
    """A point where credible analysts disagree."""

    topic: str = Field(..., description="What's disputed")
    position_a: str = Field(..., min_length=30, description="First position")
    position_b: str = Field(..., min_length=30, description="Second position")
    our_assessment: str = Field(
        ...,
        min_length=30,
        description="Our view on the disagreement",
    )
    resolution_evidence: str = Field(
        default="",
        description="What evidence would resolve this?",
    )


class InformationGap(StrictModel):
    """An identified gap in available information."""

    gap_description: str = Field(
        ...,
        min_length=30,
        description="What we don't know",
    )
    importance: Literal["critical", "significant", "moderate", "minor"] = Field(
        ...,
        description="How important is this gap?",
    )
    why_it_matters: str = Field(
        ...,
        min_length=30,
        description="Why this gap matters for the analysis",
    )
    how_to_fill: str = Field(
        default="",
        description="How this gap might be filled",
    )


class FalsificationCriteria(StrictModel):
    """Criteria that would falsify key assessments."""

    assessment: str = Field(..., description="The assessment that could be wrong")
    falsification_evidence: str = Field(
        ...,
        min_length=30,
        description="What evidence would prove this wrong?",
    )
    likelihood_of_discovery: Literal["high", "medium", "low"] = Field(
        ...,
        description="How likely is such evidence to emerge?",
    )
    monitoring_recommendation: str = Field(
        default="",
        description="What to watch for",
    )


class ConfidenceDriver(StrictModel):
    """A factor driving confidence up or down."""

    factor: str = Field(..., description="The factor")
    direction: Literal["increases", "decreases"] = Field(
        ...,
        description="Does it increase or decrease confidence?",
    )
    magnitude: Literal["strongly", "moderately", "slightly"] = Field(
        ...,
        description="How much does it affect confidence?",
    )
    explanation: str = Field(
        ...,
        min_length=30,
        description="Why this factor matters",
    )


class UncertaintySynthesis(StrictModel):
    """Synthesis of uncertainty analysis."""

    overall_confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description="Overall confidence in analysis",
    )
    confidence_band: str = Field(
        ...,
        description="e.g., '65-80%' or 'moderate-high'",
    )
    primary_uncertainty_source: str = Field(
        ...,
        min_length=50,
        description="Biggest source of uncertainty",
    )
    what_we_know_well: list[str] = Field(
        default_factory=list,
        description="Our highest-confidence assessments",
    )
    what_we_dont_know: list[str] = Field(
        default_factory=list,
        description="Key acknowledged unknowns",
    )
    hedging_language_guidance: str = Field(
        ...,
        min_length=30,
        description="How to hedge claims appropriately",
    )


class UncertaintyInput(StrictModel):
    """Input for Uncertainty Analysis Agent."""

    analysis_content: str = Field(
        ...,
        min_length=200,
        description="The analysis to assess uncertainty for",
    )
    key_claims: list[str] = Field(
        ...,
        min_length=1,
        description="Key claims made in the analysis",
    )
    stated_confidence: float = Field(
        default=0.8,
        ge=0,
        le=1,
        description="Confidence stated in the analysis",
    )


class UncertaintyOutput(StrictModel):
    """Output from Uncertainty Analysis Agent."""

    knowledge_classifications: list[KnowledgeClassification] = Field(
        ...,
        min_length=1,
        description="Classification of key claims",
    )
    disagreement_points: list[DisagreementPoint] = Field(
        default_factory=list,
        description="Points of analyst disagreement",
    )
    information_gaps: list[InformationGap] = Field(
        default_factory=list,
        description="Identified information gaps",
    )
    falsification_criteria: list[FalsificationCriteria] = Field(
        default_factory=list,
        description="What would prove us wrong",
    )
    confidence_drivers: list[ConfidenceDriver] = Field(
        default_factory=list,
        description="Factors affecting confidence",
    )
    synthesis: UncertaintySynthesis = Field(
        ...,
        description="Overall synthesis",
    )

