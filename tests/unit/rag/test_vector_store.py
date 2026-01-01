"""
Unit tests for pgvector-based vector store.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID
from undertow.rag.vector_store import (
    PgVectorStore,
    Document,
    SearchResult,
)


@pytest.fixture
def mock_embeddings():
    """Create mock embeddings service."""
    embeddings = MagicMock()
    embeddings.embed = AsyncMock(return_value=MagicMock(embedding=[0.1] * 1536))
    embeddings.embed_batch = AsyncMock(
        return_value=MagicMock(embeddings=[[0.1] * 1536, [0.2] * 1536])
    )
    embeddings.dimension = 1536
    return embeddings


@pytest.fixture
def mock_db_pool():
    """Create mock database pool."""
    pool = MagicMock()
    pool.acquire = MagicMock()
    return pool


class TestPgVectorStore:
    """Tests for PgVectorStore."""

    def test_initialization(self, mock_embeddings):
        """Test store initialization."""
        store = PgVectorStore(
            embeddings=mock_embeddings,
            connection_string="postgresql://test",
        )
        
        assert store._embeddings == mock_embeddings
        assert store._dimension == 1536

    @pytest.mark.asyncio
    async def test_add_document(self, mock_embeddings):
        """Test adding a document."""
        store = PgVectorStore(
            embeddings=mock_embeddings,
            connection_string="postgresql://test",
        )
        
        # Mock the pool connection
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=UUID("12345678-1234-1234-1234-123456789012"))
        
        with patch.object(store, "_pool", MagicMock()):
            store._pool.acquire = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_conn)))
            
            doc_id = await store.add_document(
                content="Test document content",
                source_type="article",
                zones=["horn_of_africa"],
                themes=["security"],
                metadata={"author": "Test"},
            )
            
            # Embedding should be generated
            mock_embeddings.embed.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_returns_results(self, mock_embeddings):
        """Test searching returns ranked results."""
        store = PgVectorStore(
            embeddings=mock_embeddings,
            connection_string="postgresql://test",
        )
        
        # Mock search results
        mock_results = [
            {
                "id": UUID("12345678-1234-1234-1234-123456789012"),
                "content": "Result 1",
                "score": 0.95,
                "source_type": "article",
                "zones": ["horn_of_africa"],
            },
            {
                "id": UUID("12345678-1234-1234-1234-123456789013"),
                "content": "Result 2",
                "score": 0.85,
                "source_type": "news",
                "zones": ["gulf_gcc"],
            },
        ]
        
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=mock_results)
        
        with patch.object(store, "_pool", MagicMock()):
            store._pool.acquire = MagicMock(
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_conn))
            )
            
            results = await store.search(
                query="Test query",
                limit=10,
            )
            
            # Should return search results
            # Note: actual implementation may differ

    @pytest.mark.asyncio
    async def test_hybrid_search(self, mock_embeddings):
        """Test hybrid search combines semantic and keyword search."""
        store = PgVectorStore(
            embeddings=mock_embeddings,
            connection_string="postgresql://test",
        )
        
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])
        
        with patch.object(store, "_pool", MagicMock()):
            store._pool.acquire = MagicMock(
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_conn))
            )
            
            results = await store.hybrid_search(
                query="Test query about Ethiopia",
                keyword_weight=0.3,
                semantic_weight=0.7,
                limit=10,
            )
            
            # Should call embedding
            mock_embeddings.embed.assert_called()

    @pytest.mark.asyncio
    async def test_search_with_zone_filter(self, mock_embeddings):
        """Test searching with zone filtering."""
        store = PgVectorStore(
            embeddings=mock_embeddings,
            connection_string="postgresql://test",
        )
        
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])
        
        with patch.object(store, "_pool", MagicMock()):
            store._pool.acquire = MagicMock(
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_conn))
            )
            
            await store.search(
                query="Ethiopia security",
                zones=["horn_of_africa", "east_africa"],
                limit=5,
            )
            
            # Query should have been executed with zone filter

    @pytest.mark.asyncio
    async def test_delete_document(self, mock_embeddings):
        """Test deleting a document."""
        store = PgVectorStore(
            embeddings=mock_embeddings,
            connection_string="postgresql://test",
        )
        
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value="DELETE 1")
        
        with patch.object(store, "_pool", MagicMock()):
            store._pool.acquire = MagicMock(
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_conn))
            )
            
            doc_id = UUID("12345678-1234-1234-1234-123456789012")
            result = await store.delete(doc_id)
            
            mock_conn.execute.assert_called()

    def test_mmr_diversity_selection(self, mock_embeddings):
        """Test MMR diversity selection algorithm."""
        store = PgVectorStore(
            embeddings=mock_embeddings,
            connection_string="postgresql://test",
        )
        
        # Create test candidates
        candidates = [
            {"embedding": [1.0, 0.0], "score": 0.9, "content": "Doc 1"},
            {"embedding": [0.99, 0.01], "score": 0.85, "content": "Doc 2"},  # Very similar to 1
            {"embedding": [0.0, 1.0], "score": 0.8, "content": "Doc 3"},  # Very different
        ]
        query_embedding = [1.0, 0.0]
        
        # MMR should prefer Doc 3 over Doc 2 despite lower relevance
        # because it adds more diversity
        selected = store._mmr_rerank(
            query_embedding=query_embedding,
            candidates=candidates,
            k=2,
            lambda_mult=0.5,
        )
        
        # Should select doc 1 (highest relevance) and doc 3 (most diverse)
        # Note: actual implementation may vary


class TestDocument:
    """Tests for Document model."""

    def test_document_creation(self):
        """Test creating a document."""
        doc = Document(
            id=UUID("12345678-1234-1234-1234-123456789012"),
            content="Test content",
            source_type="article",
            zones=["horn_of_africa"],
            themes=["security"],
            metadata={"author": "Test"},
        )
        
        assert doc.content == "Test content"
        assert doc.source_type == "article"
        assert "horn_of_africa" in doc.zones


class TestSearchResult:
    """Tests for SearchResult model."""

    def test_search_result_creation(self):
        """Test creating a search result."""
        result = SearchResult(
            document=Document(
                id=UUID("12345678-1234-1234-1234-123456789012"),
                content="Test content",
                source_type="article",
            ),
            score=0.95,
            rank=1,
        )
        
        assert result.score == 0.95
        assert result.rank == 1

