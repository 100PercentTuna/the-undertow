"""
Article export service.

Exports articles in various formats.
"""

import json
from datetime import datetime
from io import BytesIO, StringIO
from typing import Any

import structlog

from undertow.models.article import Article

logger = structlog.get_logger()


class ArticleExporter:
    """
    Service for exporting articles to various formats.

    Supports:
    - JSON
    - Markdown
    - HTML
    - Plain text
    """

    def export_json(self, article: Article) -> str:
        """
        Export article as JSON.

        Args:
            article: Article to export

        Returns:
            JSON string
        """
        data = {
            "id": str(article.id),
            "headline": article.headline,
            "subhead": article.subhead,
            "content": article.content,
            "zones": article.zones,
            "themes": article.themes,
            "status": article.status.value if article.status else None,
            "quality_score": article.quality_score,
            "word_count": article.word_count,
            "created_at": article.created_at.isoformat() if article.created_at else None,
            "published_at": article.published_at.isoformat() if article.published_at else None,
        }

        return json.dumps(data, indent=2, ensure_ascii=False)

    def export_markdown(self, article: Article) -> str:
        """
        Export article as Markdown.

        Args:
            article: Article to export

        Returns:
            Markdown string
        """
        lines = []

        # Front matter
        lines.append("---")
        lines.append(f"title: \"{article.headline}\"")
        if article.subhead:
            lines.append(f"subtitle: \"{article.subhead}\"")
        lines.append(f"date: {article.created_at.strftime('%Y-%m-%d') if article.created_at else 'Unknown'}")
        if article.zones:
            lines.append(f"zones: [{', '.join(article.zones)}]")
        if article.themes:
            lines.append(f"themes: [{', '.join(article.themes)}]")
        lines.append(f"word_count: {article.word_count}")
        lines.append("---")
        lines.append("")

        # Title
        lines.append(f"# {article.headline}")
        lines.append("")

        if article.subhead:
            lines.append(f"*{article.subhead}*")
            lines.append("")

        # Metadata
        lines.append(f"**Published:** {article.created_at.strftime('%B %d, %Y') if article.created_at else 'Draft'}")
        lines.append(f"**Read time:** ~{max(1, article.word_count // 250)} minutes")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Content
        lines.append(article.content or "")

        return "\n".join(lines)

    def export_html(self, article: Article) -> str:
        """
        Export article as standalone HTML.

        Args:
            article: Article to export

        Returns:
            HTML string
        """
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{article.headline} | The Undertow</title>
    <style>
        body {{
            font-family: Georgia, 'Times New Roman', serif;
            max-width: 720px;
            margin: 0 auto;
            padding: 2rem;
            line-height: 1.7;
            color: #1a1a1a;
            background: #fafafa;
        }}
        h1 {{
            font-size: 2.25rem;
            margin-bottom: 0.5rem;
            line-height: 1.2;
        }}
        .subhead {{
            font-size: 1.25rem;
            color: #666;
            font-style: italic;
            margin-bottom: 1.5rem;
        }}
        .meta {{
            font-size: 0.875rem;
            color: #888;
            border-bottom: 1px solid #ddd;
            padding-bottom: 1rem;
            margin-bottom: 2rem;
        }}
        .content {{
            font-size: 1.125rem;
        }}
        .content p {{
            margin-bottom: 1.25rem;
        }}
        .footer {{
            margin-top: 3rem;
            padding-top: 1rem;
            border-top: 1px solid #ddd;
            font-size: 0.875rem;
            color: #888;
        }}
    </style>
</head>
<body>
    <article>
        <h1>{article.headline}</h1>
        {f'<p class="subhead">{article.subhead}</p>' if article.subhead else ''}
        <div class="meta">
            <span>{article.created_at.strftime('%B %d, %Y') if article.created_at else 'Draft'}</span>
            &middot;
            <span>{max(1, article.word_count // 250)} min read</span>
            &middot;
            <span>{article.word_count} words</span>
        </div>
        <div class="content">
            {self._content_to_html(article.content or '')}
        </div>
    </article>
    <footer class="footer">
        <p>© The Undertow. All rights reserved.</p>
    </footer>
</body>
</html>"""

        return html

    def export_text(self, article: Article) -> str:
        """
        Export article as plain text.

        Args:
            article: Article to export

        Returns:
            Plain text string
        """
        lines = []

        # Header
        lines.append("=" * 60)
        lines.append(article.headline.upper())
        lines.append("=" * 60)
        lines.append("")

        if article.subhead:
            lines.append(article.subhead)
            lines.append("")

        lines.append(f"Date: {article.created_at.strftime('%B %d, %Y') if article.created_at else 'Draft'}")
        lines.append(f"Words: {article.word_count}")
        lines.append(f"Read time: ~{max(1, article.word_count // 250)} minutes")
        lines.append("")
        lines.append("-" * 60)
        lines.append("")

        # Content
        lines.append(article.content or "")

        lines.append("")
        lines.append("-" * 60)
        lines.append("© The Undertow")

        return "\n".join(lines)

    def export_batch_json(self, articles: list[Article]) -> str:
        """
        Export multiple articles as JSON array.

        Args:
            articles: Articles to export

        Returns:
            JSON string
        """
        data = []
        for article in articles:
            data.append(json.loads(self.export_json(article)))

        return json.dumps(data, indent=2, ensure_ascii=False)

    def _content_to_html(self, content: str) -> str:
        """Convert plain text content to HTML paragraphs."""
        paragraphs = content.split("\n\n")
        html_paragraphs = [f"<p>{p.strip()}</p>" for p in paragraphs if p.strip()]
        return "\n".join(html_paragraphs)


# Global instance
_article_exporter: ArticleExporter | None = None


def get_article_exporter() -> ArticleExporter:
    """Get global article exporter instance."""
    global _article_exporter
    if _article_exporter is None:
        _article_exporter = ArticleExporter()
    return _article_exporter

