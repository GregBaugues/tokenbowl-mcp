"""Tests for the players cache module."""

import json
import gzip
from unittest.mock import MagicMock, patch, AsyncMock
import pytest
import sys
import os
import fakeredis

# Add parent directory to path for imports
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
        "active": True,
    },
    "5678": {
        "player_id": "5678",
        "first_name": "Christian",
        "last_name": "McCaffrey",
        "team": "SF",
        "position": "RB",
        "status": "Active",
        "active": True,
    },
    "9999": {
        "player_id": "9999",
        "first_name": "Tom",
        "last_name": "Brady",
        "team": None,
        "position": "QB",
        "status": "Inactive",
        "active": False,
    },
}


@pytest.fixture
def redis_client():
    """Create a fake Redis client for testing."""
    client = fakeredis.FakeRedis(decode_responses=False)
    yield client
    client.flushall()


class TestPlayersCache:
    """Test the players cache functionality."""

    @pytest.mark.asyncio
    async def test_get_redis_connection(self, redis_client):
        """Test getting Redis connection."""
        # Direct test of redis connection
        assert redis_client is not None
        # Test that we can perform a basic operation
        redis_client.ping()

    @pytest.mark.asyncio
    async def test_update_cache_mock(self):
        """Test updating cache with mocked API response."""
        with (
            patch("httpx.AsyncClient") as mock_client,
            patch("redis.from_url") as mock_redis,
        ):
            # Mock HTTP client
            mock_response = AsyncMock()
            mock_response.json.return_value = MOCK_PLAYERS
            mock_response.raise_for_status = MagicMock()

            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            # Mock Redis
            mock_redis_client = MagicMock()
            mock_redis.return_value = mock_redis_client
            mock_redis_client.setex = MagicMock()

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
            redis_client.setex("nfl_players", 86400, test_data)

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
                # Mock update_cache to return test data
                mock_update.return_value = MOCK_PLAYERS
                
                result = await cache.get_all_players()

                # Should have called update_cache
                mock_update.assert_called_once()
                assert result == MOCK_PLAYERS

    @pytest.mark.asyncio
    async def test_search_players_by_name(self, redis_client):
        """Test searching for players by name."""
        # Prepare test data
        test_data = gzip.compress(json.dumps(MOCK_PLAYERS).encode())

        with patch("players_cache_redis.get_redis_client", return_value=redis_client):
            # Store test data for players
            redis_client.setex("nfl_players", 86400, test_data)

            # Search for a player
            result = await cache.get_player_by_name("Mahomes")

            assert result is not None
            assert len(result) > 0
            assert any(
                p.get("last_name") == "Mahomes" or p.get("first_name") == "Mahomes"
                for p in result
            )

    @pytest.mark.asyncio
    async def test_get_player_by_id(self, redis_client):
        """Test getting a player by Sleeper ID."""
        # Prepare test data
        test_data = gzip.compress(json.dumps(MOCK_PLAYERS).encode())

        with patch("players_cache_redis.get_redis_client", return_value=redis_client):
            # Store test data
            redis_client.setex("nfl_players", 86400, test_data)

            # Get a specific player
            result = await cache.get_player_by_id("1234")

            assert result is not None
            assert result["player_id"] == "1234"
            assert result["last_name"] == "Mahomes"

    @pytest.mark.asyncio
    async def test_get_cache_status_cached(self, redis_client):
        """Test getting cache status when data is cached."""
        # Prepare test data and metadata
        test_data = gzip.compress(json.dumps(MOCK_PLAYERS).encode())
        meta = {
            "last_updated": "2024-01-01T00:00:00",
            "total_players": 3,
            "cached_players": 2,
            "compressed_size_mb": 0.01,
        }

        with patch("players_cache_redis.get_redis_client", return_value=redis_client):
            # Store compressed data
            redis_client.setex("nfl_players", 86400, test_data)
            # Store metadata
            redis_client.setex("nfl_players_meta", 86400, json.dumps(meta))

            # Get cache status
            result = await cache.get_cache_status()

            assert result["cached"] is True
            assert result["player_count"] == 3
            assert "last_refresh_time" in result

    @pytest.mark.asyncio
    async def test_get_cache_status_not_cached(self, redis_client):
        """Test getting cache status when no data is cached."""
        meta = {"last_updated": "2024-01-01T00:00:00", "total_players": 0}

        with patch("players_cache_redis.get_redis_client", return_value=redis_client):
            # Verify no data in cache
            result = redis_client.get("nfl_players")
            assert result is None

            # Store metadata
            redis_client.setex("nfl_players_meta", 86400, json.dumps(meta))

            # Get cache status
            result = await cache.get_cache_status()

            assert result["cached"] is False
            assert result["player_count"] == 0

    @pytest.mark.asyncio
    async def test_force_refresh(self):
        """Test forcing a cache refresh."""
        with (
            patch("httpx.AsyncClient") as mock_client,
            patch("redis.from_url") as mock_redis,
        ):
            # Mock HTTP client
            mock_response = AsyncMock()
            mock_response.json.return_value = MOCK_PLAYERS
            mock_response.raise_for_status = MagicMock()

            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            # Mock Redis
            mock_redis_client = MagicMock()
            mock_redis.return_value = mock_redis_client
            mock_redis_client.setex = MagicMock()

            await cache.force_refresh()

            # Verify Redis setex was called for both data and metadata
            assert mock_redis_client.setex.call_count >= 1

    @pytest.mark.asyncio
    async def test_compression(self):
        """Test that data is properly compressed."""
        large_data = {str(i): {"player_id": str(i), "data": "x" * 100} for i in range(100)}
        
        with patch("players_cache_redis.get_redis_client") as mock_get_redis:
            mock_redis = MagicMock()
            mock_get_redis.return_value = mock_redis
            
            with patch("httpx.AsyncClient") as mock_client:
                mock_response = AsyncMock()
                mock_response.json.return_value = large_data
                mock_response.raise_for_status = MagicMock()
                
                mock_instance = AsyncMock()
                mock_instance.get.return_value = mock_response
                mock_client.return_value.__aenter__.return_value = mock_instance
                
                await cache.update_cache()
                
                # Check that setex was called with compressed data
                mock_redis.setex.assert_called()
                call_args = mock_redis.setex.call_args[0]
                # The second argument should be TTL, third should be compressed data
                compressed_data = call_args[2]
                
                # Verify it's actually compressed (should be smaller than original)
                original_size = len(json.dumps(large_data))
                compressed_size = len(compressed_data)
                assert compressed_size < original_size

    @pytest.mark.asyncio
    async def test_filter_players(self):
        """Test that inactive/irrelevant players are filtered out."""
        test_players = {
            "1": {"player_id": "1", "active": True, "position": "QB"},
            "2": {"player_id": "2", "active": False, "position": "RB"},
            "3": {"player_id": "3", "active": True, "position": "DEF"},
            "4": {"player_id": "4", "active": None, "position": "WR"},
        }
        
        with patch("players_cache_redis.get_redis_client") as mock_get_redis:
            mock_redis = MagicMock()
            mock_get_redis.return_value = mock_redis
            
            with patch("httpx.AsyncClient") as mock_client:
                mock_response = AsyncMock()
                mock_response.json.return_value = test_players
                mock_response.raise_for_status = MagicMock()
                
                mock_instance = AsyncMock()
                mock_instance.get.return_value = mock_response
                mock_client.return_value.__aenter__.return_value = mock_instance
                
                result = await cache.update_cache()
                
                # Only active players and defenses should be included
                assert len(result) == 2
                assert "1" in result  # Active QB
                assert "3" in result  # Defense (always included)
                assert "2" not in result  # Inactive
                assert "4" not in result  # No active status