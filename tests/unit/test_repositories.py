"""
Tests for repositories.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from undertow.repositories.base import BaseRepository
from undertow.repositories.story import StoryRepository
from undertow.repositories.article import ArticleRepository
from undertow.models.story import Story, StoryStatus, Zone
from undertow.models.article import Article, ArticleStatus


class TestStoryRepository:
    """Tests for StoryRepository."""

    @pytest.fixture
    def mock_session(self) -> MagicMock:
        """Create mock session."""
        session = MagicMock()
        session.execute = AsyncMock()
        session.get = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        session.delete = AsyncMock()
        return session

    @pytest.fixture
    def repo(self, mock_session: MagicMock) -> StoryRepository:
        """Create repository with mock session."""
        return StoryRepository(mock_session)

    @pytest.mark.asyncio
    async def test_get_by_id(
        self, repo: StoryRepository, mock_session: MagicMock
    ) -> None:
        """Test getting story by ID."""
        mock_story = Story(
            id="test-id",
            headline="Test Story",
            status=StoryStatus.PENDING,
        )
        mock_session.get.return_value = mock_story

        result = await repo.get("test-id")

        assert result == mock_story
        mock_session.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_url(
        self, repo: StoryRepository, mock_session: MagicMock
    ) -> None:
        """Test getting story by URL."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = Story(
            id="test-id",
            headline="Test",
            source_url="https://example.com/story",
        )
        mock_session.execute.return_value = mock_result

        result = await repo.get_by_url("https://example.com/story")

        assert result is not None
        assert result.source_url == "https://example.com/story"

    @pytest.mark.asyncio
    async def test_list_pending_for_analysis(
        self, repo: StoryRepository, mock_session: MagicMock
    ) -> None:
        """Test listing pending stories."""
        mock_stories = [
            Story(id="1", headline="Story 1", status=StoryStatus.PENDING),
            Story(id="2", headline="Story 2", status=StoryStatus.PENDING),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_stories
        mock_session.execute.return_value = mock_result

        result = await repo.list_pending_for_analysis(limit=10)

        assert len(result) == 2
        assert all(s.status == StoryStatus.PENDING for s in result)

    @pytest.mark.asyncio
    async def test_create(
        self, repo: StoryRepository, mock_session: MagicMock
    ) -> None:
        """Test creating a story."""
        story = Story(
            headline="New Story",
            status=StoryStatus.PENDING,
        )

        await repo.create(story)

        mock_session.add.assert_called_once_with(story)
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once_with(story)

    @pytest.mark.asyncio
    async def test_update_status(
        self, repo: StoryRepository, mock_session: MagicMock
    ) -> None:
        """Test updating story status."""
        mock_story = Story(
            id="test-id",
            headline="Test",
            status=StoryStatus.PENDING,
        )
        mock_session.get.return_value = mock_story

        result = await repo.update_status("test-id", StoryStatus.ANALYZED)

        assert result is not None
        assert result.status == StoryStatus.ANALYZED


class TestArticleRepository:
    """Tests for ArticleRepository."""

    @pytest.fixture
    def mock_session(self) -> MagicMock:
        """Create mock session."""
        session = MagicMock()
        session.execute = AsyncMock()
        session.get = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        return session

    @pytest.fixture
    def repo(self, mock_session: MagicMock) -> ArticleRepository:
        """Create repository with mock session."""
        return ArticleRepository(mock_session)

    @pytest.mark.asyncio
    async def test_get_by_slug(
        self, repo: ArticleRepository, mock_session: MagicMock
    ) -> None:
        """Test getting article by slug."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = Article(
            id="test-id",
            headline="Test Article",
            slug="test-article",
        )
        mock_session.execute.return_value = mock_result

        result = await repo.get_by_slug("test-article")

        assert result is not None
        assert result.slug == "test-article"

    @pytest.mark.asyncio
    async def test_list_published(
        self, repo: ArticleRepository, mock_session: MagicMock
    ) -> None:
        """Test listing published articles."""
        mock_articles = [
            Article(
                id="1",
                headline="Article 1",
                status=ArticleStatus.PUBLISHED,
                published_at=datetime.utcnow(),
            ),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_articles
        mock_session.execute.return_value = mock_result

        result = await repo.list_published()

        assert len(result) == 1
        assert result[0].status == ArticleStatus.PUBLISHED

    @pytest.mark.asyncio
    async def test_update_status_to_published(
        self, repo: ArticleRepository, mock_session: MagicMock
    ) -> None:
        """Test updating article to published sets timestamp."""
        mock_article = Article(
            id="test-id",
            headline="Test",
            status=ArticleStatus.DRAFT,
        )
        mock_session.get.return_value = mock_article

        result = await repo.update_status("test-id", ArticleStatus.PUBLISHED)

        assert result is not None
        assert result.status == ArticleStatus.PUBLISHED
        assert result.published_at is not None

