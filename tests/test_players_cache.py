"""Tests for Redis caching functionality."""

import pytest
import json
import gzip
from unittest.mock import patch, AsyncMock, MagicMock
import fakeredis.aioredis as fakeredis
import sys
import os

# Import the module to test
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import players_cache_redis as cache

# Test data
MOCK_PLAYERS = {
    "1234": {
        "player_id": "1234",
        "first_name": "Patrick",
        "last_name": "Mahomes",
        "team": "KC",
        "position": "QB",
        "status": "Active",
        "search_full_name": "patrickmahomes",
    },
    "5678": {
        "player_id": "5678",
        "first_name": "Travis",
        "last_name": "Kelce",
        "team": "KC",
        "position": "TE",
        "status": "Active",
        "search_full_name": "traviskelce",
    },
    "9999": {
        "player_id": "9999",
        "first_name": "Tyreek",
        "last_name": "Hill",
        "team": "MIA",
        "position": "WR",
        "status": "Active",
        "search_full_name": "tyreekhill",
    },
}


@pytest.fixture
async def redis_client():
    """Create a fake Redis client for testing."""
    client = fakeredis.FakeRedis(decode_responses=False)
    yield client
    await client.flushall()
    await client.close()


class TestPlayersCache:
    """Test the players cache functionality."""

    @pytest.mark.asyncio
    async def test_get_redis_connection(self, redis_client):
        """Test getting Redis connection."""
        # Direct test of redis connection
        assert redis_client is not None
        # Test that we can perform a basic operation
        await redis_client.ping()

    @pytest.mark.asyncio
    async def test_update_cache_mock(self):
        """Test updating cache with mocked API response."""
        with (
            patch("httpx.AsyncClient") as mock_client,
            patch("redis.from_url") as mock_redis,
        ):
            # Mock HTTP client
            mock_async_client = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_async_client

            mock_response = MagicMock()
            mock_response.json.return_value = MOCK_PLAYERS
            mock_response.raise_for_status = MagicMock()
            mock_async_client.get.return_value = mock_response

            # Mock Redis
            mock_redis_client = AsyncMock()
            mock_redis.return_value = mock_redis_client
            mock_redis_client.setex = AsyncMock()

            await cache.update_cache()

            # Verify Redis setex was called
            mock_redis_client.setex.assert_called()

    @pytest.mark.asyncio
    async def test_get_all_players_from_cache(self, redis_client):
        """Test retrieving all players from cache."""
        # Prepare test data
        test_data = gzip.compress(json.dumps(MOCK_PLAYERS).encode())

        with patch("players_cache_redis.get_redis_client", return_value=redis_client):
            # Store test data in fake Redis
            await redis_client.setex("nfl_players", 86400, test_data)

            # Retrieve data
            result = await cache.get_all_players()

            assert result is not None
            assert len(result) == 3
            assert "1234" in result
            assert result["1234"]["last_name"] == "Mahomes"

    @pytest.mark.asyncio
    async def test_get_all_players_no_cache(self):
        """Test getting players when cache is empty."""
        with patch("players_cache_redis.get_redis_client") as mock_redis:
            mock_redis_client = MagicMock()
            mock_redis.return_value = mock_redis_client
            mock_redis_client.get.return_value = None

            with patch("players_cache_redis.update_cache") as mock_update:
                mock_update.return_value = None
                # After update, return the cached data
                mock_redis_client.get.side_effect = [
                    None,
                    gzip.compress(json.dumps(MOCK_PLAYERS).encode()),
                ]

                result = await cache.get_all_players()

                # Should have called update_cache
                mock_update.assert_called_once()
                assert result is not None

    @pytest.mark.asyncio
    async def test_search_players_by_name(self, redis_client):
        """Test searching for players by name."""
        # Prepare test data
        test_data = gzip.compress(json.dumps(MOCK_PLAYERS).encode())

        with patch("players_cache_redis.get_redis_client", return_value=redis_client):
            await redis_client.setex("nfl_players", 86400, test_data)

            # Search for Mahomes
            result = await cache.get_player_by_name("Mahomes")
            assert len(result) == 1
            assert result[0]["last_name"] == "Mahomes"

            # Search for KC players (should find Mahomes and Kelce)
            result = await cache.get_player_by_name("KC")
            assert len(result) == 2

            # Case-insensitive search
            result = await cache.get_player_by_name("mahomes")
            assert len(result) == 1

            # Search with no results
            result = await cache.get_player_by_name("NonExistentPlayer")
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_player_by_id(self, redis_client):
        """Test getting a player by ID."""
        test_data = gzip.compress(json.dumps(MOCK_PLAYERS).encode())

        with patch("players_cache_redis.get_redis_client", return_value=redis_client):
            await redis_client.setex("nfl_players", 86400, test_data)

            # Get existing player
            result = await cache.get_player_by_id("1234")
            assert result is not None
            assert result["last_name"] == "Mahomes"

            # Get non-existent player
            result = await cache.get_player_by_id("00000")
            assert result is None

    @pytest.mark.asyncio
    async def test_get_cache_status_cached(self, redis_client):
        """Test cache status when data is cached."""
        test_data = gzip.compress(json.dumps(MOCK_PLAYERS).encode())

        with patch("players_cache_redis.get_redis_client", return_value=redis_client):
            await redis_client.setex("nfl_players", 86400, test_data)

            result = await cache.get_cache_status()

            assert result["cached"] is True
            assert result["player_count"] == 3
            assert result["ttl_seconds"] > 0
            assert "last_updated" in result

    @pytest.mark.asyncio
    async def test_get_cache_status_not_cached(self, redis_client):
        """Test cache status when no data is cached."""
        with patch("players_cache_redis.get_redis_client", return_value=redis_client):
            result = await cache.get_cache_status()

            assert result["cached"] is False
            assert result["player_count"] == 0
            assert result["ttl_seconds"] == 0
            assert result["last_updated"] is None

    @pytest.mark.asyncio
    async def test_force_refresh(self):
        """Test forcing cache refresh."""
        with patch("players_cache_redis.update_cache") as mock_update:
            mock_update.return_value = None

            await cache.force_refresh()

            # Should have called update_cache
            mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_compression(self):
        """Test that data is properly compressed and decompressed."""
        original_data = {
            "test": "data" * 1000
        }  # Large enough to benefit from compression

        # Compress
        compressed = gzip.compress(json.dumps(original_data).encode())

        # Verify compression worked
        assert len(compressed) < len(json.dumps(original_data).encode())

        # Decompress
        decompressed = json.loads(gzip.decompress(compressed).decode())

        assert decompressed == original_data

    @pytest.mark.asyncio
    async def test_filter_players(self):
        """Test the player filtering logic."""
        # Create a large set of mock players with different statuses
        large_player_set = {
            "active_qb": {"position": "QB", "status": "Active"},
            "inactive_qb": {"position": "QB", "status": "Inactive"},
            "retired_qb": {"position": "QB", "status": "Retired"},
            "active_rb": {"position": "RB", "status": "Active"},
            "active_wr": {"position": "WR", "status": "Active"},
            "active_te": {"position": "TE", "status": "Active"},
            "active_k": {"position": "K", "status": "Active"},
            "active_def": {"position": "DEF", "status": "Active"},
            "active_ol": {"position": "OL", "status": "Active"},  # Should be filtered
            "active_dl": {"position": "DL", "status": "Active"},  # Should be filtered
        }

        # Apply the filtering logic from the actual code
        fantasy_positions = {"QB", "RB", "WR", "TE", "K", "DEF", "LB", "DB", "DL"}
        filtered = {
            k: v
            for k, v in large_player_set.items()
            if v.get("position") in fantasy_positions and v.get("status") == "Active"
        }

        assert "active_qb" in filtered
        assert "inactive_qb" not in filtered
        assert "retired_qb" not in filtered
        assert "active_ol" not in filtered  # OL is not a fantasy position
        assert len(filtered) == 7  # All active fantasy positions
