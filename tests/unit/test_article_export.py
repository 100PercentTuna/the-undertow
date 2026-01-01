"""
Unit tests for Article Export service.
"""

import json
import pytest
from datetime import datetime
from unittest.mock import MagicMock
from uuid import uuid4

from undertow.services.article_export import ArticleExporter
from undertow.models.article import Article, ArticleStatus


@pytest.fixture
def exporter() -> ArticleExporter:
    """Create article exporter."""
    return ArticleExporter()


@pytest.fixture
def sample_article() -> Article:
    """Create sample article."""
    article = MagicMock(spec=Article)
    article.id = uuid4()
    article.headline = "Major Power Signs Defense Agreement"
    article.subhead = "A strategic shift in regional dynamics"
    article.content = """This is the first paragraph of the article. It contains important information about the defense agreement.

This is the second paragraph. It provides more context and analysis.

This is the third paragraph with conclusions."""
    article.zones = ["horn_of_africa", "gulf_gcc"]
    article.themes = ["defense", "strategy"]
    article.status = ArticleStatus.PUBLISHED
    article.quality_score = 0.85
    article.word_count = 250
    article.created_at = datetime(2025, 1, 1, 12, 0, 0)
    article.published_at = datetime(2025, 1, 1, 14, 0, 0)
    return article


class TestArticleExporter:
    """Tests for ArticleExporter."""

    def test_export_json(
        self,
        exporter: ArticleExporter,
        sample_article: Article,
    ) -> None:
        """Test JSON export."""
        result = exporter.export_json(sample_article)
        data = json.loads(result)

        assert data["headline"] == "Major Power Signs Defense Agreement"
        assert data["word_count"] == 250
        assert data["quality_score"] == 0.85
        assert "horn_of_africa" in data["zones"]

    def test_export_markdown(
        self,
        exporter: ArticleExporter,
        sample_article: Article,
    ) -> None:
        """Test Markdown export."""
        result = exporter.export_markdown(sample_article)

        # Should have front matter
        assert "---" in result
        assert "title:" in result

        # Should have headline
        assert "# Major Power Signs Defense Agreement" in result

        # Should have content
        assert "first paragraph" in result

    def test_export_html(
        self,
        exporter: ArticleExporter,
        sample_article: Article,
    ) -> None:
        """Test HTML export."""
        result = exporter.export_html(sample_article)

        # Should be valid HTML
        assert "<!DOCTYPE html>" in result
        assert "<html" in result
        assert "</html>" in result

        # Should have headline
        assert "Major Power Signs Defense Agreement" in result

        # Should have content paragraphs
        assert "<p>" in result

    def test_export_text(
        self,
        exporter: ArticleExporter,
        sample_article: Article,
    ) -> None:
        """Test plain text export."""
        result = exporter.export_text(sample_article)

        # Should have headline
        assert "MAJOR POWER SIGNS DEFENSE AGREEMENT" in result

        # Should have content
        assert "first paragraph" in result

        # Should have footer
        assert "The Undertow" in result

    def test_export_batch_json(
        self,
        exporter: ArticleExporter,
        sample_article: Article,
    ) -> None:
        """Test batch JSON export."""
        articles = [sample_article, sample_article]
        result = exporter.export_batch_json(articles)
        data = json.loads(result)

        assert isinstance(data, list)
        assert len(data) == 2

    def test_content_to_html(self, exporter: ArticleExporter) -> None:
        """Test content to HTML conversion."""
        content = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        result = exporter._content_to_html(content)

        assert result.count("<p>") == 3
        assert result.count("</p>") == 3

    def test_empty_content(
        self,
        exporter: ArticleExporter,
        sample_article: Article,
    ) -> None:
        """Test export with empty content."""
        sample_article.content = None

        # Should not raise
        result = exporter.export_markdown(sample_article)
        assert result is not None

        result = exporter.export_html(sample_article)
        assert result is not None

    def test_missing_optional_fields(
        self,
        exporter: ArticleExporter,
        sample_article: Article,
    ) -> None:
        """Test export with missing optional fields."""
        sample_article.subhead = None
        sample_article.published_at = None

        result = exporter.export_json(sample_article)
        data = json.loads(result)

        assert data["subhead"] is None
        assert data["published_at"] is None

