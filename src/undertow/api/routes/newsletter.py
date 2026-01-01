"""
Newsletter API routes.
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from undertow.infrastructure.database import get_session
from undertow.repositories import ArticleRepository
from undertow.services.newsletter import NewsletterService

router = APIRouter(prefix="/newsletter", tags=["Newsletter"])


class PreviewRequest(BaseModel):
    """Request to preview newsletter."""

    edition_date: datetime | None = None


class SendRequest(BaseModel):
    """Request to send newsletter."""

    subscriber_emails: list[EmailStr] = Field(..., min_length=1)
    edition_date: datetime | None = None


class NewsletterResponse(BaseModel):
    """Newsletter preview response."""

    edition_date: datetime
    article_count: int
    html_preview: str
    text_preview: str


class SendResponse(BaseModel):
    """Newsletter send response."""

    status: str
    sent: int = 0
    failed: int = 0
    errors: list[dict[str, Any]] = []


@router.post("/preview", response_model=NewsletterResponse)
async def preview_newsletter(
    request: PreviewRequest,
    session: AsyncSession = Depends(get_session),
) -> NewsletterResponse:
    """
    Preview the newsletter for a given date.

    Returns HTML and text versions without sending.
    """
    article_repo = ArticleRepository(session)
    edition_date = request.edition_date or datetime.utcnow()

    # Get articles for newsletter
    articles = await article_repo.list_for_newsletter(date=edition_date)

    if not articles:
        raise HTTPException(
            status_code=404,
            detail="No articles available for newsletter",
        )

    # Convert to dicts
    article_dicts = [
        {
            "headline": a.headline,
            "subhead": a.subhead or "",
            "summary": a.summary or "",
            "content": a.content or "",
            "read_time_minutes": a.read_time_minutes or 5,
            "zones": a.zones or [],
        }
        for a in articles
    ]

    # Compile newsletter
    service = NewsletterService()
    newsletter = await service.compile_edition(
        articles=article_dicts,
        edition_date=edition_date,
    )

    return NewsletterResponse(
        edition_date=edition_date,
        article_count=len(articles),
        html_preview=service.render_html(newsletter),
        text_preview=service.render_text(newsletter),
    )


@router.post("/send", response_model=SendResponse)
async def send_newsletter(
    request: SendRequest,
    session: AsyncSession = Depends(get_session),
) -> SendResponse:
    """
    Send the newsletter to specified subscribers.

    Requires SendGrid API key to be configured.
    """
    article_repo = ArticleRepository(session)
    edition_date = request.edition_date or datetime.utcnow()

    # Get articles for newsletter
    articles = await article_repo.list_for_newsletter(date=edition_date)

    if not articles:
        raise HTTPException(
            status_code=404,
            detail="No articles available for newsletter",
        )

    # Convert to dicts
    article_dicts = [
        {
            "headline": a.headline,
            "subhead": a.subhead or "",
            "summary": a.summary or "",
            "content": a.content or "",
            "read_time_minutes": a.read_time_minutes or 5,
            "zones": a.zones or [],
        }
        for a in articles
    ]

    # Compile and send
    service = NewsletterService()
    newsletter = await service.compile_edition(
        articles=article_dicts,
        edition_date=edition_date,
    )

    result = await service.send_to_subscribers(
        newsletter=newsletter,
        subscribers=[str(email) for email in request.subscriber_emails],
    )

    return SendResponse(
        status=result.get("status", "unknown"),
        sent=result.get("sent", 0),
        failed=result.get("failed", 0),
        errors=result.get("errors", []),
    )


@router.get("/schedule")
async def get_schedule() -> dict[str, Any]:
    """
    Get the newsletter schedule configuration.
    """
    return {
        "schedule": {
            "pipeline_start": "05:00 UTC",
            "newsletter_send": "10:00 UTC",
        },
        "articles_per_edition": 5,
        "timezone": "UTC",
    }

