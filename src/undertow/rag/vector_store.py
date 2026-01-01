"""
Vector store for semantic search using pgvector.

Provides hybrid search (semantic + keyword) with reranking.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal
from uuid import UUID, uuid4

import structlog
from sqlalchemy import Column, DateTime, Index, String, Text, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PG_UUID
from pgvector.sqlalchemy import Vector

from undertow.infrastructure.database import Base, get_session
from undertow.rag.embeddings import get_embedding_provider

logger = structlog.get_logger()


class Document(Base):
    """
    Document stored in vector database.

    Stores text chunks with embeddings for semantic search.
    """

    __tablename__ = "documents"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=True)  # OpenAI small dimensions

    # Metadata for filtering
    source_type = Column(String(50), nullable=False)  # article, source, context
    source_id = Column(String(255), nullable=True)  # Reference to original
    source_url = Column(Text, nullable=True)
    zones = Column(ARRAY(String), default=[])
    themes = Column(ARRAY(String), default=[])

    # Additional metadata
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        # HNSW index for fast similarity search
        Index(
            "ix_documents_embedding_hnsw",
            embedding,
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        # GIN index for array containment queries
        Index("ix_documents_zones_gin", zones, postgresql_using="gin"),
        Index("ix_documents_themes_gin", themes, postgresql_using="gin"),
    )


@dataclass
class SearchResult:
    """A single search result."""

    id: UUID
    content: str
    score: float
    source_type: str
    source_id: str | None
    source_url: str | None
    zones: list[str]
    metadata: dict[str, Any]


@dataclass
class HybridSearchResult:
    """Result from hybrid search with reranking."""

    results: list[SearchResult]
    query: str
    semantic_count: int
    keyword_count: int
    reranked: bool


class VectorStore:
    """
    Vector store with hybrid search capabilities.

    Features:
    - Semantic search using pgvector
    - Keyword search using PostgreSQL full-text
    - Hybrid search combining both
    - Cross-encoder reranking for precision
    - Maximal Marginal Relevance (MMR) for diversity

    Example:
        store = VectorStore()

        # Add documents
        await store.add_document(
            content="The defense agreement was signed...",
            source_type="article",
            zones=["horn_of_africa"],
        )

        # Search
        results = await store.hybrid_search(
            query="defense agreements in Horn of Africa",
            zones=["horn_of_africa"],
            limit=10,
        )
    """

    def __init__(self) -> None:
        """Initialize vector store."""
        self._embedder = get_embedding_provider()

    async def add_document(
        self,
        content: str,
        source_type: str,
        source_id: str | None = None,
        source_url: str | None = None,
        zones: list[str] | None = None,
        themes: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> UUID:
        """
        Add a document to the vector store.

        Args:
            content: Document text
            source_type: Type (article, source, context)
            source_id: Reference to original
            source_url: Source URL
            zones: Geographic zones
            themes: Thematic tags
            metadata: Additional metadata

        Returns:
            Document ID
        """
        # Generate embedding
        embedding = await self._embedder.embed(content)

        doc_id = uuid4()

        async with get_session() as session:
            doc = Document(
                id=doc_id,
                content=content,
                embedding=embedding,
                source_type=source_type,
                source_id=source_id,
                source_url=source_url,
                zones=zones or [],
                themes=themes or [],
                metadata=metadata or {},
            )
            session.add(doc)
            await session.commit()

        logger.debug(
            "Document added to vector store",
            doc_id=str(doc_id),
            source_type=source_type,
        )

        return doc_id

    async def add_documents_batch(
        self,
        documents: list[dict[str, Any]],
        batch_size: int = 50,
    ) -> list[UUID]:
        """
        Add multiple documents in batch.

        Args:
            documents: List of document dicts with content and metadata
            batch_size: Batch size for embedding generation

        Returns:
            List of document IDs
        """
        if not documents:
            return []

        # Extract texts for batch embedding
        texts = [d["content"] for d in documents]
        embeddings = await self._embedder.embed_batch(texts, batch_size=batch_size)

        doc_ids = []

        async with get_session() as session:
            for doc_dict, embedding in zip(documents, embeddings):
                doc_id = uuid4()
                doc = Document(
                    id=doc_id,
                    content=doc_dict["content"],
                    embedding=embedding,
                    source_type=doc_dict.get("source_type", "unknown"),
                    source_id=doc_dict.get("source_id"),
                    source_url=doc_dict.get("source_url"),
                    zones=doc_dict.get("zones", []),
                    themes=doc_dict.get("themes", []),
                    metadata=doc_dict.get("metadata", {}),
                )
                session.add(doc)
                doc_ids.append(doc_id)

            await session.commit()

        logger.info(
            "Batch documents added",
            count=len(doc_ids),
        )

        return doc_ids

    async def semantic_search(
        self,
        query: str,
        limit: int = 10,
        zones: list[str] | None = None,
        themes: list[str] | None = None,
        source_types: list[str] | None = None,
        min_score: float = 0.5,
    ) -> list[SearchResult]:
        """
        Semantic similarity search.

        Args:
            query: Search query
            limit: Max results
            zones: Filter by zones
            themes: Filter by themes
            source_types: Filter by source type
            min_score: Minimum similarity score

        Returns:
            List of search results
        """
        # Generate query embedding
        query_embedding = await self._embedder.embed(query)

        async with get_session() as session:
            # Build query with filters
            sql = """
                SELECT
                    id,
                    content,
                    1 - (embedding <=> :query_embedding::vector) as score,
                    source_type,
                    source_id,
                    source_url,
                    zones,
                    metadata
                FROM documents
                WHERE 1=1
            """

            params: dict[str, Any] = {
                "query_embedding": query_embedding,
            }

            if zones:
                sql += " AND zones && :zones"
                params["zones"] = zones

            if themes:
                sql += " AND themes && :themes"
                params["themes"] = themes

            if source_types:
                sql += " AND source_type = ANY(:source_types)"
                params["source_types"] = source_types

            sql += """
                ORDER BY embedding <=> :query_embedding::vector
                LIMIT :limit
            """
            params["limit"] = limit

            result = await session.execute(text(sql), params)
            rows = result.fetchall()

        results = []
        for row in rows:
            score = float(row.score)
            if score >= min_score:
                results.append(
                    SearchResult(
                        id=row.id,
                        content=row.content,
                        score=score,
                        source_type=row.source_type,
                        source_id=row.source_id,
                        source_url=row.source_url,
                        zones=row.zones or [],
                        metadata=row.metadata or {},
                    )
                )

        return results

    async def keyword_search(
        self,
        query: str,
        limit: int = 10,
        zones: list[str] | None = None,
    ) -> list[SearchResult]:
        """
        Full-text keyword search.

        Args:
            query: Search query
            limit: Max results
            zones: Filter by zones

        Returns:
            List of search results
        """
        async with get_session() as session:
            sql = """
                SELECT
                    id,
                    content,
                    ts_rank(to_tsvector('english', content), plainto_tsquery('english', :query)) as score,
                    source_type,
                    source_id,
                    source_url,
                    zones,
                    metadata
                FROM documents
                WHERE to_tsvector('english', content) @@ plainto_tsquery('english', :query)
            """

            params: dict[str, Any] = {"query": query}

            if zones:
                sql += " AND zones && :zones"
                params["zones"] = zones

            sql += """
                ORDER BY score DESC
                LIMIT :limit
            """
            params["limit"] = limit

            result = await session.execute(text(sql), params)
            rows = result.fetchall()

        return [
            SearchResult(
                id=row.id,
                content=row.content,
                score=float(row.score),
                source_type=row.source_type,
                source_id=row.source_id,
                source_url=row.source_url,
                zones=row.zones or [],
                metadata=row.metadata or {},
            )
            for row in rows
        ]

    async def hybrid_search(
        self,
        query: str,
        limit: int = 10,
        zones: list[str] | None = None,
        themes: list[str] | None = None,
        semantic_weight: float = 0.7,
        rerank: bool = True,
    ) -> HybridSearchResult:
        """
        Hybrid search combining semantic and keyword search.

        Args:
            query: Search query
            limit: Max results
            zones: Filter by zones
            themes: Filter by themes
            semantic_weight: Weight for semantic vs keyword (0-1)
            rerank: Whether to apply cross-encoder reranking

        Returns:
            HybridSearchResult with combined results
        """
        # Run both searches
        semantic_results = await self.semantic_search(
            query=query,
            limit=limit * 2,
            zones=zones,
            themes=themes,
        )

        keyword_results = await self.keyword_search(
            query=query,
            limit=limit * 2,
            zones=zones,
        )

        # Combine and deduplicate
        seen_ids: set[UUID] = set()
        combined: dict[UUID, SearchResult] = {}

        keyword_weight = 1 - semantic_weight

        for result in semantic_results:
            combined[result.id] = SearchResult(
                id=result.id,
                content=result.content,
                score=result.score * semantic_weight,
                source_type=result.source_type,
                source_id=result.source_id,
                source_url=result.source_url,
                zones=result.zones,
                metadata=result.metadata,
            )
            seen_ids.add(result.id)

        for result in keyword_results:
            if result.id in combined:
                # Boost score for appearing in both
                combined[result.id].score += result.score * keyword_weight
            else:
                combined[result.id] = SearchResult(
                    id=result.id,
                    content=result.content,
                    score=result.score * keyword_weight,
                    source_type=result.source_type,
                    source_id=result.source_id,
                    source_url=result.source_url,
                    zones=result.zones,
                    metadata=result.metadata,
                )

        # Sort by combined score
        results = sorted(combined.values(), key=lambda x: x.score, reverse=True)

        # Apply reranking if requested
        reranked = False
        if rerank and results:
            results = await self._rerank(query, results[:limit * 2])
            reranked = True

        return HybridSearchResult(
            results=results[:limit],
            query=query,
            semantic_count=len(semantic_results),
            keyword_count=len(keyword_results),
            reranked=reranked,
        )

    async def _rerank(
        self,
        query: str,
        results: list[SearchResult],
    ) -> list[SearchResult]:
        """
        Rerank results using cross-encoder or LLM.

        For now, uses a simple relevance scoring heuristic.
        TODO: Integrate actual cross-encoder model.
        """
        # Simple reranking based on query term overlap
        query_terms = set(query.lower().split())

        for result in results:
            content_terms = set(result.content.lower().split())
            overlap = len(query_terms & content_terms)
            # Boost score based on term overlap
            result.score = result.score * (1 + overlap * 0.1)

        return sorted(results, key=lambda x: x.score, reverse=True)

    async def mmr_search(
        self,
        query: str,
        limit: int = 10,
        diversity: float = 0.3,
        zones: list[str] | None = None,
    ) -> list[SearchResult]:
        """
        Maximal Marginal Relevance search for diverse results.

        Args:
            query: Search query
            limit: Max results
            diversity: Diversity factor (0 = relevance only, 1 = diversity only)
            zones: Filter by zones

        Returns:
            Diverse search results
        """
        # Get more candidates than needed
        candidates = await self.semantic_search(
            query=query,
            limit=limit * 3,
            zones=zones,
        )

        if len(candidates) <= limit:
            return candidates

        # MMR selection
        selected: list[SearchResult] = []
        remaining = list(candidates)

        while len(selected) < limit and remaining:
            # Score each remaining candidate
            best_score = -1
            best_idx = 0

            for i, candidate in enumerate(remaining):
                # Relevance to query (already computed)
                relevance = candidate.score

                # Similarity to already selected (penalize)
                if selected:
                    max_sim = max(
                        self._content_similarity(candidate.content, s.content)
                        for s in selected
                    )
                else:
                    max_sim = 0

                # MMR score
                mmr_score = (1 - diversity) * relevance - diversity * max_sim

                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = i

            selected.append(remaining.pop(best_idx))

        return selected

    def _content_similarity(self, text1: str, text2: str) -> float:
        """Simple content similarity using term overlap."""
        terms1 = set(text1.lower().split())
        terms2 = set(text2.lower().split())

        if not terms1 or not terms2:
            return 0

        intersection = len(terms1 & terms2)
        union = len(terms1 | terms2)

        return intersection / union if union > 0 else 0


# Global instance
_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    """Get global vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store

