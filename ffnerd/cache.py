"""Redis caching layer for Fantasy Nerds data."""

import json
import os
import gzip
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import redis
from redis.exceptions import RedisError
import logging

logger = logging.getLogger(__name__)

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
DEFAULT_CACHE_TTL = int(os.getenv("FFNERD_CACHE_TTL", "7200"))  # 2 hours
COMPRESSION_LEVEL = int(os.getenv("FFNERD_CACHE_COMPRESSION_LEVEL", "9"))
KEY_PREFIX = os.getenv("FFNERD_CACHE_KEY_PREFIX", "ffnerd")

# Cache TTLs for different data types
TTL_MAPPING = 86400  # 24 hours for player mapping
TTL_PROJECTIONS = 7200  # 2 hours for projections
TTL_INJURIES = 3600  # 1 hour for injuries (more frequent updates)
TTL_NEWS = 1800  # 30 minutes for news (most frequent)
TTL_RANKINGS = 7200  # 2 hours for rankings
TTL_ENRICHMENT = 3600  # 1 hour for player enrichment


class FantasyNerdsCache:
    """Redis cache for Fantasy Nerds fantasy football data."""

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize the cache with Redis connection.

        Args:
            redis_url: Redis connection URL. Uses REDIS_URL env var if not provided.
        """
        self.redis_url = redis_url or REDIS_URL
        self._redis_client = None
        self._stats = {
            "hits": 0,
            "misses": 0,
            "errors": 0,
            "last_error": None,
        }

    def get_redis_client(self) -> redis.Redis:
        """Get Redis client with connection pooling."""
        if self._redis_client is None:
            self._redis_client = redis.from_url(
                self.redis_url,
                decode_responses=False,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                max_connections=10,
            )
        return self._redis_client

    def _compress_data(self, data: Any) -> bytes:
        """
        Compress data using gzip.

        Args:
            data: Data to compress (will be JSON serialized).

        Returns:
            Compressed bytes.
        """
        json_str = json.dumps(data)
        return gzip.compress(json_str.encode(), compresslevel=COMPRESSION_LEVEL)

    def _decompress_data(self, compressed: bytes) -> Any:
        """
        Decompress gzipped data.

        Args:
            compressed: Compressed bytes.

        Returns:
            Decompressed and deserialized data.
        """
        try:
            decompressed = gzip.decompress(compressed)
            return json.loads(decompressed)
        except gzip.BadGzipFile:
            # Try parsing as uncompressed JSON (backwards compatibility)
            return json.loads(compressed)

    def _make_key(self, *parts: str) -> str:
        """
        Create a cache key from parts.

        Args:
            parts: Key components to join.

        Returns:
            Full cache key.
        """
        return ":".join([KEY_PREFIX] + list(parts))

    def _set_with_compression(
        self, key: str, data: Any, ttl: int = DEFAULT_CACHE_TTL
    ) -> bool:
        """
        Store data with compression and TTL.

        Args:
            key: Cache key.
            data: Data to store.
            ttl: Time to live in seconds.

        Returns:
            True if stored successfully.
        """
        try:
            r = self.get_redis_client()
            compressed = self._compress_data(data)

            # Log compression stats
            original_size = len(json.dumps(data))
            compressed_size = len(compressed)
            compression_ratio = (1 - compressed_size / original_size) * 100

            logger.debug(
                f"Compression for {key}: {original_size} → {compressed_size} bytes "
                f"({compression_ratio:.1f}% reduction)"
            )

            r.setex(key, ttl, compressed)
            return True
        except RedisError as e:
            logger.error(f"Failed to set cache key {key}: {e}")
            self._stats["errors"] += 1
            self._stats["last_error"] = str(e)
            return False

    def _get_with_decompression(self, key: str) -> Optional[Any]:
        """
        Retrieve and decompress data from cache.

        Args:
            key: Cache key.

        Returns:
            Decompressed data or None if not found.
        """
        try:
            r = self.get_redis_client()
            compressed = r.get(key)

            if compressed is None:
                self._stats["misses"] += 1
                return None

            self._stats["hits"] += 1
            return self._decompress_data(compressed)
        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Failed to get cache key {key}: {e}")
            self._stats["errors"] += 1
            self._stats["last_error"] = str(e)
            return None

    # Storage methods
    def store_mapping(self, mapping: Dict[str, int]) -> bool:
        """
        Store player ID mapping (Sleeper ID → Fantasy Nerds ID).

        Args:
            mapping: Dictionary of sleeper_id to ffnerd_id.

        Returns:
            True if stored successfully.
        """
        key = self._make_key("mapping")
        return self._set_with_compression(key, mapping, TTL_MAPPING)

    def store_projections(
        self, week: int, data: Union[Dict, List], scoring: str = "PPR"
    ) -> bool:
        """
        Store weekly fantasy projections.

        Args:
            week: NFL week number.
            data: Projections data.
            scoring: Scoring type (PPR, HALF, STD).

        Returns:
            True if stored successfully.
        """
        key = self._make_key("projections", f"week_{week}", scoring.lower())
        return self._set_with_compression(key, data, TTL_PROJECTIONS)

    def store_injuries(self, data: List[Dict[str, Any]]) -> bool:
        """
        Store current injury reports.

        Args:
            data: List of injury report entries.

        Returns:
            True if stored successfully.
        """
        key = self._make_key("injuries", "current")
        return self._set_with_compression(key, data, TTL_INJURIES)

    def store_news(self, data: List[Dict[str, Any]]) -> bool:
        """
        Store recent player news.

        Args:
            data: List of news articles.

        Returns:
            True if stored successfully.
        """
        key = self._make_key("news", "recent")
        return self._set_with_compression(key, data, TTL_NEWS)

    def store_rankings(
        self,
        week: Optional[int],
        scoring: str,
        position: Optional[str],
        data: List[Dict[str, Any]],
    ) -> bool:
        """
        Store expert consensus rankings.

        Args:
            week: NFL week number (None for season rankings).
            scoring: Scoring type (PPR, HALF, STD).
            position: Position filter (QB, RB, WR, TE, etc.) or None for overall.
            data: Rankings data.

        Returns:
            True if stored successfully.
        """
        parts = ["rankings"]
        if week:
            parts.append(f"week_{week}")
        else:
            parts.append("season")
        parts.append(scoring.lower())
        if position:
            parts.append(position.lower())

        key = self._make_key(*parts)
        return self._set_with_compression(key, data, TTL_RANKINGS)

    def store_player_enrichment(
        self, sleeper_id: str, enrichment_data: Dict[str, Any]
    ) -> bool:
        """
        Store combined enrichment data for a specific player.

        Args:
            sleeper_id: Sleeper player ID.
            enrichment_data: Combined data (projections, news, injuries, etc.).

        Returns:
            True if stored successfully.
        """
        key = self._make_key("enrichment", sleeper_id)
        enrichment_data["cached_at"] = datetime.now().isoformat()
        return self._set_with_compression(key, enrichment_data, TTL_ENRICHMENT)

    # Retrieval methods
    def get_mapping(self) -> Optional[Dict[str, int]]:
        """
        Get cached player ID mapping.

        Returns:
            Mapping dictionary or None if not cached.
        """
        key = self._make_key("mapping")
        return self._get_with_decompression(key)

    def get_projections(
        self, week: int, scoring: str = "PPR"
    ) -> Optional[Union[Dict, List]]:
        """
        Get cached weekly projections.

        Args:
            week: NFL week number.
            scoring: Scoring type.

        Returns:
            Projections data or None if not cached.
        """
        key = self._make_key("projections", f"week_{week}", scoring.lower())
        return self._get_with_decompression(key)

    def get_injuries(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached injury reports.

        Returns:
            List of injuries or None if not cached.
        """
        key = self._make_key("injuries", "current")
        return self._get_with_decompression(key)

    def get_news(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached news articles.

        Returns:
            List of news or None if not cached.
        """
        key = self._make_key("news", "recent")
        return self._get_with_decompression(key)

    def get_rankings(
        self, week: Optional[int], scoring: str, position: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached rankings.

        Args:
            week: NFL week number (None for season rankings).
            scoring: Scoring type.
            position: Position filter or None for overall.

        Returns:
            Rankings data or None if not cached.
        """
        parts = ["rankings"]
        if week:
            parts.append(f"week_{week}")
        else:
            parts.append("season")
        parts.append(scoring.lower())
        if position:
            parts.append(position.lower())

        key = self._make_key(*parts)
        return self._get_with_decompression(key)

    def get_player_enrichment(self, sleeper_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached enrichment data for a player.

        Args:
            sleeper_id: Sleeper player ID.

        Returns:
            Enrichment data or None if not cached.
        """
        key = self._make_key("enrichment", sleeper_id)
        return self._get_with_decompression(key)

    # Cache management methods
    def invalidate_cache(self, pattern: Optional[str] = None) -> int:
        """
        Clear cache keys matching pattern.

        Args:
            pattern: Key pattern to match (e.g., "projections:*").
                    If None, clears all Fantasy Nerds cache.

        Returns:
            Number of keys deleted.
        """
        try:
            r = self.get_redis_client()

            if pattern:
                search_pattern = self._make_key(pattern)
            else:
                search_pattern = self._make_key("*")

            # Use SCAN to avoid blocking on large keysets
            deleted = 0
            for key in r.scan_iter(match=search_pattern, count=100):
                r.delete(key)
                deleted += 1

            logger.info(f"Invalidated {deleted} cache keys matching {search_pattern}")
            return deleted
        except RedisError as e:
            logger.error(f"Failed to invalidate cache: {e}")
            return 0

    def get_cache_status(self) -> Dict[str, Any]:
        """
        Get comprehensive cache status and statistics.

        Returns:
            Dictionary with cache metrics and health status.
        """
        try:
            r = self.get_redis_client()

            # Get all Fantasy Nerds cache keys
            all_keys = list(r.scan_iter(match=self._make_key("*"), count=100))

            # Categorize keys
            key_categories = {
                "mapping": 0,
                "projections": 0,
                "injuries": 0,
                "news": 0,
                "rankings": 0,
                "enrichment": 0,
                "other": 0,
            }

            total_size = 0
            for key in all_keys:
                # Get size and TTL for each key
                try:
                    key_str = key.decode() if isinstance(key, bytes) else key
                    size = r.memory_usage(key) or 0
                    total_size += size

                    # Categorize
                    if "mapping" in key_str:
                        key_categories["mapping"] += 1
                    elif "projections" in key_str:
                        key_categories["projections"] += 1
                    elif "injuries" in key_str:
                        key_categories["injuries"] += 1
                    elif "news" in key_str:
                        key_categories["news"] += 1
                    elif "rankings" in key_str:
                        key_categories["rankings"] += 1
                    elif "enrichment" in key_str:
                        key_categories["enrichment"] += 1
                    else:
                        key_categories["other"] += 1
                except Exception:
                    pass

            # Calculate hit rate
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = (
                self._stats["hits"] / total_requests * 100 if total_requests > 0 else 0
            )

            # Get Redis memory info
            try:
                info = r.info("memory")
                redis_memory_mb = info.get("used_memory", 0) / (1024 * 1024)
                redis_peak_mb = info.get("used_memory_peak", 0) / (1024 * 1024)
            except Exception:
                redis_memory_mb = 0
                redis_peak_mb = 0

            return {
                "healthy": True,
                "total_keys": len(all_keys),
                "key_categories": key_categories,
                "total_size_mb": total_size / (1024 * 1024),
                "redis_memory_used_mb": redis_memory_mb,
                "redis_memory_peak_mb": redis_peak_mb,
                "stats": {
                    "hits": self._stats["hits"],
                    "misses": self._stats["misses"],
                    "hit_rate_pct": hit_rate,
                    "errors": self._stats["errors"],
                    "last_error": self._stats["last_error"],
                },
                "timestamp": datetime.now().isoformat(),
            }
        except RedisError as e:
            return {
                "healthy": False,
                "error": str(e),
                "stats": self._stats,
                "timestamp": datetime.now().isoformat(),
            }

    def get_ttl(self, cache_type: str, **kwargs) -> Optional[int]:
        """
        Get TTL (time to live) for a cached item.

        Args:
            cache_type: Type of cache (projections, injuries, news, etc.).
            **kwargs: Additional parameters for key construction.

        Returns:
            TTL in seconds, or None if key doesn't exist.
        """
        try:
            r = self.get_redis_client()

            # Build the key based on cache type
            if cache_type == "mapping":
                key = self._make_key("mapping")
            elif cache_type == "projections":
                week = kwargs.get("week", 1)
                scoring = kwargs.get("scoring", "PPR")
                key = self._make_key("projections", f"week_{week}", scoring.lower())
            elif cache_type == "injuries":
                key = self._make_key("injuries", "current")
            elif cache_type == "news":
                key = self._make_key("news", "recent")
            elif cache_type == "enrichment":
                sleeper_id = kwargs.get("sleeper_id", "")
                key = self._make_key("enrichment", sleeper_id)
            else:
                return None

            ttl = r.ttl(key)
            return ttl if ttl > 0 else None
        except RedisError:
            return None

    def warmup_cache(self, data_types: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        Pre-populate cache with specified data types.
        This is a placeholder for integration with the Fantasy Nerds client.

        Args:
            data_types: List of data types to warmup (projections, injuries, etc.).
                       If None, warms up all types.

        Returns:
            Dictionary indicating success for each data type.
        """
        if data_types is None:
            data_types = ["mapping", "projections", "injuries", "news", "rankings"]

        results = {}
        for data_type in data_types:
            # This would be integrated with the Fantasy Nerds client
            # to actually fetch and cache data
            results[data_type] = False
            logger.info(f"Warmup for {data_type} would be implemented here")

        return results
