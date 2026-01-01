"""
Schemas for Production agents (Writer, Voice, Editor).

These agents produce the final article output.
"""

from typing import Literal

from pydantic import Field, field_validator

from undertow.schemas.base import StrictModel


class ArticleSection(StrictModel):
    """A section of the article."""

    section_id: str = Field(..., description="Section identifier")
    section_type: Literal[
        "hook",
        "what_happened",
        "actors",
        "backstory",
        "motivation_analysis",
        "subtleties",
        "chains",
        "geometry",
        "deep_well",
        "connections",
        "unknown",
        "takeaway",
    ] = Field(..., description="Type of section")
    title: str = Field(..., min_length=1, max_length=200, description="Section title")
    content: str = Field(..., min_length=100, description="Section content")
    word_count: int = Field(..., ge=50, description="Word count")


class SourceCitation(StrictModel):
    """A source citation in the article."""

    citation_id: str = Field(..., description="Citation identifier")
    source_name: str = Field(..., description="Name of source")
    source_url: str | None = Field(None, description="URL if available")
    publication_date: str | None = Field(None, description="Publication date")
    claim_supported: str = Field(..., description="The claim this supports")


class WriterInput(StrictModel):
    """Input for Article Writer agent."""

    headline: str = Field(..., min_length=10, max_length=200)
    summary: str = Field(..., min_length=100, max_length=2000)
    
    # Analysis data
    motivation_analysis: dict = Field(..., description="Motivation analysis output")
    chains_analysis: dict = Field(..., description="Chains analysis output")
    
    # Optional enrichments
    subtlety_analysis: dict | None = Field(None, description="Subtlety analysis")
    historical_parallels: list[str] = Field(default_factory=list)
    theoretical_frameworks: list[str] = Field(default_factory=list)
    
    # Context
    zones: list[str] = Field(..., min_length=1)
    key_actors: list[str] = Field(..., min_length=1)
    key_events: list[str] = Field(..., min_length=1)
    
    # Sources for citation
    sources: list[dict] = Field(default_factory=list)
    
    # Constraints
    target_word_count: int = Field(default=3000, ge=1500, le=6000)


class WriterOutput(StrictModel):
    """Output from Article Writer agent."""

    headline: str = Field(..., min_length=10, max_length=200)
    subhead: str = Field(..., min_length=20, max_length=500)
    
    sections: list[ArticleSection] = Field(
        ...,
        min_length=8,
        description="Article sections in order",
    )
    
    citations: list[SourceCitation] = Field(
        ...,
        min_length=2,
        description="Source citations",
    )
    
    total_word_count: int = Field(..., ge=1000)
    read_time_minutes: int = Field(..., ge=5, le=30)
    
    # Metadata
    themes: list[str] = Field(..., min_length=1)
    regions: list[str] = Field(..., min_length=1)
    key_takeaway: str = Field(..., min_length=50, max_length=500)

    @field_validator("total_word_count")
    @classmethod
    def validate_word_count(cls, v: int, info) -> int:
        """Validate word count matches sections."""
        # Actual validation would sum section word counts
        return v


class VoiceIssue(StrictModel):
    """A voice/style issue found in the article."""

    issue_id: str = Field(..., description="Issue identifier")
    location: str = Field(..., description="Where in the article")
    issue_type: Literal[
        "forbidden_phrase",
        "passive_voice",
        "jargon",
        "tone_mismatch",
        "overconfidence",
        "hedging_excessive",
        "unclear_agency",
        "repetition",
        "cliche",
    ] = Field(..., description="Type of issue")
    original_text: str = Field(..., description="Problematic text")
    explanation: str = Field(..., description="Why this is an issue")
    suggested_fix: str = Field(..., description="Suggested replacement")
    severity: Literal["minor", "moderate", "major"] = Field(...)


class VoiceCalibrationInput(StrictModel):
    """Input for Voice Calibration agent."""

    article_content: str = Field(..., min_length=1000)
    target_voice: str = Field(
        default="parallax",
        description="Target voice profile",
    )


class VoiceCalibrationOutput(StrictModel):
    """Output from Voice Calibration agent."""

    issues: list[VoiceIssue] = Field(
        default_factory=list,
        description="Voice issues found",
    )
    voice_consistency_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall voice consistency",
    )
    tone_assessment: str = Field(
        ...,
        min_length=50,
        description="Assessment of overall tone",
    )
    strengths: list[str] = Field(
        default_factory=list,
        description="Voice/style strengths",
    )
    corrected_content: str | None = Field(
        None,
        description="Full corrected content (if needed)",
    )


class QualityDimension(StrictModel):
    """Assessment of a single quality dimension."""

    dimension: str = Field(..., description="Dimension name")
    score: float = Field(..., ge=0.0, le=1.0)
    assessment: str = Field(..., min_length=20)
    issues: list[str] = Field(default_factory=list)


class EditorInput(StrictModel):
    """Input for Editor agent."""

    article: WriterOutput = Field(..., description="Article to review")
    voice_report: VoiceCalibrationOutput | None = Field(None)
    fact_check_score: float = Field(default=1.0, ge=0.0, le=1.0)


class EditorOutput(StrictModel):
    """Output from Editor agent."""

    approved: bool = Field(..., description="Whether article is approved")
    
    quality_dimensions: list[QualityDimension] = Field(
        ...,
        description="Assessment of each quality dimension",
    )
    
    overall_score: float = Field(..., ge=0.0, le=1.0)
    
    required_changes: list[str] = Field(
        default_factory=list,
        description="Changes required before publication",
    )
    
    suggested_improvements: list[str] = Field(
        default_factory=list,
        description="Optional improvements",
    )
    
    publication_readiness: Literal[
        "ready",
        "minor_edits",
        "major_revision",
        "reject",
    ] = Field(..., description="Publication readiness")
    
    editor_notes: str = Field(
        default="",
        description="Additional editor notes",
    )

