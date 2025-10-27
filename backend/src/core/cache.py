"""
Redis caching utilities for response caching and performance optimization.
Implements T259 from tasks.md.
"""

import functools
import hashlib
import json
import logging
from collections.abc import Callable
from typing import Any

import redis
from redis.exceptions import RedisError

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class CacheService:
    """Redis-based caching service with automatic serialization and TTL management."""

    def __init__(self):
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis cache service initialized successfully")
            self._enabled = True
        except RedisError as e:
            logger.warning(f"Redis connection failed: {e}. Caching disabled.")
            self.redis_client = None
            self._enabled = False

    def is_enabled(self) -> bool:
        """Check if caching is enabled and Redis is available."""
        return self._enabled and self.redis_client is not None

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate a cache key from function arguments.

        Args:
            prefix: Key prefix (usually function name)
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Cache key string
        """
        # Create a unique key from arguments
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_string = ":".join(key_parts)

        # Hash if too long
        if len(key_string) > 100:
            key_hash = hashlib.md5(key_string.encode()).hexdigest()
            return f"cache:{prefix}:{key_hash}"

        return f"cache:{prefix}:{key_string}" if key_string else f"cache:{prefix}"

    def get(self, key: str) -> Any | None:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not self.is_enabled():
            return None

        try:
            value = self.redis_client.get(key)
            if value is None:
                return None

            # Deserialize JSON
            return json.loads(value)
        except (RedisError, json.JSONDecodeError) as e:
            logger.warning(f"Cache get error for key '{key}': {e}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> bool:
        """
        Set value in cache with optional TTL.

        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            ttl: Time-to-live in seconds (None = no expiration)

        Returns:
            True if successful, False otherwise
        """
        if not self.is_enabled():
            return False

        try:
            # Serialize to JSON
            serialized = json.dumps(value, default=str)

            if ttl:
                self.redis_client.setex(key, ttl, serialized)
            else:
                self.redis_client.set(key, serialized)

            return True
        except (RedisError, TypeError, ValueError) as e:
            logger.warning(f"Cache set error for key '{key}': {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if successful, False otherwise
        """
        if not self.is_enabled():
            return False

        try:
            self.redis_client.delete(key)
            return True
        except RedisError as e:
            logger.warning(f"Cache delete error for key '{key}': {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Args:
            pattern: Redis pattern (e.g., "cache:analytics:*")

        Returns:
            Number of keys deleted
        """
        if not self.is_enabled():
            return 0

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except RedisError as e:
            logger.warning(f"Cache delete pattern error for '{pattern}': {e}")
            return 0

    def clear_all(self) -> bool:
        """
        Clear all cache entries.

        ⚠️ WARNING: This clears ALL keys in the Redis database.
        Use with caution in production.

        Returns:
            True if successful, False otherwise
        """
        if not self.is_enabled():
            return False

        try:
            self.redis_client.flushdb()
            logger.info("All cache cleared")
            return True
        except RedisError as e:
            logger.error(f"Cache clear error: {e}")
            return False


# Global cache service instance
_cache_service: CacheService | None = None


def get_cache_service() -> CacheService:
    """Get or create the global cache service instance."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


def cached(
    ttl: int = 300,
    key_prefix: str | None = None,
    invalidate_on: list[str] | None = None,
):
    """
    Decorator to cache function results in Redis.

    Args:
        ttl: Time-to-live in seconds (default: 5 minutes)
        key_prefix: Custom key prefix (default: function name)
        invalidate_on: List of cache patterns to invalidate when this function is called

    Usage:
        @cached(ttl=600)
        async def get_analytics(user_id: str, date_range: str):
            # Expensive computation
            return result

    Example with invalidation:
        @cached(ttl=3600, invalidate_on=["cache:analytics:*"])
        async def create_payment(payment_data):
            # This will invalidate all analytics caches when called
            return payment
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache = get_cache_service()

            # Generate cache key
            prefix = key_prefix or func.__name__
            cache_key = cache._generate_key(prefix, *args, **kwargs)

            # Try to get from cache
            if cache.is_enabled():
                cached_value = cache.get(cache_key)
                if cached_value is not None:
                    logger.debug(f"Cache HIT: {cache_key}")
                    return cached_value
                logger.debug(f"Cache MISS: {cache_key}")

            # Call function
            result = await func(*args, **kwargs)

            # Cache result
            if cache.is_enabled():
                cache.set(cache_key, result, ttl)
                logger.debug(f"Cache SET: {cache_key} (TTL: {ttl}s)")

            # Invalidate specified patterns
            if invalidate_on and cache.is_enabled():
                for pattern in invalidate_on:
                    deleted = cache.delete_pattern(pattern)
                    if deleted > 0:
                        logger.debug(f"Cache invalidated: {pattern} ({deleted} keys)")

            return result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache = get_cache_service()

            # Generate cache key
            prefix = key_prefix or func.__name__
            cache_key = cache._generate_key(prefix, *args, **kwargs)

            # Try to get from cache
            if cache.is_enabled():
                cached_value = cache.get(cache_key)
                if cached_value is not None:
                    logger.debug(f"Cache HIT: {cache_key}")
                    return cached_value
                logger.debug(f"Cache MISS: {cache_key}")

            # Call function
            result = func(*args, **kwargs)

            # Cache result
            if cache.is_enabled():
                cache.set(cache_key, result, ttl)
                logger.debug(f"Cache SET: {cache_key} (TTL: {ttl}s)")

            # Invalidate specified patterns
            if invalidate_on and cache.is_enabled():
                for pattern in invalidate_on:
                    deleted = cache.delete_pattern(pattern)
                    if deleted > 0:
                        logger.debug(f"Cache invalidated: {pattern} ({deleted} keys)")

            return result

        # Return appropriate wrapper based on function type
        if functools.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def invalidate_cache(pattern: str) -> int:
    """
    Invalidate cache entries matching a pattern.

    Args:
        pattern: Redis pattern (e.g., "cache:analytics:*")

    Returns:
        Number of keys deleted
    """
    cache = get_cache_service()
    return cache.delete_pattern(pattern)


# Cache configuration presets
CACHE_TTL = {
    "short": 60,  # 1 minute - frequently changing data
    "medium": 300,  # 5 minutes - default
    "long": 900,  # 15 minutes - semi-static data
    "hour": 3600,  # 1 hour - relatively static data
    "day": 86400,  # 24 hours - rarely changing data
}
