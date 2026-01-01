"""
Story repository for database operations.
"""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from undertow.models.story import Story, StoryStatus, Zone
from undertow.repositories.base import BaseRepository


class StoryRepository(BaseRepository[Story]):
    """
    Repository for Story operations.

    Provides specialized queries for story management.
    """

    model = Story

    async def get_by_url(self, url: str) -> Story | None:
        """
        Get story by source URL.

        Args:
            url: Source URL

        Returns:
            Story or None
        """
        query = select(Story).where(Story.source_url == url)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_by_status(
        self,
        status: StoryStatus,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Story]:
        """
        List stories by status.

        Args:
            status: Story status
            offset: Pagination offset
            limit: Maximum results

        Returns:
            List of stories
        """
        query = (
            select(Story)
            .where(Story.status == status)
            .order_by(Story.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_by_zone(
        self,
        zone: Zone,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Story]:
        """
        List stories by zone.

        Args:
            zone: Primary zone
            offset: Pagination offset
            limit: Maximum results

        Returns:
            List of stories
        """
        query = (
            select(Story)
            .where(Story.primary_zone == zone)
            .order_by(Story.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_pending_for_analysis(
        self,
        limit: int = 10,
        min_relevance: float = 0.0,
    ) -> list[Story]:
        """
        Get pending stories ready for analysis.

        Args:
            limit: Maximum stories to return
            min_relevance: Minimum relevance score

        Returns:
            List of pending stories ordered by relevance
        """
        query = (
            select(Story)
            .where(
                and_(
                    Story.status == StoryStatus.PENDING,
                    Story.relevance_score >= min_relevance,
                )
            )
            .order_by(
                Story.relevance_score.desc().nulls_last(),
                Story.importance_score.desc().nulls_last(),
            )
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_recent(
        self,
        hours: int = 24,
        limit: int = 100,
    ) -> list[Story]:
        """
        Get stories from the last N hours.

        Args:
            hours: Hours to look back
            limit: Maximum results

        Returns:
            Recent stories
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        query = (
            select(Story)
            .where(Story.created_at >= cutoff)
            .order_by(Story.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_status(self) -> dict[str, int]:
        """
        Count stories by status.

        Returns:
            Dict mapping status to count
        """
        query = (
            select(Story.status, func.count())
            .group_by(Story.status)
        )
        result = await self.session.execute(query)
        return {row[0].value: row[1] for row in result}

    async def count_by_zone(self) -> dict[str, int]:
        """
        Count stories by zone.

        Returns:
            Dict mapping zone to count
        """
        query = (
            select(Story.primary_zone, func.count())
            .group_by(Story.primary_zone)
        )
        result = await self.session.execute(query)
        return {row[0].value: row[1] for row in result}

    async def update_status(self, story_id: str, status: StoryStatus) -> Story | None:
        """
        Update story status.

        Args:
            story_id: Story ID
            status: New status

        Returns:
            Updated story or None
        """
        story = await self.get(story_id)
        if story:
            story.status = status
            await self.session.flush()
            return story
        return None

    async def update_analysis(
        self,
        story_id: str,
        analysis_data: dict[str, Any],
    ) -> Story | None:
        """
        Update story with analysis results.

        Args:
            story_id: Story ID
            analysis_data: Analysis data to store

        Returns:
            Updated story or None
        """
        story = await self.get(story_id)
        if story:
            # Merge with existing analysis data
            existing = story.analysis_data or {}
            existing.update(analysis_data)
            story.analysis_data = existing
            story.status = StoryStatus.ANALYZED
            await self.session.flush()
            return story
        return None

    async def search(
        self,
        query_text: str,
        limit: int = 20,
    ) -> list[Story]:
        """
        Search stories by headline/summary.

        Note: For production, use full-text search or vector similarity.

        Args:
            query_text: Search query
            limit: Maximum results

        Returns:
            Matching stories
        """
        # Simple ILIKE search - production should use FTS
        pattern = f"%{query_text}%"
        query = (
            select(Story)
            .where(
                Story.headline.ilike(pattern)
                | Story.summary.ilike(pattern)
            )
            .order_by(Story.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

