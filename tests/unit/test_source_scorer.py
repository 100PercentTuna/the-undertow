"""
Unit tests for Source Scorer service.
"""

import pytest

from undertow.services.source_scorer import (
    SourceScorer,
    SourceProfile,
    SourceTier,
    BiasIndicator,
)


@pytest.fixture
def scorer() -> SourceScorer:
    """Create source scorer."""
    return SourceScorer()


class TestSourceScorer:
    """Tests for SourceScorer service."""

    def test_get_known_profile(self, scorer: SourceScorer) -> None:
        """Test getting known source profile."""
        profile = scorer.get_profile("ft.com")

        assert profile is not None
        assert profile.name == "Financial Times"
        assert profile.tier == SourceTier.TIER_1

    def test_get_unknown_profile(self, scorer: SourceScorer) -> None:
        """Test getting unknown source profile."""
        profile = scorer.get_profile("unknown-site.xyz")
        assert profile is None

    def test_normalize_domain(self, scorer: SourceScorer) -> None:
        """Test domain normalization."""
        # With www prefix
        profile = scorer.get_profile("www.ft.com")
        assert profile is not None
        assert profile.name == "Financial Times"

        # With uppercase
        profile = scorer.get_profile("FT.COM")
        assert profile is not None

    def test_get_tier(self, scorer: SourceScorer) -> None:
        """Test getting source tier."""
        assert scorer.get_tier("ft.com") == SourceTier.TIER_1
        assert scorer.get_tier("unknown.com") == SourceTier.UNRATED

    def test_score_known_source(self, scorer: SourceScorer) -> None:
        """Test scoring known source."""
        score = scorer.score_source("ft.com")

        assert score.overall_score > 0.8
        assert score.reliability == 0.95
        assert score.sample_size == 1000

    def test_score_unknown_source(self, scorer: SourceScorer) -> None:
        """Test scoring unknown source."""
        score = scorer.score_source("unknown-blog.com")

        assert score.overall_score == 0.5
        assert score.sample_size == 0

    def test_score_for_zone(self, scorer: SourceScorer) -> None:
        """Test zone-specific scoring."""
        # Africa Confidential should score high for African zones
        score_africa = scorer.score_for_zone("africaconfidential.com", "horn_of_africa")
        score_other = scorer.score_for_zone("africaconfidential.com", "china")

        assert score_africa > score_other

    def test_is_state_media(self, scorer: SourceScorer) -> None:
        """Test state media detection."""
        assert scorer.is_state_media("aljazeera.com")  # Qatar state-funded
        assert not scorer.is_state_media("ft.com")
        assert not scorer.is_state_media("unknown.com")

    def test_requires_triangulation(self, scorer: SourceScorer) -> None:
        """Test triangulation requirement."""
        # State media needs triangulation
        assert scorer.requires_triangulation("aljazeera.com")

        # Independent sources don't need triangulation
        assert not scorer.requires_triangulation("reuters.com")

        # Unknown sources always need triangulation
        assert scorer.requires_triangulation("random-blog.com")

    def test_get_sources_for_zone(self, scorer: SourceScorer) -> None:
        """Test getting sources for zone."""
        sources = scorer.get_sources_for_zone("horn_of_africa")

        assert len(sources) > 0
        # Africa Confidential should be in the list
        assert any(s.domain == "africaconfidential.com" for s in sources)

    def test_add_custom_profile(self, scorer: SourceScorer) -> None:
        """Test adding custom source profile."""
        custom = SourceProfile(
            domain="custom-source.com",
            name="Custom Source",
            tier=SourceTier.TIER_3,
            bias=BiasIndicator.INDEPENDENT,
            regions=["test_zone"],
            languages=["en"],
            reliability_score=0.75,
        )

        scorer.add_profile(custom)

        profile = scorer.get_profile("custom-source.com")
        assert profile is not None
        assert profile.name == "Custom Source"


class TestSourceProfile:
    """Tests for SourceProfile dataclass."""

    def test_profile_creation(self) -> None:
        """Test creating source profile."""
        profile = SourceProfile(
            domain="test.com",
            name="Test Source",
            tier=SourceTier.TIER_2,
            bias=BiasIndicator.PARTISAN,
            regions=["europe"],
            languages=["en", "de"],
        )

        assert profile.domain == "test.com"
        assert profile.reliability_score == 0.8  # Default
        assert profile.requires_subscription is False  # Default

    def test_profile_with_all_fields(self) -> None:
        """Test profile with all fields set."""
        profile = SourceProfile(
            domain="premium.com",
            name="Premium Source",
            tier=SourceTier.TIER_1,
            bias=BiasIndicator.CORPORATE,
            regions=["global"],
            languages=["en"],
            requires_subscription=True,
            notes="Excellent coverage",
            reliability_score=0.95,
            timeliness_score=0.90,
            depth_score=0.92,
        )

        assert profile.requires_subscription is True
        assert profile.notes == "Excellent coverage"
        assert profile.reliability_score == 0.95

