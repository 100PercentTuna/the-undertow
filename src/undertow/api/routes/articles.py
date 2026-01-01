"""
Article management endpoints.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from undertow.infrastructure.database import get_session
from undertow.models.article import Article, ArticleStatus
from undertow.schemas.base import PaginatedResponse, PaginationParams

router = APIRouter()


@router.get("")
async def list_articles(
    page: Annotated[int, Query(ge=1, le=10000)] = 1,
    per_page: Annotated[int, Query(ge=1, le=200)] = 50,
    status_filter: ArticleStatus | None = None,
    zone: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> PaginatedResponse:
    """
    List articles with filtering and pagination.

    Args:
        page: Page number (1-indexed)
        per_page: Items per page (max 200)
        status_filter: Filter by article status
        zone: Filter by zone

    Returns:
        Paginated list of articles
    """
    pagination = PaginationParams(page=page, per_page=per_page)

    # Build query
    query = select(Article).order_by(Article.created_at.desc())

    if status_filter:
        query = query.where(Article.status == status_filter)

    if zone:
        query = query.where(Article.zones.contains([zone]))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_query)).scalar() or 0

    # Apply pagination
    query = query.offset(pagination.offset).limit(pagination.per_page)

    result = await session.execute(query)
    articles = result.scalars().all()

    return PaginatedResponse.create(
        items=[_article_to_dict(a) for a in articles],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{article_id}")
async def get_article(
    article_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Get a single article by ID.

    Args:
        article_id: Article UUID

    Returns:
        Full article details
    """
    article = await session.get(Article, article_id)

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article {article_id} not found",
        )

    return _article_to_dict(article, include_content=True)


@router.get("/slug/{slug}")
async def get_article_by_slug(
    slug: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Get article by slug.

    Args:
        slug: Article slug

    Returns:
        Full article details
    """
    query = select(Article).where(Article.slug == slug)
    result = await session.execute(query)
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article with slug '{slug}' not found",
        )

    return _article_to_dict(article, include_content=True)


@router.post("/{article_id}/publish")
async def publish_article(
    article_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Publish an approved article.

    Args:
        article_id: Article UUID

    Returns:
        Updated article status
    """
    article = await session.get(Article, article_id)

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article {article_id} not found",
        )

    if article.status != ArticleStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Article must be APPROVED to publish, current status: {article.status}",
        )

    # Update status and publish time
    from datetime import datetime, timezone

    article.status = ArticleStatus.PUBLISHED
    article.published_at = datetime.now(timezone.utc)
    await session.commit()

    return {
        "message": "Article published",
        "article_id": article_id,
        "status": article.status.value,
        "published_at": article.published_at.isoformat(),
    }


@router.post("/{article_id}/approve")
async def approve_article(
    article_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Approve an article for publication.

    Args:
        article_id: Article UUID

    Returns:
        Updated article status
    """
    article = await session.get(Article, article_id)

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article {article_id} not found",
        )

    if article.status not in [ArticleStatus.DRAFT, ArticleStatus.REVIEW]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Article cannot be approved from status {article.status}",
        )

    article.status = ArticleStatus.APPROVED
    await session.commit()

    return {
        "message": "Article approved",
        "article_id": article_id,
        "status": article.status.value,
    }


def _article_to_dict(article: Article, include_content: bool = False) -> dict:
    """Convert Article model to dict."""
    data = {
        "id": article.id,
        "headline": article.headline,
        "subhead": article.subhead,
        "slug": article.slug,
        "summary": article.summary,
        "read_time_minutes": article.read_time_minutes,
        "status": article.status.value,
        "quality_score": article.quality_score,
        "confidence_score": article.confidence_score,
        "zones": article.zones,
        "themes": article.themes,
        "story_id": article.story_id,
        "published_at": article.published_at.isoformat() if article.published_at else None,
        "created_at": article.created_at.isoformat(),
        "updated_at": article.updated_at.isoformat() if article.updated_at else None,
    }

    if include_content:
        data["content"] = article.content
        data["sources"] = article.sources
        data["analysis_data"] = article.analysis_data

    return data

