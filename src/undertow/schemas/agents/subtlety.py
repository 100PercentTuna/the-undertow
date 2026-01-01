"""
Schemas for Subtlety Analysis Agent.

Decodes the five channels of diplomatic communication:
1. Signal in the action
2. Eloquent silence
3. Timing message
4. Choreography
5. Deniable communication
"""

from typing import Literal

from pydantic import Field

from undertow.schemas.base import StrictModel
from undertow.schemas.agents.motivation import StoryContext, AnalysisContext


class SignalAnalysis(StrictModel):
    """Analysis of the signal in the action."""

    intended_audiences: list[str] = Field(
        ...,
        min_length=1,
        description="Who is this really addressed to?",
    )
    norm_invoked_or_violated: str = Field(
        ...,
        min_length=20,
        description="What principle is being upheld or challenged?",
    )
    capability_demonstrated: str = Field(
        default="",
        description="What capability is being signaled?",
    )
    commitment_signaled: str = Field(
        default="",
        description="What commitment is being signaled?",
    )
    counterfactual_signal: str = Field(
        ...,
        min_length=20,
        description="What would it have meant NOT to do this?",
    )


class SilenceAnalysis(StrictModel):
    """Analysis of eloquent silences."""

    notable_non_commenters: list[str] = Field(
        default_factory=list,
        description="Major players who haven't commented",
    )
    significance_of_silence: str = Field(
        ...,
        min_length=30,
        description="What does the silence signify?",
    )
    missing_from_framing: list[str] = Field(
        default_factory=list,
        description="What's conspicuously absent from coverage?",
    )
    deflected_questions: list[str] = Field(
        default_factory=list,
        description="What questions are being evaded?",
    )


class TimingAnalysis(StrictModel):
    """Analysis of timing significance."""

    preceded_by: list[str] = Field(
        default_factory=list,
        description="What preceded this?",
    )
    followed_by: list[str] = Field(
        default_factory=list,
        description="What follows this?",
    )
    calendar_significance: str = Field(
        default="",
        description="Elections, summits, symbolic dates?",
    )
    sequence_position: Literal[
        "opening_move",
        "response",
        "escalation",
        "de-escalation",
        "culmination",
        "routine",
    ] = Field(..., description="Position in sequence")
    window_closing: bool = Field(
        default=False,
        description="Is there 'now or never' quality?",
    )
    timing_assessment: str = Field(
        ...,
        min_length=30,
        description="Why now specifically?",
    )


class ChoreographyAnalysis(StrictModel):
    """Analysis of staging and presentation."""

    venue_significance: str = Field(
        default="",
        description="Why this location?",
    )
    protocol_level: Literal[
        "head_of_state",
        "ministerial",
        "working_level",
        "unofficial",
    ] = Field(..., description="Level of engagement")
    visual_elements: list[str] = Field(
        default_factory=list,
        description="Notable visual staging choices",
    )
    domestic_framing: dict[str, str] = Field(
        default_factory=dict,
        description="How each side frames it domestically",
    )
    notable_inclusions: list[str] = Field(
        default_factory=list,
        description="Who else was present?",
    )
    notable_exclusions: list[str] = Field(
        default_factory=list,
        description="Who was notably absent?",
    )


class DeniableChannel(StrictModel):
    """A deniable communication channel."""

    channel_type: Literal[
        "unnamed_official",
        "sympathetic_media",
        "proxy_statement",
        "back_channel",
        "track_two",
    ] = Field(..., description="Type of deniable channel")
    source: str = Field(..., description="Source of communication")
    message: str = Field(..., min_length=20, description="The message conveyed")
    likely_authorization: Literal["high", "medium", "low", "unclear"] = Field(
        ...,
        description="Likelihood this was authorized",
    )


class SubtletySynthesis(StrictModel):
    """Synthesis of subtlety analysis."""

    primary_hidden_message: str = Field(
        ...,
        min_length=50,
        description="What's really being communicated?",
    )
    key_audiences_beyond_obvious: list[str] = Field(
        ...,
        min_length=1,
        description="Who else is being signaled to?",
    )
    what_silence_reveals: str = Field(
        ...,
        min_length=30,
        description="What the silences tell us",
    )
    timing_exploitation: str = Field(
        ...,
        min_length=30,
        description="How timing was exploited",
    )
    overall_sophistication: Literal["crude", "moderate", "sophisticated", "masterful"] = Field(
        ...,
        description="Sophistication of the diplomatic signaling",
    )
    confidence: float = Field(..., ge=0, le=1)


class SubtletyInput(StrictModel):
    """Input for Subtlety Analysis Agent."""

    story: StoryContext = Field(..., description="Story context")
    context: AnalysisContext = Field(
        default_factory=AnalysisContext,
        description="Analysis context",
    )
    public_statements: list[str] = Field(
        default_factory=list,
        description="Public statements to analyze",
    )
    media_coverage: list[str] = Field(
        default_factory=list,
        description="Media coverage to analyze",
    )


class SubtletyOutput(StrictModel):
    """Output from Subtlety Analysis Agent."""

    signal_analysis: SignalAnalysis = Field(
        ...,
        description="Signal in the action",
    )
    silence_analysis: SilenceAnalysis = Field(
        ...,
        description="Eloquent silences",
    )
    timing_analysis: TimingAnalysis = Field(
        ...,
        description="Timing significance",
    )
    choreography_analysis: ChoreographyAnalysis = Field(
        ...,
        description="Staging analysis",
    )
    deniable_channels: list[DeniableChannel] = Field(
        default_factory=list,
        description="Identified deniable communications",
    )
    synthesis: SubtletySynthesis = Field(
        ...,
        description="Overall synthesis",
    )

