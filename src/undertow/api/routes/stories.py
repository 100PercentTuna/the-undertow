"""
Story management endpoints.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from undertow.infrastructure.database import get_session
from undertow.models.story import Story, StoryStatus, Zone
from undertow.schemas.base import PaginatedResponse, PaginationParams

router = APIRouter()


@router.get("")
async def list_stories(
    page: Annotated[int, Query(ge=1, le=10000)] = 1,
    per_page: Annotated[int, Query(ge=1, le=200)] = 50,
    status_filter: StoryStatus | None = None,
    zone: Zone | None = None,
    session: AsyncSession = Depends(get_session),
) -> PaginatedResponse:
    """
    List stories with filtering and pagination.

    Args:
        page: Page number (1-indexed)
        per_page: Items per page (max 200)
        status_filter: Filter by story status
        zone: Filter by primary zone

    Returns:
        Paginated list of stories
    """
    pagination = PaginationParams(page=page, per_page=per_page)

    # Build query
    query = select(Story).order_by(Story.created_at.desc())

    if status_filter:
        query = query.where(Story.status == status_filter)

    if zone:
        query = query.where(Story.primary_zone == zone)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_query)).scalar() or 0

    # Apply pagination
    query = query.offset(pagination.offset).limit(pagination.per_page)

    result = await session.execute(query)
    stories = result.scalars().all()

    return PaginatedResponse.create(
        items=[_story_to_dict(s) for s in stories],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{story_id}")
async def get_story(
    story_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Get a single story by ID.

    Args:
        story_id: Story UUID

    Returns:
        Story details including analysis data
    """
    story = await session.get(Story, story_id)

    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Story {story_id} not found",
        )

    return _story_to_dict(story, include_analysis=True)


@router.post("/{story_id}/analyze")
async def trigger_analysis(
    story_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Trigger analysis for a story.

    Args:
        story_id: Story UUID

    Returns:
        Status message
    """
    story = await session.get(Story, story_id)

    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Story {story_id} not found",
        )

    if story.status not in [StoryStatus.PENDING, StoryStatus.REJECTED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Story cannot be analyzed in status {story.status}",
        )

    # Update status
    story.status = StoryStatus.ANALYZING
    await session.commit()

    # TODO: Queue analysis task with Celery
    # analyze_story.delay(story_id)

    return {
        "message": "Analysis triggered",
        "story_id": story_id,
        "status": story.status.value,
    }


def _story_to_dict(story: Story, include_analysis: bool = False) -> dict:
    """Convert Story model to dict."""
    data = {
        "id": story.id,
        "headline": story.headline,
        "summary": story.summary,
        "source_name": story.source_name,
        "source_url": story.source_url,
        "source_published_at": story.source_published_at.isoformat()
        if story.source_published_at
        else None,
        "primary_zone": story.primary_zone.value,
        "secondary_zones": story.secondary_zones,
        "status": story.status.value,
        "relevance_score": story.relevance_score,
        "importance_score": story.importance_score,
        "key_events": story.key_events,
        "primary_actors": story.primary_actors,
        "themes": story.themes,
        "created_at": story.created_at.isoformat(),
        "updated_at": story.updated_at.isoformat() if story.updated_at else None,
    }

    if include_analysis:
        data["content"] = story.content
        data["analysis_data"] = story.analysis_data

    return data

