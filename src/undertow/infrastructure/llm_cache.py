"""
LLM response caching layer.

Caches LLM responses to reduce costs and latency for repeated queries.
Uses content-addressable storage with hash-based keys.
"""

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any

import structlog

from undertow.infrastructure.cache import get_cache

logger = structlog.get_logger()


@dataclass
class CachedResponse:
    """A cached LLM response."""

    content: str
    model: str
    input_tokens: int
    output_tokens: int
    cached_at: float
    ttl: int


class LLMCache:
    """
    LLM response cache with content-addressable storage.

    Uses a hash of the prompt + model to create cache keys.
    Supports TTL-based expiration.

    Example:
        cache = LLMCache()

        # Check cache
        cached = await cache.get(messages, model)
        if cached:
            return cached.content

        # Get from LLM...
        response = await llm.complete(messages, model)

        # Store in cache
        await cache.set(messages, model, response.content, response.input_tokens, response.output_tokens)
    """

    DEFAULT_TTL = 3600 * 24  # 24 hours

    def __init__(self, prefix: str = "llm:", ttl: int = DEFAULT_TTL) -> None:
        """
        Initialize LLM cache.

        Args:
            prefix: Cache key prefix
            ttl: Default TTL in seconds
        """
        self.prefix = prefix
        self.default_ttl = ttl
        self._cache = get_cache()

        # Stats
        self.hits = 0
        self.misses = 0

    async def get(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float = 0.7,
    ) -> CachedResponse | None:
        """
        Get cached response for messages.

        Args:
            messages: Chat messages
            model: Model identifier
            temperature: Temperature (affects cache key)

        Returns:
            CachedResponse or None if not cached
        """
        # Don't cache high-temperature requests (more random)
        if temperature > 0.8:
            return None

        key = self._make_key(messages, model, temperature)

        try:
            data = await self._cache.get(key)
            if data:
                cached = CachedResponse(**json.loads(data))

                # Check if still valid
                age = time.time() - cached.cached_at
                if age < cached.ttl:
                    self.hits += 1
                    logger.debug(
                        "LLM cache hit",
                        model=model,
                        age_seconds=int(age),
                    )
                    return cached

            self.misses += 1
            return None

        except Exception as e:
            logger.warning("LLM cache get failed", error=str(e))
            self.misses += 1
            return None

    async def set(
        self,
        messages: list[dict[str, str]],
        model: str,
        content: str,
        input_tokens: int,
        output_tokens: int,
        temperature: float = 0.7,
        ttl: int | None = None,
    ) -> bool:
        """
        Cache an LLM response.

        Args:
            messages: Chat messages
            model: Model identifier
            content: Response content
            input_tokens: Input token count
            output_tokens: Output token count
            temperature: Temperature used
            ttl: TTL override

        Returns:
            True if cached successfully
        """
        # Don't cache high-temperature responses
        if temperature > 0.8:
            return False

        key = self._make_key(messages, model, temperature)
        ttl = ttl or self.default_ttl

        try:
            cached = CachedResponse(
                content=content,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cached_at=time.time(),
                ttl=ttl,
            )

            await self._cache.set(key, json.dumps(cached.__dict__), ttl=ttl)

            logger.debug(
                "LLM response cached",
                model=model,
                tokens=input_tokens + output_tokens,
                ttl=ttl,
            )
            return True

        except Exception as e:
            logger.warning("LLM cache set failed", error=str(e))
            return False

    def _make_key(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float,
    ) -> str:
        """
        Create cache key from messages and model.

        Uses SHA-256 hash for content addressing.
        """
        # Create deterministic string representation
        content = json.dumps(
            {
                "messages": messages,
                "model": model,
                "temperature": round(temperature, 2),
            },
            sort_keys=True,
        )

        # Hash for fixed-length key
        hash_value = hashlib.sha256(content.encode()).hexdigest()[:32]

        return f"{self.prefix}{model}:{hash_value}"

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0

        return {
            "hits": self.hits,
            "misses": self.misses,
            "total": total,
            "hit_rate": round(hit_rate, 3),
        }

    def reset_stats(self) -> None:
        """Reset statistics."""
        self.hits = 0
        self.misses = 0


# Global cache instance
_llm_cache: LLMCache | None = None


def get_llm_cache() -> LLMCache:
    """Get global LLM cache instance."""
    global _llm_cache
    if _llm_cache is None:
        _llm_cache = LLMCache()
    return _llm_cache

