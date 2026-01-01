"""
RAG (Retrieval Augmented Generation) module for The Undertow.

Provides vector storage and retrieval for source documents.
"""

from undertow.rag.embeddings import (
    OpenAIEmbeddings,
    EmbeddingResult,
    BatchEmbeddingResult,
)
from undertow.rag.vector_store import (
    PgVectorStore,
    Document,
    SearchResult,
)

# Singleton instances
_embeddings: OpenAIEmbeddings | None = None
_vector_store: PgVectorStore | None = None


def get_embeddings() -> OpenAIEmbeddings:
    """Get or create the embeddings service instance."""
    global _embeddings
    if _embeddings is None:
        from undertow.config import get_settings
        settings = get_settings()
        _embeddings = OpenAIEmbeddings(api_key=settings.openai_api_key)
    return _embeddings


async def get_vector_store() -> PgVectorStore:
    """Get or create the vector store instance."""
    global _vector_store
    if _vector_store is None:
        from undertow.config import get_settings
        settings = get_settings()
        embeddings = get_embeddings()
        _vector_store = PgVectorStore(
            embeddings=embeddings,
            connection_string=settings.database_url,
        )
        await _vector_store.initialize()
    return _vector_store


__all__ = [
    # Classes
    "OpenAIEmbeddings",
    "EmbeddingResult",
    "BatchEmbeddingResult",
    "PgVectorStore",
    "Document",
    "SearchResult",
    # Factory functions
    "get_embeddings",
    "get_vector_store",
]
