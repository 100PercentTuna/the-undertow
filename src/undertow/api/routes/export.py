"""
Export routes for articles.
"""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from undertow.repositories.article import ArticleRepository
from undertow.services.article_export import get_article_exporter

router = APIRouter(prefix="/export", tags=["Export"])


@router.get("/articles/{article_id}")
async def export_article(
    article_id: UUID,
    format: Literal["json", "markdown", "html", "text"] = Query(default="json"),
) -> Response:
    """
    Export a single article.

    Supports formats:
    - json: JSON object
    - markdown: Markdown with front matter
    - html: Standalone HTML page
    - text: Plain text
    """
    repo = ArticleRepository()
    article = await repo.get(article_id)

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    exporter = get_article_exporter()

    content_types = {
        "json": "application/json",
        "markdown": "text/markdown",
        "html": "text/html",
        "text": "text/plain",
    }

    extensions = {
        "json": "json",
        "markdown": "md",
        "html": "html",
        "text": "txt",
    }

    if format == "json":
        content = exporter.export_json(article)
    elif format == "markdown":
        content = exporter.export_markdown(article)
    elif format == "html":
        content = exporter.export_html(article)
    else:
        content = exporter.export_text(article)

    filename = f"{article.headline[:50].replace(' ', '-').lower()}.{extensions[format]}"

    return Response(
        content=content,
        media_type=content_types[format],
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get("/articles")
async def export_articles(
    format: Literal["json"] = Query(default="json"),
    status: str | None = Query(default=None),
    limit: int = Query(default=100, le=1000),
) -> Response:
    """
    Export multiple articles.

    Currently only JSON format is supported for batch export.
    """
    repo = ArticleRepository()
    articles, _ = await repo.list(limit=limit)

    if status:
        articles = [a for a in articles if a.status and a.status.value == status]

    exporter = get_article_exporter()
    content = exporter.export_batch_json(articles)

    return Response(
        content=content,
        media_type="application/json",
        headers={
            "Content-Disposition": 'attachment; filename="articles.json"',
        },
    )

