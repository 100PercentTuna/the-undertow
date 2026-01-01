"""
Redis caching infrastructure.
"""

from typing import Any

import redis.asyncio as redis
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from undertow.config import settings

logger = structlog.get_logger()

# Global Redis client
_redis: redis.Redis | None = None


async def init_cache() -> None:
    """
    Initialize Redis connection.

    Should be called during application startup.
    """
    global _redis

    _redis = redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )

    # Test connection
    await _redis.ping()
    logger.info("Redis connection established")


async def close_cache() -> None:
    """
    Close Redis connection.

    Should be called during application shutdown.
    """
    global _redis

    if _redis:
        await _redis.close()
        _redis = None
        logger.info("Redis connection closed")


def get_redis() -> redis.Redis:
    """Get the global Redis client."""
    if _redis is None:
        raise RuntimeError("Redis not initialized. Call init_cache() first.")
    return _redis


class CacheService:
    """
    High-level caching service.

    Provides typed caching operations with automatic serialization.
    """

    def __init__(self, prefix: str = "undertow") -> None:
        """
        Initialize cache service.

        Args:
            prefix: Key prefix for all cache keys
        """
        self.prefix = prefix

    def _make_key(self, key: str) -> str:
        """Create prefixed cache key."""
        return f"{self.prefix}:{key}"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=5),
    )
    async def get(self, key: str) -> str | None:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        client = get_redis()
        full_key = self._make_key(key)

        try:
            value = await client.get(full_key)
            return value
        except Exception as e:
            logger.warning("Cache get error", key=key, error=str(e))
            return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=5),
    )
    async def set(
        self,
        key: str,
        value: str,
        ttl_seconds: int = 3600,
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time-to-live in seconds

        Returns:
            True if successful
        """
        client = get_redis()
        full_key = self._make_key(key)

        try:
            await client.set(full_key, value, ex=ttl_seconds)
            return True
        except Exception as e:
            logger.warning("Cache set error", key=key, error=str(e))
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted
        """
        client = get_redis()
        full_key = self._make_key(key)

        try:
            result = await client.delete(full_key)
            return result > 0
        except Exception as e:
            logger.warning("Cache delete error", key=key, error=str(e))
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if exists
        """
        client = get_redis()
        full_key = self._make_key(key)

        try:
            result = await client.exists(full_key)
            return result > 0
        except Exception as e:
            logger.warning("Cache exists error", key=key, error=str(e))
            return False

    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment a counter in cache.

        Args:
            key: Cache key
            amount: Amount to increment by

        Returns:
            New value
        """
        client = get_redis()
        full_key = self._make_key(key)

        try:
            result = await client.incrby(full_key, amount)
            return result
        except Exception as e:
            logger.warning("Cache increment error", key=key, error=str(e))
            return 0

