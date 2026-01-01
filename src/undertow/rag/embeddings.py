"""
Embedding generation for RAG.

Supports multiple embedding providers with fallback.
"""

import asyncio
import hashlib
from typing import Literal

import structlog

from undertow.config import settings
from undertow.infrastructure.cache import get_cache

logger = structlog.get_logger()


class EmbeddingProvider:
    """
    Multi-provider embedding generation with caching.

    Supports:
    - OpenAI text-embedding-3-small (1536 dims, $0.02/1M tokens)
    - OpenAI text-embedding-3-large (3072 dims, $0.13/1M tokens)
    - Voyage AI voyage-large-2 (1536 dims, better for retrieval)

    Example:
        provider = EmbeddingProvider()
        embedding = await provider.embed("What is the capital of France?")
        embeddings = await provider.embed_batch(["text1", "text2", "text3"])
    """

    MODELS = {
        "openai-small": {
            "name": "text-embedding-3-small",
            "dimensions": 1536,
            "max_tokens": 8191,
            "cost_per_1m": 0.02,
        },
        "openai-large": {
            "name": "text-embedding-3-large",
            "dimensions": 3072,
            "max_tokens": 8191,
            "cost_per_1m": 0.13,
        },
    }

    def __init__(
        self,
        model: Literal["openai-small", "openai-large"] = "openai-small",
        cache_embeddings: bool = True,
    ) -> None:
        """
        Initialize embedding provider.

        Args:
            model: Which embedding model to use
            cache_embeddings: Whether to cache embeddings
        """
        self.model_key = model
        self.model_config = self.MODELS[model]
        self.cache_embeddings = cache_embeddings
        self._cache = get_cache() if cache_embeddings else None
        self._client: "openai.AsyncOpenAI | None" = None

        # Stats
        self.total_tokens = 0
        self.total_requests = 0
        self.cache_hits = 0

    async def _get_client(self) -> "openai.AsyncOpenAI":
        """Get or create OpenAI client."""
        if self._client is None:
            import openai

            self._client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        return self._client

    async def embed(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            List of floats (embedding vector)
        """
        # Check cache
        if self._cache:
            cache_key = self._cache_key(text)
            cached = await self._cache.get(cache_key)
            if cached:
                import json
                self.cache_hits += 1
                return json.loads(cached)

        # Generate embedding
        client = await self._get_client()

        response = await client.embeddings.create(
            model=self.model_config["name"],
            input=text,
        )

        embedding = response.data[0].embedding
        self.total_tokens += response.usage.total_tokens
        self.total_requests += 1

        # Cache result
        if self._cache:
            import json
            await self._cache.set(
                cache_key,
                json.dumps(embedding),
                ttl=86400 * 7,  # 7 days
            )

        return embedding

    async def embed_batch(
        self,
        texts: list[str],
        batch_size: int = 100,
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: Texts to embed
            batch_size: Batch size for API calls

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        all_embeddings: list[list[float]] = []
        uncached_indices: list[int] = []
        uncached_texts: list[str] = []

        # Check cache for all texts
        if self._cache:
            for i, text in enumerate(texts):
                cache_key = self._cache_key(text)
                cached = await self._cache.get(cache_key)
                if cached:
                    import json
                    all_embeddings.append(json.loads(cached))
                    self.cache_hits += 1
                else:
                    all_embeddings.append([])  # Placeholder
                    uncached_indices.append(i)
                    uncached_texts.append(text)
        else:
            uncached_indices = list(range(len(texts)))
            uncached_texts = texts
            all_embeddings = [[] for _ in texts]

        # Generate embeddings for uncached texts
        if uncached_texts:
            client = await self._get_client()

            for i in range(0, len(uncached_texts), batch_size):
                batch = uncached_texts[i : i + batch_size]

                response = await client.embeddings.create(
                    model=self.model_config["name"],
                    input=batch,
                )

                self.total_tokens += response.usage.total_tokens
                self.total_requests += 1

                # Store results
                for j, embedding_data in enumerate(response.data):
                    original_idx = uncached_indices[i + j]
                    embedding = embedding_data.embedding
                    all_embeddings[original_idx] = embedding

                    # Cache
                    if self._cache:
                        import json
                        cache_key = self._cache_key(uncached_texts[i + j])
                        await self._cache.set(
                            cache_key,
                            json.dumps(embedding),
                            ttl=86400 * 7,
                        )

        return all_embeddings

    def _cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        return f"emb:{self.model_key}:{text_hash}"

    @property
    def dimensions(self) -> int:
        """Get embedding dimensions."""
        return self.model_config["dimensions"]

    @property
    def estimated_cost(self) -> float:
        """Estimate cost based on tokens used."""
        return (self.total_tokens / 1_000_000) * self.model_config["cost_per_1m"]

    def get_stats(self) -> dict:
        """Get usage statistics."""
        return {
            "model": self.model_key,
            "total_tokens": self.total_tokens,
            "total_requests": self.total_requests,
            "cache_hits": self.cache_hits,
            "estimated_cost_usd": round(self.estimated_cost, 4),
        }


# Global instance
_embedding_provider: EmbeddingProvider | None = None


def get_embedding_provider() -> EmbeddingProvider:
    """Get global embedding provider."""
    global _embedding_provider
    if _embedding_provider is None:
        _embedding_provider = EmbeddingProvider()
    return _embedding_provider

