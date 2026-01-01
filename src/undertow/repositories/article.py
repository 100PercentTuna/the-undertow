"""
Article repository for database operations.
"""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from undertow.models.article import Article, ArticleStatus
from undertow.repositories.base import BaseRepository


class ArticleRepository(BaseRepository[Article]):
    """
    Repository for Article operations.

    Provides specialized queries for article management.
    """

    model = Article

    async def get_by_slug(self, slug: str) -> Article | None:
        """
        Get article by slug.

        Args:
            slug: Article slug

        Returns:
            Article or None
        """
        query = select(Article).where(Article.slug == slug)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_by_status(
        self,
        status: ArticleStatus,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Article]:
        """
        List articles by status.

        Args:
            status: Article status
            offset: Pagination offset
            limit: Maximum results

        Returns:
            List of articles
        """
        query = (
            select(Article)
            .where(Article.status == status)
            .order_by(Article.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_published(
        self,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Article]:
        """
        List published articles.

        Args:
            offset: Pagination offset
            limit: Maximum results

        Returns:
            List of published articles
        """
        query = (
            select(Article)
            .where(Article.status == ArticleStatus.PUBLISHED)
            .order_by(Article.published_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_for_newsletter(
        self,
        date: datetime | None = None,
        limit: int = 5,
    ) -> list[Article]:
        """
        Get articles for newsletter edition.

        Args:
            date: Edition date (default: today)
            limit: Maximum articles

        Returns:
            Articles for newsletter
        """
        if date is None:
            date = datetime.utcnow()

        # Get articles from the last 24 hours
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)

        query = (
            select(Article)
            .where(
                and_(
                    Article.status == ArticleStatus.PUBLISHED,
                    Article.published_at >= start,
                    Article.published_at < end,
                )
            )
            .order_by(Article.quality_score.desc().nulls_last())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_by_zone(
        self,
        zone: str,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Article]:
        """
        List articles by zone.

        Args:
            zone: Zone identifier
            offset: Pagination offset
            limit: Maximum results

        Returns:
            Articles in zone
        """
        query = (
            select(Article)
            .where(Article.zones.contains([zone]))
            .order_by(Article.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_status(self) -> dict[str, int]:
        """
        Count articles by status.

        Returns:
            Dict mapping status to count
        """
        query = (
            select(Article.status, func.count())
            .group_by(Article.status)
        )
        result = await self.session.execute(query)
        return {row[0].value: row[1] for row in result}

    async def update_status(
        self,
        article_id: str,
        status: ArticleStatus,
    ) -> Article | None:
        """
        Update article status.

        Args:
            article_id: Article ID
            status: New status

        Returns:
            Updated article or None
        """
        article = await self.get(article_id)
        if article:
            article.status = status
            if status == ArticleStatus.PUBLISHED:
                article.published_at = datetime.utcnow()
            await self.session.flush()
            return article
        return None

    async def get_ready_for_review(self, limit: int = 20) -> list[Article]:
        """
        Get articles ready for editorial review.

        Args:
            limit: Maximum results

        Returns:
            Articles needing review
        """
        query = (
            select(Article)
            .where(
                Article.status.in_([ArticleStatus.DRAFT, ArticleStatus.REVIEW])
            )
            .order_by(Article.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_stats(self) -> dict[str, Any]:
        """
        Get article statistics.

        Returns:
            Statistics dict
        """
        # Count by status
        status_counts = await self.count_by_status()

        # Average quality score
        avg_query = select(func.avg(Article.quality_score)).where(
            Article.quality_score.isnot(None)
        )
        avg_result = await self.session.execute(avg_query)
        avg_quality = avg_result.scalar() or 0

        # Published today
        today_start = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        today_query = select(func.count()).select_from(Article).where(
            and_(
                Article.status == ArticleStatus.PUBLISHED,
                Article.published_at >= today_start,
            )
        )
        today_result = await self.session.execute(today_query)
        published_today = today_result.scalar() or 0

        return {
            "by_status": status_counts,
            "avg_quality_score": round(float(avg_quality), 3),
            "published_today": published_today,
            "total": sum(status_counts.values()),
        }

