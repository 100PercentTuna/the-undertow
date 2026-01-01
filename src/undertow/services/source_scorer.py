"""
Source quality scoring service.

Evaluates and tracks source reliability.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import structlog

from undertow.infrastructure.cache import get_cache

logger = structlog.get_logger()


class SourceTier(str, Enum):
    """Source reliability tiers."""

    TIER_1 = "tier_1"  # Primary authoritative sources (FT, Reuters, etc.)
    TIER_2 = "tier_2"  # Reputable regional sources
    TIER_3 = "tier_3"  # General news sources
    TIER_4 = "tier_4"  # Opinion/analysis sites
    UNRATED = "unrated"


class BiasIndicator(str, Enum):
    """Bias indicators."""

    STATE_MEDIA = "state_media"
    CORPORATE = "corporate"
    PARTISAN = "partisan"
    INDEPENDENT = "independent"
    UNKNOWN = "unknown"


@dataclass
class SourceProfile:
    """Profile for a news source."""

    domain: str
    name: str
    tier: SourceTier
    bias: BiasIndicator
    regions: list[str]  # Zones this source covers well
    languages: list[str]
    requires_subscription: bool = False
    notes: str = ""

    # Calculated scores
    reliability_score: float = 0.8
    timeliness_score: float = 0.8
    depth_score: float = 0.8


@dataclass
class SourceScore:
    """Calculated score for a source."""

    domain: str
    overall_score: float
    reliability: float
    timeliness: float
    depth: float
    sample_size: int
    last_updated: datetime


# Known source profiles - comprehensive list for all 42 zones
SOURCE_PROFILES: dict[str, SourceProfile] = {
    # ========================================================================
    # TIER 1 - Primary Authoritative (Global)
    # ========================================================================
    "ft.com": SourceProfile(
        domain="ft.com",
        name="Financial Times",
        tier=SourceTier.TIER_1,
        bias=BiasIndicator.CORPORATE,
        regions=["western_europe", "usa", "china", "global"],
        languages=["en"],
        requires_subscription=True,
        reliability_score=0.95,
        depth_score=0.90,
    ),
    "reuters.com": SourceProfile(
        domain="reuters.com",
        name="Reuters",
        tier=SourceTier.TIER_1,
        bias=BiasIndicator.INDEPENDENT,
        regions=["global"],
        languages=["en"],
        reliability_score=0.95,
        timeliness_score=0.95,
    ),
    "economist.com": SourceProfile(
        domain="economist.com",
        name="The Economist",
        tier=SourceTier.TIER_1,
        bias=BiasIndicator.CORPORATE,
        regions=["global"],
        languages=["en"],
        requires_subscription=True,
        reliability_score=0.92,
        depth_score=0.95,
    ),
    "foreignaffairs.com": SourceProfile(
        domain="foreignaffairs.com",
        name="Foreign Affairs",
        tier=SourceTier.TIER_1,
        bias=BiasIndicator.INDEPENDENT,
        regions=["global"],
        languages=["en"],
        depth_score=0.98,
        timeliness_score=0.60,
    ),
    "apnews.com": SourceProfile(
        domain="apnews.com",
        name="Associated Press",
        tier=SourceTier.TIER_1,
        bias=BiasIndicator.INDEPENDENT,
        regions=["global"],
        languages=["en"],
        reliability_score=0.94,
        timeliness_score=0.95,
    ),
    
    # ========================================================================
    # AFRICA - Tier 1/2
    # ========================================================================
    "africaconfidential.com": SourceProfile(
        domain="africaconfidential.com",
        name="Africa Confidential",
        tier=SourceTier.TIER_1,
        bias=BiasIndicator.INDEPENDENT,
        regions=["horn_of_africa", "east_africa", "west_africa", "sahel", "southern_africa", "great_lakes"],
        languages=["en"],
        requires_subscription=True,
        reliability_score=0.95,
        depth_score=0.95,
        notes="Essential for African politics",
    ),
    "thecontinent.org": SourceProfile(
        domain="thecontinent.org",
        name="The Continent",
        tier=SourceTier.TIER_2,
        bias=BiasIndicator.INDEPENDENT,
        regions=["horn_of_africa", "east_africa", "west_africa", "southern_africa"],
        languages=["en"],
        reliability_score=0.85,
    ),
    "dailymaverick.co.za": SourceProfile(
        domain="dailymaverick.co.za",
        name="Daily Maverick",
        tier=SourceTier.TIER_1,
        bias=BiasIndicator.INDEPENDENT,
        regions=["southern_africa"],
        languages=["en"],
        reliability_score=0.90,
        notes="Essential for South Africa",
    ),
    "addisstandard.com": SourceProfile(
        domain="addisstandard.com",
        name="Addis Standard",
        tier=SourceTier.TIER_2,
        bias=BiasIndicator.INDEPENDENT,
        regions=["horn_of_africa"],
        languages=["en"],
        reliability_score=0.82,
    ),
    
    # ========================================================================
    # MIDDLE EAST & NORTH AFRICA
    # ========================================================================
    "aljazeera.com": SourceProfile(
        domain="aljazeera.com",
        name="Al Jazeera",
        tier=SourceTier.TIER_2,
        bias=BiasIndicator.STATE_MEDIA,
        regions=["gulf_gcc", "levant", "maghreb"],
        languages=["en", "ar"],
        notes="Qatar state-funded, good MENA coverage",
        reliability_score=0.75,
        depth_score=0.85,
    ),
    "al-monitor.com": SourceProfile(
        domain="al-monitor.com",
        name="Al-Monitor",
        tier=SourceTier.TIER_1,
        bias=BiasIndicator.INDEPENDENT,
        regions=["levant", "gulf_gcc", "turkey", "iran", "iraq"],
        languages=["en"],
        reliability_score=0.88,
        depth_score=0.90,
    ),
    "middleeasteye.net": SourceProfile(
        domain="middleeasteye.net",
        name="Middle East Eye",
        tier=SourceTier.TIER_2,
        bias=BiasIndicator.PARTISAN,
        regions=["levant", "gulf_gcc", "maghreb"],
        languages=["en"],
        reliability_score=0.75,
        notes="Qatar-linked, critical of Saudi/UAE",
    ),
    "amwaj.media": SourceProfile(
        domain="amwaj.media",
        name="Amwaj.media",
        tier=SourceTier.TIER_1,
        bias=BiasIndicator.INDEPENDENT,
        regions=["iran", "gulf_gcc", "iraq"],
        languages=["en"],
        reliability_score=0.90,
        depth_score=0.92,
        notes="Essential for Iran and Gulf",
    ),
    "972mag.com": SourceProfile(
        domain="972mag.com",
        name="+972 Magazine",
        tier=SourceTier.TIER_2,
        bias=BiasIndicator.PARTISAN,
        regions=["levant"],
        languages=["en"],
        reliability_score=0.78,
        notes="Israeli-Palestinian, left perspective",
    ),
    
    # ========================================================================
    # RUSSIA & EURASIA
    # ========================================================================
    "meduza.io": SourceProfile(
        domain="meduza.io",
        name="Meduza",
        tier=SourceTier.TIER_2,
        bias=BiasIndicator.INDEPENDENT,
        regions=["russia_core", "eastern_europe"],
        languages=["en", "ru"],
        notes="Independent Russian media in exile",
        reliability_score=0.88,
    ),
    "themoscowtimes.com": SourceProfile(
        domain="themoscowtimes.com",
        name="The Moscow Times",
        tier=SourceTier.TIER_2,
        bias=BiasIndicator.INDEPENDENT,
        regions=["russia_core"],
        languages=["en"],
        reliability_score=0.82,
        notes="In exile since 2022",
    ),
    "eurasianet.org": SourceProfile(
        domain="eurasianet.org",
        name="Eurasianet",
        tier=SourceTier.TIER_1,
        bias=BiasIndicator.INDEPENDENT,
        regions=["central_asia_west", "central_asia_east", "south_caucasus"],
        languages=["en"],
        reliability_score=0.90,
        depth_score=0.88,
        notes="Essential for Central Asia and Caucasus",
    ),
    "ocmedia.org": SourceProfile(
        domain="ocmedia.org",
        name="OC Media",
        tier=SourceTier.TIER_2,
        bias=BiasIndicator.INDEPENDENT,
        regions=["south_caucasus"],
        languages=["en"],
        reliability_score=0.85,
        notes="Excellent for Caucasus",
    ),
    
    # ========================================================================
    # ASIA
    # ========================================================================
    "scmp.com": SourceProfile(
        domain="scmp.com",
        name="South China Morning Post",
        tier=SourceTier.TIER_2,
        bias=BiasIndicator.CORPORATE,
        regions=["china", "maritime_sea", "mainland_sea"],
        languages=["en"],
        notes="Alibaba-owned, China expertise",
        reliability_score=0.80,
    ),
    "nikkei.com": SourceProfile(
        domain="nikkei.com",
        name="Nikkei Asia",
        tier=SourceTier.TIER_1,
        bias=BiasIndicator.CORPORATE,
        regions=["japan", "korea", "mainland_sea", "maritime_sea", "china"],
        languages=["en", "ja"],
        reliability_score=0.90,
    ),
    "frontier-myanmar.net": SourceProfile(
        domain="frontier-myanmar.net",
        name="Frontier Myanmar",
        tier=SourceTier.TIER_1,
        bias=BiasIndicator.INDEPENDENT,
        regions=["mainland_sea"],
        languages=["en"],
        reliability_score=0.88,
        notes="Essential for Myanmar",
    ),
    "thediplomat.com": SourceProfile(
        domain="thediplomat.com",
        name="The Diplomat",
        tier=SourceTier.TIER_2,
        bias=BiasIndicator.INDEPENDENT,
        regions=["china", "japan", "korea", "mainland_sea", "maritime_sea", "india"],
        languages=["en"],
        reliability_score=0.82,
        depth_score=0.85,
    ),
    "hindustantimes.com": SourceProfile(
        domain="hindustantimes.com",
        name="Hindustan Times",
        tier=SourceTier.TIER_2,
        bias=BiasIndicator.CORPORATE,
        regions=["india", "pakistan_afghanistan"],
        languages=["en"],
        reliability_score=0.75,
    ),
    "dawn.com": SourceProfile(
        domain="dawn.com",
        name="Dawn",
        tier=SourceTier.TIER_1,
        bias=BiasIndicator.INDEPENDENT,
        regions=["pakistan_afghanistan"],
        languages=["en"],
        reliability_score=0.88,
        notes="Essential for Pakistan",
    ),
    "nknews.org": SourceProfile(
        domain="nknews.org",
        name="NK News",
        tier=SourceTier.TIER_1,
        bias=BiasIndicator.INDEPENDENT,
        regions=["korea"],
        languages=["en"],
        requires_subscription=True,
        reliability_score=0.90,
        notes="Essential for North Korea",
    ),
    
    # ========================================================================
    # EUROPE
    # ========================================================================
    "bbc.com": SourceProfile(
        domain="bbc.com",
        name="BBC",
        tier=SourceTier.TIER_2,
        bias=BiasIndicator.INDEPENDENT,
        regions=["british_isles", "global"],
        languages=["en"],
        reliability_score=0.85,
    ),
    "theguardian.com": SourceProfile(
        domain="theguardian.com",
        name="The Guardian",
        tier=SourceTier.TIER_2,
        bias=BiasIndicator.PARTISAN,
        regions=["british_isles", "australia_nz"],
        languages=["en"],
        reliability_score=0.80,
    ),
    "politico.eu": SourceProfile(
        domain="politico.eu",
        name="Politico Europe",
        tier=SourceTier.TIER_1,
        bias=BiasIndicator.INDEPENDENT,
        regions=["western_europe", "central_europe"],
        languages=["en"],
        reliability_score=0.88,
    ),
    "balkaninsight.com": SourceProfile(
        domain="balkaninsight.com",
        name="Balkan Insight (BIRN)",
        tier=SourceTier.TIER_1,
        bias=BiasIndicator.INDEPENDENT,
        regions=["western_balkans"],
        languages=["en"],
        reliability_score=0.90,
        notes="Essential for Balkans investigative journalism",
    ),
    "kyivindependent.com": SourceProfile(
        domain="kyivindependent.com",
        name="Kyiv Independent",
        tier=SourceTier.TIER_2,
        bias=BiasIndicator.INDEPENDENT,
        regions=["eastern_europe"],
        languages=["en"],
        reliability_score=0.82,
        notes="Founded by former Kyiv Post journalists",
    ),
    
    # ========================================================================
    # AMERICAS
    # ========================================================================
    "americasquarterly.org": SourceProfile(
        domain="americasquarterly.org",
        name="Americas Quarterly",
        tier=SourceTier.TIER_1,
        bias=BiasIndicator.INDEPENDENT,
        regions=["andean", "southern_cone", "mexico_central_america", "caribbean"],
        languages=["en"],
        reliability_score=0.88,
        depth_score=0.90,
    ),
    "insightcrime.org": SourceProfile(
        domain="insightcrime.org",
        name="InSight Crime",
        tier=SourceTier.TIER_1,
        bias=BiasIndicator.INDEPENDENT,
        regions=["andean", "mexico_central_america"],
        languages=["en", "es"],
        reliability_score=0.90,
        notes="Essential for organized crime in Latin America",
    ),
    
    # ========================================================================
    # PACIFIC
    # ========================================================================
    "lowyinstitute.org": SourceProfile(
        domain="lowyinstitute.org",
        name="The Interpreter (Lowy)",
        tier=SourceTier.TIER_1,
        bias=BiasIndicator.INDEPENDENT,
        regions=["australia_nz", "pacific_islands", "maritime_sea"],
        languages=["en"],
        reliability_score=0.90,
        depth_score=0.92,
        notes="Essential for Pacific and Australia",
    ),
    "aspistrategist.org.au": SourceProfile(
        domain="aspistrategist.org.au",
        name="The Strategist (ASPI)",
        tier=SourceTier.TIER_1,
        bias=BiasIndicator.INDEPENDENT,
        regions=["australia_nz", "china", "pacific_islands"],
        languages=["en"],
        reliability_score=0.88,
    ),
    
    # ========================================================================
    # THINK TANKS & ANALYSIS
    # ========================================================================
    "crisisgroup.org": SourceProfile(
        domain="crisisgroup.org",
        name="International Crisis Group",
        tier=SourceTier.TIER_1,
        bias=BiasIndicator.INDEPENDENT,
        regions=["global"],
        languages=["en"],
        reliability_score=0.92,
        depth_score=0.95,
        timeliness_score=0.70,
        notes="Essential for conflict analysis",
    ),
    "carnegieendowment.org": SourceProfile(
        domain="carnegieendowment.org",
        name="Carnegie Endowment",
        tier=SourceTier.TIER_1,
        bias=BiasIndicator.INDEPENDENT,
        regions=["global", "russia_core", "china", "india"],
        languages=["en"],
        reliability_score=0.90,
        depth_score=0.92,
    ),
    "csis.org": SourceProfile(
        domain="csis.org",
        name="CSIS",
        tier=SourceTier.TIER_1,
        bias=BiasIndicator.INDEPENDENT,
        regions=["global", "usa", "china"],
        languages=["en"],
        reliability_score=0.88,
        depth_score=0.90,
    ),
}


class SourceScorer:
    """
    Service for scoring source quality.

    Tracks source reliability over time and provides
    scoring for claim verification.
    """

    CACHE_PREFIX = "source_score:"
    CACHE_TTL = 86400  # 24 hours

    def __init__(self) -> None:
        """Initialize source scorer."""
        self._cache = get_cache()
        self._profiles = SOURCE_PROFILES.copy()

    def get_profile(self, domain: str) -> SourceProfile | None:
        """
        Get source profile by domain.

        Args:
            domain: Source domain (e.g., 'ft.com')

        Returns:
            SourceProfile or None if unknown
        """
        # Normalize domain
        domain = domain.lower().strip()
        if domain.startswith("www."):
            domain = domain[4:]

        return self._profiles.get(domain)

    def get_tier(self, domain: str) -> SourceTier:
        """Get source tier."""
        profile = self.get_profile(domain)
        return profile.tier if profile else SourceTier.UNRATED

    def score_source(self, domain: str) -> SourceScore:
        """
        Calculate overall score for a source.

        Args:
            domain: Source domain

        Returns:
            SourceScore with overall and component scores
        """
        profile = self.get_profile(domain)

        if profile:
            # Use profile scores
            overall = (
                profile.reliability_score * 0.5
                + profile.timeliness_score * 0.25
                + profile.depth_score * 0.25
            )

            return SourceScore(
                domain=domain,
                overall_score=round(overall, 3),
                reliability=profile.reliability_score,
                timeliness=profile.timeliness_score,
                depth=profile.depth_score,
                sample_size=1000,  # Known source
                last_updated=datetime.utcnow(),
            )
        else:
            # Unknown source - conservative default
            return SourceScore(
                domain=domain,
                overall_score=0.5,
                reliability=0.5,
                timeliness=0.5,
                depth=0.5,
                sample_size=0,
                last_updated=datetime.utcnow(),
            )

    def score_for_zone(self, domain: str, zone: str) -> float:
        """
        Score a source for a specific zone.

        Sources get bonus for covering that zone.

        Args:
            domain: Source domain
            zone: Zone ID

        Returns:
            Score 0-1, higher for sources that cover this zone
        """
        profile = self.get_profile(domain)

        if not profile:
            return 0.5

        base_score = self.score_source(domain).overall_score

        # Bonus for zone coverage
        if zone in profile.regions or "global" in profile.regions:
            return min(1.0, base_score + 0.1)

        return base_score

    def is_state_media(self, domain: str) -> bool:
        """Check if source is state media."""
        profile = self.get_profile(domain)
        return profile.bias == BiasIndicator.STATE_MEDIA if profile else False

    def requires_triangulation(self, domain: str) -> bool:
        """
        Check if source requires triangulation.

        State media and partisan sources require verification
        from independent sources.
        """
        profile = self.get_profile(domain)

        if not profile:
            return True  # Unknown sources always need triangulation

        return profile.bias in [BiasIndicator.STATE_MEDIA, BiasIndicator.PARTISAN]

    def get_sources_for_zone(self, zone: str) -> list[SourceProfile]:
        """
        Get recommended sources for a zone.

        Args:
            zone: Zone ID

        Returns:
            List of source profiles covering that zone
        """
        sources = []

        for profile in self._profiles.values():
            if zone in profile.regions or "global" in profile.regions:
                sources.append(profile)

        # Sort by reliability
        sources.sort(key=lambda s: s.reliability_score, reverse=True)

        return sources

    def get_all_profiles(self) -> list[SourceProfile]:
        """Get all source profiles."""
        return list(self._profiles.values())

    def add_profile(self, profile: SourceProfile) -> None:
        """Add or update a source profile."""
        self._profiles[profile.domain] = profile


# Global instance
_source_scorer: SourceScorer | None = None


def get_source_scorer() -> SourceScorer:
    """Get global source scorer instance."""
    global _source_scorer
    if _source_scorer is None:
        _source_scorer = SourceScorer()
    return _source_scorer

