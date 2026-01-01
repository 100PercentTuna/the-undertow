"""
Story processor for converting ingested content to Story models.
"""

import hashlib
from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from undertow.config import settings
from undertow.ingestion.fetchers.rss import FeedEntry
from undertow.ingestion.fetchers.web import WebContent, WebFetcher
from undertow.models.story import Story, StoryStatus, Zone

logger = structlog.get_logger()


class StoryProcessor:
    """
    Processes feed entries into Story models.
    
    Handles:
    - Deduplication
    - Content enrichment
    - Zone classification
    - Initial scoring
    """

    def __init__(self) -> None:
        """Initialize story processor."""
        self.web_fetcher = WebFetcher()
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    async def _get_session(self) -> AsyncSession:
        """Get database session."""
        if self._session_factory is None:
            engine = create_async_engine(settings.database_url)
            self._session_factory = async_sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
        return self._session_factory()

    async def process(
        self,
        entry: FeedEntry,
        zone_hint: str | None = None,
    ) -> Story | None:
        """
        Process a feed entry into a Story.
        
        Args:
            entry: Feed entry to process
            zone_hint: Optional zone hint from feed configuration
            
        Returns:
            Created Story or None if duplicate/invalid
        """
        logger.debug("Processing entry", title=entry.title[:50])
        
        async with await self._get_session() as session:
            # Check for duplicate
            if await self._is_duplicate(session, entry.link):
                logger.debug("Duplicate entry", url=entry.link)
                return None
            
            # Fetch full content if summary is short
            content = entry.summary
            if len(content) < 500 and entry.link:
                try:
                    web_content = await self.web_fetcher.fetch(entry.link)
                    if web_content.success and web_content.content:
                        content = web_content.content
                except Exception as e:
                    logger.warning("Failed to fetch full content", error=str(e))
            
            # Determine zone
            zone = self._classify_zone(entry, zone_hint)
            
            # Calculate initial scores
            relevance = self._score_relevance(entry, content)
            importance = self._score_importance(entry, content)
            
            # Create story
            story = Story(
                headline=entry.title[:500],
                summary=entry.summary[:5000],
                content=content[:50000],
                source_name=entry.source_name,
                source_url=entry.link,
                source_published_at=entry.published,
                primary_zone=zone,
                status=StoryStatus.PENDING,
                relevance_score=relevance,
                importance_score=importance,
                themes=entry.categories or [],
            )
            
            session.add(story)
            await session.commit()
            await session.refresh(story)
            
            logger.info(
                "Story created",
                story_id=story.id,
                headline=story.headline[:50],
                zone=zone.value,
            )
            
            return story

    async def _is_duplicate(self, session: AsyncSession, url: str) -> bool:
        """Check if URL already exists in database."""
        query = select(Story.id).where(Story.source_url == url)
        result = await session.execute(query)
        return result.scalar_one_or_none() is not None

    def _classify_zone(
        self,
        entry: FeedEntry,
        zone_hint: str | None,
    ) -> Zone:
        """
        Classify story into a zone.
        
        Uses zone hint if provided, otherwise attempts classification.
        """
        # If zone hint provided, try to match
        if zone_hint:
            try:
                return Zone(zone_hint)
            except ValueError:
                pass
        
        # Keyword-based classification (simplified)
        # In production, this would use NLP or the LLM
        text = f"{entry.title} {entry.summary}".lower()
        
        zone_keywords = {
            Zone.USA: ["united states", "america", "washington", "biden", "trump", "congress"],
            Zone.CHINA: ["china", "beijing", "xi jinping", "chinese"],
            Zone.RUSSIA_CORE: ["russia", "moscow", "putin", "kremlin"],
            Zone.LEVANT: ["syria", "lebanon", "jordan", "israel", "palestine", "gaza"],
            Zone.GULF_GCC: ["saudi", "uae", "qatar", "gulf", "bahrain", "kuwait"],
            Zone.IRAN: ["iran", "tehran", "khamenei"],
            Zone.TURKEY: ["turkey", "ankara", "erdogan"],
            Zone.INDIA: ["india", "modi", "delhi", "indian"],
            Zone.WESTERN_EUROPE: ["france", "germany", "eu", "european union", "brussels"],
            Zone.HORN_OF_AFRICA: ["ethiopia", "somalia", "eritrea", "djibouti"],
            Zone.SAHEL: ["mali", "niger", "burkina", "sahel"],
        }
        
        for zone, keywords in zone_keywords.items():
            if any(kw in text for kw in keywords):
                return zone
        
        # Default to USA if no match
        return Zone.USA

    def _score_relevance(self, entry: FeedEntry, content: str) -> float:
        """
        Calculate relevance score.
        
        Based on content quality indicators.
        """
        score = 0.5  # Base score
        
        # Content length bonus
        word_count = len(content.split())
        if word_count > 500:
            score += 0.1
        if word_count > 1000:
            score += 0.1
        
        # Has summary
        if entry.summary and len(entry.summary) > 100:
            score += 0.1
        
        # Has published date
        if entry.published:
            score += 0.1
        
        # Has categories
        if entry.categories:
            score += 0.1
        
        return min(1.0, score)

    def _score_importance(self, entry: FeedEntry, content: str) -> float:
        """
        Calculate importance score.
        
        Based on geopolitical significance indicators.
        """
        score = 0.5  # Base score
        
        text = f"{entry.title} {content}".lower()
        
        # High-importance keywords
        high_importance = [
            "war", "invasion", "military", "nuclear",
            "sanction", "crisis", "coup", "election",
            "treaty", "summit", "agreement", "alliance",
        ]
        
        matches = sum(1 for kw in high_importance if kw in text)
        score += min(0.3, matches * 0.1)
        
        # Named entity bonus (simplified)
        leaders = ["president", "minister", "leader", "general"]
        if any(leader in text for leader in leaders):
            score += 0.1
        
        return min(1.0, score)

