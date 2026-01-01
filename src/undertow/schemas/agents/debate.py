"""
Schemas for debate agents (Challenger, Advocate, Judge).
"""

from typing import Literal

from pydantic import Field

from undertow.schemas.base import StrictModel


# --- Shared debate models ---

class DebateChallenge(StrictModel):
    """A challenge raised by the Challenger agent."""

    challenge_id: str = Field(..., description="Unique identifier")
    challenge_type: Literal[
        "factual_accuracy",
        "logical_flaw",
        "missing_evidence",
        "alternative_explanation",
        "overconfidence",
        "bias_detected",
        "causal_gap",
        "source_reliability",
    ] = Field(..., description="Type of challenge")
    target_claim: str = Field(..., description="The claim being challenged")
    challenge_text: str = Field(
        ...,
        min_length=50,
        description="The challenge explanation",
    )
    severity: Literal["low", "medium", "high", "critical"] = Field(
        ...,
        description="Severity of the issue",
    )
    evidence_requested: list[str] = Field(
        default_factory=list,
        description="Evidence that would address this",
    )


class AdvocateResponse(StrictModel):
    """Response from the Advocate agent."""

    challenge_id: str = Field(..., description="ID of challenge being addressed")
    response_type: Literal[
        "defend",
        "acknowledge",
        "partial_concede",
        "full_concede",
    ] = Field(..., description="Type of response")
    response_text: str = Field(
        ...,
        min_length=50,
        description="The response",
    )
    evidence_provided: list[str] = Field(
        default_factory=list,
        description="Evidence supporting defense",
    )
    suggested_modification: str | None = Field(
        default=None,
        description="Suggested change if acknowledging issue",
    )


class JudgeRuling(StrictModel):
    """Ruling from the Judge agent."""

    challenge_id: str = Field(..., description="Challenge being ruled on")
    ruling: Literal[
        "challenge_sustained",
        "challenge_overruled",
        "partial_sustain",
    ] = Field(..., description="The ruling")
    reasoning: str = Field(
        ...,
        min_length=50,
        description="Reasoning for the ruling",
    )
    required_action: Literal[
        "no_change",
        "minor_revision",
        "significant_revision",
        "remove_claim",
    ] = Field(..., description="Action required")
    action_details: str | None = Field(
        default=None,
        description="Specific changes needed",
    )


class DebateRound(StrictModel):
    """A complete debate round."""

    round_number: int = Field(..., ge=1)
    challenge: DebateChallenge
    response: AdvocateResponse
    ruling: JudgeRuling


class DebateSummary(StrictModel):
    """Summary of the complete debate."""

    total_rounds: int = Field(..., ge=0)
    challenges_sustained: int = Field(..., ge=0)
    challenges_overruled: int = Field(..., ge=0)
    challenges_partial: int = Field(..., ge=0)
    required_modifications: list[str] = Field(default_factory=list)
    analysis_strengthened: bool = Field(...)
    final_confidence_adjustment: float = Field(..., ge=-0.5, le=0.2)
    key_insights_from_debate: list[str] = Field(default_factory=list)


# --- Challenger Agent ---

class ChallengerInput(StrictModel):
    """Input for Challenger agent."""

    analysis_summary: str = Field(
        ...,
        min_length=100,
        description="Summary of analysis to challenge",
    )
    key_claims: list[str] = Field(
        ...,
        min_length=1,
        description="Key claims to scrutinize",
    )
    motivation_synthesis: str = Field(
        default="",
        description="Motivation analysis if available",
    )
    chains_synthesis: str = Field(
        default="",
        description="Chains analysis if available",
    )
    prior_challenges: list[DebateChallenge] = Field(
        default_factory=list,
        description="Previous challenges (for continuation)",
    )


class ChallengerOutput(StrictModel):
    """Output from Challenger agent."""

    challenges: list[DebateChallenge] = Field(default_factory=list)
    overall_assessment: str = Field(
        ...,
        min_length=50,
        description="Overall assessment of analysis quality",
    )
    analysis_strength_rating: float = Field(
        ...,
        ge=0,
        le=1,
        description="How strong the analysis appears",
    )


# --- Advocate Agent ---

class AdvocateInput(StrictModel):
    """Input for Advocate agent."""

    original_analysis: str = Field(
        ...,
        min_length=100,
        description="The original analysis being defended",
    )
    challenge: DebateChallenge = Field(
        ...,
        description="The challenge to respond to",
    )
    available_evidence: list[str] = Field(
        default_factory=list,
        description="Additional evidence available",
    )


class AdvocateOutput(StrictModel):
    """Output from Advocate agent."""

    response: AdvocateResponse = Field(..., description="The response")
    defense_strength: float = Field(
        ...,
        ge=0,
        le=1,
        description="Strength of the defense",
    )


# --- Judge Agent ---

class JudgeInput(StrictModel):
    """Input for Judge agent."""

    original_claim: str = Field(
        ...,
        description="The original claim under dispute",
    )
    challenge: DebateChallenge = Field(
        ...,
        description="The challenge raised",
    )
    response: AdvocateResponse = Field(
        ...,
        description="The advocate's response",
    )
    context: str = Field(
        default="",
        description="Additional context",
    )


class JudgeOutput(StrictModel):
    """Output from Judge agent."""

    ruling: JudgeRuling = Field(..., description="The ruling")
    confidence_in_ruling: float = Field(
        ...,
        ge=0,
        le=1,
        description="Judge's confidence",
    )
