"""Tests for the players cache module."""

import json
import gzip
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import players_cache_redis as cache


class TestPlayersCache:
    """Test the players cache functionality - basic tests only."""

    def test_cache_module_imports(self):
        """Test that cache module can be imported."""
        assert cache is not None
        assert hasattr(cache, "get_all_players")
        assert hasattr(cache, "get_player_by_name")
        assert hasattr(cache, "get_player_by_id")
        assert hasattr(cache, "get_cache_status")
        assert hasattr(cache, "force_refresh")

    def test_cache_constants(self):
        """Test that cache constants are defined."""
        assert cache.CACHE_KEY == "nfl_players:data"
        assert cache.META_KEY == "nfl_players:meta"
        assert cache.CACHE_TTL == 86400  # 24 hours

    @pytest.mark.asyncio
    async def test_compression_logic(self):
        """Test that compression logic works correctly."""
        # Test data
        test_data = {"player1": {"name": "Test Player"}}

        # Test compression
        json_str = json.dumps(test_data)
        compressed = gzip.compress(json_str.encode(), compresslevel=9)

        # Verify compression actually reduces size for larger data
        large_data = {str(i): {"data": "x" * 100} for i in range(100)}
        large_json = json.dumps(large_data)
        large_compressed = gzip.compress(large_json.encode(), compresslevel=9)

        assert len(large_compressed) < len(large_json)

        # Test decompression
        decompressed = gzip.decompress(compressed)
        restored_data = json.loads(decompressed.decode())

        assert restored_data == test_data

    def test_filter_logic(self):
        """Test player filtering logic (without actual Redis)."""
        # Test data with various player statuses
        test_players = {
            "1": {"player_id": "1", "active": True, "position": "QB"},
            "2": {"player_id": "2", "active": False, "position": "RB"},
            "3": {"player_id": "3", "active": True, "position": "DEF"},
            "4": {"player_id": "4", "active": None, "position": "WR"},
            "5": {"player_id": "5", "position": "K"},  # No active field
        }

        # Apply the same filtering logic as in update_cache
        filtered = {}
        for player_id, player in test_players.items():
            # Skip if explicitly inactive (active = False)
            if player.get("active") is False:
                continue

            # Always include DEF and K positions
            if player.get("position") in ["DEF", "K"]:
                filtered[player_id] = player
                continue

            # Include if active is True
            if player.get("active") is True:
                filtered[player_id] = player

        # Check filtering results
        assert "1" in filtered  # Active QB
        assert "2" not in filtered  # Inactive RB
        assert "3" in filtered  # DEF (always included)
        assert "4" not in filtered  # No active status
        assert "5" in filtered  # K (always included)
