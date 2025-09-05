"""Tests for Fantasy Nerds Redis cache implementation."""

import json
from unittest.mock import patch, MagicMock
import pytest
from redis.exceptions import RedisError

from ffnerd.cache import FantasyNerdsCache


@pytest.fixture
def cache():
    """Create a cache instance for testing."""
    with patch("ffnerd.cache.redis.from_url") as mock_redis:
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        cache = FantasyNerdsCache()
        cache._redis_client = mock_client
        yield cache


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client."""
    return MagicMock()


class TestFantasyNerdsCache:
    """Test suite for Fantasy Nerds cache."""

    def test_initialization(self):
        """Test cache initialization."""
        cache = FantasyNerdsCache()
        assert cache.redis_url == "redis://localhost:6379"
        assert cache._redis_client is None
        assert cache._stats["hits"] == 0
        assert cache._stats["misses"] == 0

    def test_custom_redis_url(self):
        """Test initialization with custom Redis URL."""
        custom_url = "redis://custom:6379"
        cache = FantasyNerdsCache(redis_url=custom_url)
        assert cache.redis_url == custom_url

    def test_compression_decompression(self, cache):
        """Test data compression and decompression."""
        test_data = {
            "players": [{"id": 1, "name": "Player 1"} for _ in range(100)],
            "metadata": {"timestamp": "2024-01-01", "version": "1.0"},
        }

        # Compress
        compressed = cache._compress_data(test_data)
        assert isinstance(compressed, bytes)

        # Verify compression reduces size
        original_size = len(json.dumps(test_data))
        compressed_size = len(compressed)
        assert compressed_size < original_size
        compression_ratio = (1 - compressed_size / original_size) * 100
        assert compression_ratio > 50  # Should achieve >50% compression

        # Decompress
        decompressed = cache._decompress_data(compressed)
        assert decompressed == test_data

    def test_backwards_compatibility(self, cache):
        """Test decompression handles uncompressed JSON (backwards compatibility)."""
        test_data = {"key": "value"}
        json_bytes = json.dumps(test_data).encode()

        # Should handle uncompressed data
        result = cache._decompress_data(json_bytes)
        assert result == test_data

    def test_make_key(self, cache):
        """Test cache key generation."""
        # Single part
        key = cache._make_key("test")
        assert key == "ffnerd:test"

        # Multiple parts
        key = cache._make_key("projections", "week_1", "ppr")
        assert key == "ffnerd:projections:week_1:ppr"

    def test_store_and_get_mapping(self, cache):
        """Test storing and retrieving player ID mapping."""
        mapping = {"12345": 6789, "67890": 1234}

        # Store mapping
        cache._redis_client.setex.return_value = True
        result = cache.store_mapping(mapping)
        assert result is True

        # Verify Redis call
        cache._redis_client.setex.assert_called_once()
        call_args = cache._redis_client.setex.call_args[0]
        assert call_args[0] == "ffnerd:mapping"
        assert call_args[1] == 86400  # 24 hours TTL

        # Get mapping
        compressed_data = cache._compress_data(mapping)
        cache._redis_client.get.return_value = compressed_data
        retrieved = cache.get_mapping()
        assert retrieved == mapping
        assert cache._stats["hits"] == 1

    def test_store_and_get_projections(self, cache):
        """Test storing and retrieving projections."""
        projections = [
            {"player_id": 1, "points": 20.5},
            {"player_id": 2, "points": 15.3},
        ]

        # Store projections
        cache._redis_client.setex.return_value = True
        result = cache.store_projections(week=1, data=projections, scoring="PPR")
        assert result is True

        # Verify key format
        call_args = cache._redis_client.setex.call_args[0]
        assert call_args[0] == "ffnerd:projections:week_1:ppr"
        assert call_args[1] == 7200  # 2 hours TTL

        # Get projections
        compressed_data = cache._compress_data(projections)
        cache._redis_client.get.return_value = compressed_data
        retrieved = cache.get_projections(week=1, scoring="PPR")
        assert retrieved == projections

    def test_store_and_get_injuries(self, cache):
        """Test storing and retrieving injury data."""
        injuries = [
            {"player": "Player 1", "status": "Questionable"},
            {"player": "Player 2", "status": "Out"},
        ]

        # Store injuries
        cache._redis_client.setex.return_value = True
        result = cache.store_injuries(injuries)
        assert result is True

        call_args = cache._redis_client.setex.call_args[0]
        assert call_args[0] == "ffnerd:injuries:current"
        assert call_args[1] == 3600  # 1 hour TTL

        # Get injuries
        compressed_data = cache._compress_data(injuries)
        cache._redis_client.get.return_value = compressed_data
        retrieved = cache.get_injuries()
        assert retrieved == injuries

    def test_store_and_get_news(self, cache):
        """Test storing and retrieving news."""
        news = [
            {"title": "Breaking News", "content": "Important update"},
            {"title": "Trade Alert", "content": "Player traded"},
        ]

        # Store news
        cache._redis_client.setex.return_value = True
        result = cache.store_news(news)
        assert result is True

        call_args = cache._redis_client.setex.call_args[0]
        assert call_args[0] == "ffnerd:news:recent"
        assert call_args[1] == 1800  # 30 minutes TTL

        # Get news
        compressed_data = cache._compress_data(news)
        cache._redis_client.get.return_value = compressed_data
        retrieved = cache.get_news()
        assert retrieved == news

    def test_store_and_get_rankings(self, cache):
        """Test storing and retrieving rankings."""
        rankings = [
            {"player": "Player 1", "rank": 1},
            {"player": "Player 2", "rank": 2},
        ]

        # Weekly rankings with position
        cache._redis_client.setex.return_value = True
        result = cache.store_rankings(
            week=5, scoring="PPR", position="QB", data=rankings
        )
        assert result is True

        call_args = cache._redis_client.setex.call_args[0]
        assert call_args[0] == "ffnerd:rankings:week_5:ppr:qb"

        # Season rankings without position
        result = cache.store_rankings(
            week=None, scoring="STD", position=None, data=rankings
        )
        call_args = cache._redis_client.setex.call_args[0]
        assert call_args[0] == "ffnerd:rankings:season:std"

    def test_store_and_get_player_enrichment(self, cache):
        """Test storing and retrieving player enrichment data."""
        enrichment = {
            "projections": {"points": 20.5},
            "injury": {"status": "Healthy"},
            "news": [{"title": "Player Update"}],
        }

        sleeper_id = "12345"

        # Store enrichment
        cache._redis_client.setex.return_value = True
        result = cache.store_player_enrichment(sleeper_id, enrichment)
        assert result is True

        call_args = cache._redis_client.setex.call_args[0]
        assert call_args[0] == f"ffnerd:enrichment:{sleeper_id}"
        assert call_args[1] == 3600  # 1 hour TTL

        # Get enrichment
        # Need to include the cached_at field that's added
        stored_data = enrichment.copy()
        stored_data["cached_at"] = "2024-01-01T00:00:00"
        compressed_data = cache._compress_data(stored_data)
        cache._redis_client.get.return_value = compressed_data
        retrieved = cache.get_player_enrichment(sleeper_id)
        assert "cached_at" in retrieved
        assert retrieved["projections"] == enrichment["projections"]

    def test_cache_miss(self, cache):
        """Test cache miss behavior."""
        cache._redis_client.get.return_value = None

        result = cache.get_projections(week=1)
        assert result is None
        assert cache._stats["misses"] == 1
        assert cache._stats["hits"] == 0

    def test_redis_error_handling(self, cache):
        """Test handling of Redis errors."""
        # Test storage error
        cache._redis_client.setex.side_effect = RedisError("Connection failed")
        result = cache.store_mapping({"test": 123})
        assert result is False
        assert cache._stats["errors"] == 1
        assert "Connection failed" in cache._stats["last_error"]

        # Test retrieval error
        cache._redis_client.get.side_effect = RedisError("Read error")
        result = cache.get_mapping()
        assert result is None
        assert cache._stats["errors"] == 2

    def test_invalidate_cache(self, cache):
        """Test cache invalidation."""
        # Mock scan_iter to return some keys
        mock_keys = [
            b"ffnerd:projections:week_1:ppr",
            b"ffnerd:projections:week_2:ppr",
            b"ffnerd:injuries:current",
        ]
        cache._redis_client.scan_iter.return_value = iter(mock_keys)
        cache._redis_client.delete.return_value = 1

        # Invalidate projections only
        deleted = cache.invalidate_cache("projections:*")
        assert deleted == 3  # All keys would match in this mock

        # Verify scan was called with correct pattern
        cache._redis_client.scan_iter.assert_called_with(
            match="ffnerd:projections:*", count=100
        )

    def test_invalidate_all_cache(self, cache):
        """Test invalidating all Fantasy Nerds cache."""
        mock_keys = [
            b"ffnerd:mapping",
            b"ffnerd:projections:week_1:ppr",
            b"ffnerd:injuries:current",
        ]
        cache._redis_client.scan_iter.return_value = iter(mock_keys)
        cache._redis_client.delete.return_value = 1

        deleted = cache.invalidate_cache()
        assert deleted == 3
        cache._redis_client.scan_iter.assert_called_with(match="ffnerd:*", count=100)

    def test_get_cache_status(self, cache):
        """Test cache status reporting."""
        # Set up mock data
        mock_keys = [
            b"ffnerd:mapping",
            b"ffnerd:projections:week_1:ppr",
            b"ffnerd:injuries:current",
            b"ffnerd:news:recent",
            b"ffnerd:enrichment:12345",
        ]
        cache._redis_client.scan_iter.return_value = iter(mock_keys)
        cache._redis_client.memory_usage.return_value = 1024 * 100  # 100KB per key
        cache._redis_client.info.return_value = {
            "used_memory": 50 * 1024 * 1024,  # 50MB
            "used_memory_peak": 100 * 1024 * 1024,  # 100MB
        }

        # Set some stats
        cache._stats["hits"] = 80
        cache._stats["misses"] = 20

        status = cache.get_cache_status()

        assert status["healthy"] is True
        assert status["total_keys"] == 5
        assert status["key_categories"]["mapping"] == 1
        assert status["key_categories"]["projections"] == 1
        assert status["key_categories"]["injuries"] == 1
        assert status["key_categories"]["news"] == 1
        assert status["key_categories"]["enrichment"] == 1
        assert status["stats"]["hit_rate_pct"] == 80.0
        assert status["redis_memory_used_mb"] == 50.0

    def test_get_cache_status_error(self, cache):
        """Test cache status when Redis connection fails."""
        cache._redis_client.scan_iter.side_effect = RedisError("Connection lost")

        status = cache.get_cache_status()
        assert status["healthy"] is False
        assert "Connection lost" in status["error"]

    def test_get_ttl(self, cache):
        """Test getting TTL for cached items."""
        cache._redis_client.ttl.return_value = 3600

        # Test mapping TTL
        ttl = cache.get_ttl("mapping")
        assert ttl == 3600
        cache._redis_client.ttl.assert_called_with("ffnerd:mapping")

        # Test projections TTL with parameters
        ttl = cache.get_ttl("projections", week=5, scoring="PPR")
        cache._redis_client.ttl.assert_called_with("ffnerd:projections:week_5:ppr")

        # Test non-existent key
        cache._redis_client.ttl.return_value = -2
        ttl = cache.get_ttl("injuries")
        assert ttl is None

    def test_warmup_cache_placeholder(self, cache):
        """Test cache warmup placeholder method."""
        results = cache.warmup_cache(["projections", "injuries"])
        assert results["projections"] is False
        assert results["injuries"] is False

        # Test with default data types
        results = cache.warmup_cache()
        assert len(results) == 5
        assert all(not success for success in results.values())

    def test_large_data_compression(self, cache):
        """Test compression effectiveness on large datasets."""
        # Create a large dataset similar to real NFL data
        large_data = {
            "players": [
                {
                    "id": i,
                    "name": f"Player {i}",
                    "team": "Team",
                    "position": "QB",
                    "stats": {"yards": 3000 + i, "touchdowns": 20 + i % 10},
                    "projections": {
                        "week_1": 20.5 + i % 5,
                        "week_2": 22.3 + i % 3,
                    },
                }
                for i in range(500)
            ]
        }

        compressed = cache._compress_data(large_data)
        original_size = len(json.dumps(large_data))
        compressed_size = len(compressed)

        # Should achieve significant compression on repetitive data
        compression_ratio = (1 - compressed_size / original_size) * 100
        assert compression_ratio > 60

        # Verify data integrity after decompression
        decompressed = cache._decompress_data(compressed)
        assert decompressed == large_data
        assert len(decompressed["players"]) == 500

    @pytest.mark.parametrize(
        "data_type,expected_ttl",
        [
            ("mapping", 86400),
            ("projections", 7200),
            ("injuries", 3600),
            ("news", 1800),
            ("rankings", 7200),
            ("enrichment", 3600),
        ],
    )
    def test_ttl_values(self, cache, data_type, expected_ttl):
        """Test that correct TTL values are used for different data types."""
        test_data = {"test": "data"}

        # Call the appropriate store method
        if data_type == "mapping":
            cache.store_mapping(test_data)
        elif data_type == "projections":
            cache.store_projections(1, test_data)
        elif data_type == "injuries":
            cache.store_injuries([test_data])
        elif data_type == "news":
            cache.store_news([test_data])
        elif data_type == "rankings":
            cache.store_rankings(1, "PPR", None, [test_data])
        elif data_type == "enrichment":
            cache.store_player_enrichment("12345", test_data)

        # Verify TTL was set correctly
        call_args = cache._redis_client.setex.call_args[0]
        assert call_args[1] == expected_ttl
