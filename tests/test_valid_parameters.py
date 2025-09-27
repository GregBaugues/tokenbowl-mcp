"""Tests to ensure MCP tools still work with valid parameters after validation changes."""

import pytest
import sys
import os
from unittest.mock import AsyncMock, patch

# Import the module to test
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sleeper_mcp


class TestValidParameters:
    """Test that MCP tools work correctly with valid parameters."""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_get_roster_with_valid_id(self, mock_client):
        """Test get_roster works with valid roster_id."""
        # Mock the HTTP responses
        mock_response = AsyncMock()
        mock_response.json = lambda: [
            {
                "roster_id": 2,
                "owner_id": "123",
                "players": ["4046"],
                "settings": {"wins": 5, "losses": 3},
            }
        ]
        mock_response.raise_for_status = lambda: None

        mock_users_response = AsyncMock()
        mock_users_response.json = lambda: [
            {"user_id": "123", "display_name": "Test User"}
        ]
        mock_users_response.raise_for_status = lambda: None

        # Setup the mock client
        mock_instance = AsyncMock()
        mock_instance.get = AsyncMock()
        mock_instance.get.side_effect = [mock_response, mock_users_response]
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_client.return_value = mock_instance

        # Mock the cache function
        with patch("sleeper_mcp.get_players_from_cache") as mock_cache:
            mock_cache.return_value = {
                "4046": {"first_name": "Patrick", "last_name": "Mahomes"}
            }

            # Test with valid integer
            result = await sleeper_mcp.get_roster.fn(2)
            assert "error" not in result
            assert result["roster"]["roster_id"] == 2

            # Test with string that can be converted to valid integer
            result = await sleeper_mcp.get_roster.fn("2")
            assert "error" not in result
            assert result["roster"]["roster_id"] == 2

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_get_league_matchups_with_valid_week(self, mock_client):
        """Test get_league_matchups works with valid week."""
        # Mock the HTTP response
        mock_response = AsyncMock()
        mock_response.json = lambda: [
            {"matchup_id": 1, "roster_id": 1, "points": 100.5}
        ]
        mock_response.raise_for_status = lambda: None

        mock_instance = AsyncMock()
        mock_instance.get.return_value = mock_response
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_client.return_value = mock_instance

        # Mock spot refresh
        with patch("sleeper_mcp.spot_refresh_player_stats"):
            # Test with valid week
            result = await sleeper_mcp.get_league_matchups.fn(5)
            assert isinstance(result, list)
            assert len(result) > 0
            assert "error" not in result[0]

            # Test with string that converts to valid week
            result = await sleeper_mcp.get_league_matchups.fn("10")
            assert isinstance(result, list)
            assert "error" not in result[0] if result else True

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_get_league_transactions_with_valid_round(self, mock_client):
        """Test get_league_transactions works with valid round."""
        # Mock the HTTP response
        mock_response = AsyncMock()
        mock_response.json = lambda: [
            {"type": "waiver", "status": "complete", "adds": {"4046": 1}}
        ]
        mock_response.raise_for_status = lambda: None

        mock_instance = AsyncMock()
        mock_instance.get.return_value = mock_response
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_client.return_value = mock_instance

        # Test with valid round
        result = await sleeper_mcp.get_league_transactions.fn(1)
        assert isinstance(result, list)
        assert "error" not in result[0] if result else True

        # Test with string that converts to valid round
        result = await sleeper_mcp.get_league_transactions.fn("5")
        assert isinstance(result, list)
        assert "error" not in result[0] if result else True

    @pytest.mark.asyncio
    async def test_search_players_with_valid_name(self):
        """Test search_players_by_name works with valid name."""
        # Mock the search function
        with patch("sleeper_mcp.search_players_unified") as mock_search:
            with patch("sleeper_mcp.spot_refresh_player_stats"):
                mock_search.return_value = [
                    {
                        "player_id": "4046",
                        "first_name": "Patrick",
                        "last_name": "Mahomes",
                    }
                ]

                # Test with valid name
                result = await sleeper_mcp.search_players_by_name.fn("Mahomes")
                assert isinstance(result, list)
                if result:
                    assert "error" not in result[0]
                    assert result[0]["player_id"] == "4046"

                # Test with minimum valid length
                result = await sleeper_mcp.search_players_by_name.fn("Ma")
                assert isinstance(result, list)
                assert "error" not in result[0] if result else True

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_get_user_with_valid_username(self, mock_client):
        """Test get_user works with valid username."""
        # Mock the HTTP response
        mock_response = AsyncMock()
        mock_response.json = lambda: {
            "user_id": "123456",
            "username": "testuser",
            "display_name": "Test User",
        }
        mock_response.raise_for_status = lambda: None

        mock_instance = AsyncMock()
        mock_instance.get.return_value = mock_response
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_client.return_value = mock_instance

        # Test with valid username
        result = await sleeper_mcp.get_user.fn("testuser")
        assert "error" not in result
        assert result["username"] == "testuser"

        # Test with valid user_id
        result = await sleeper_mcp.get_user.fn("123456")
        assert "error" not in result

    @pytest.mark.asyncio
    async def test_get_trending_players_with_valid_type(self):
        """Test get_trending_players works with valid type."""
        with patch("httpx.AsyncClient") as mock_client:
            # Mock the HTTP response
            mock_response = AsyncMock()
            mock_response.json = lambda: [{"player_id": "4046", "count": 1000}]
            mock_response.raise_for_status = lambda: None

            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            with patch("sleeper_mcp.get_player_by_id") as mock_player:
                mock_player.return_value = {
                    "player_id": "4046",
                    "first_name": "Patrick",
                }

                # Test with valid 'add' type
                result = await sleeper_mcp.get_trending_players.fn(type="add")
                assert isinstance(result, list)
                assert "error" not in result[0] if result else True

                # Test with valid 'drop' type
                result = await sleeper_mcp.get_trending_players.fn(type="drop")
                assert isinstance(result, list)
                assert "error" not in result[0] if result else True

    @pytest.mark.asyncio
    async def test_evaluate_waiver_priority_with_valid_params(self):
        """Test evaluate_waiver_priority_cost works with valid parameters."""
        # Test with all valid parameters
        result = await sleeper_mcp.evaluate_waiver_priority_cost.fn(
            current_position=1, projected_points_gain=5.5, weeks_remaining=10
        )
        assert "error" not in result
        assert "recommended_action" in result
        assert result["recommended_action"] in ["claim", "wait"]

        # Test with string parameters that convert to valid values
        result = await sleeper_mcp.evaluate_waiver_priority_cost.fn(
            current_position="3", projected_points_gain="7.5", weeks_remaining="12"
        )
        assert "error" not in result
        assert "recommended_action" in result

    @pytest.mark.asyncio
    async def test_search_with_valid_query(self):
        """Test search works with valid query."""
        with patch("sleeper_mcp.search_players_unified") as mock_search:
            with patch("sleeper_mcp.get_trending_players.fn") as mock_trending:
                mock_search.return_value = [
                    {"player_id": "4046", "first_name": "Patrick"}
                ]
                mock_trending.return_value = []

                # Test with valid search query
                result = await sleeper_mcp.search.fn("Patrick Mahomes")
                assert "results" in result
                assert "error" not in result

                # Test with another valid query
                result = await sleeper_mcp.search.fn("waiver RB")
                assert "results" in result
                assert "error" not in result

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health_check tool works correctly."""
        with patch("sleeper_mcp.get_players_from_cache") as mock_cache:
            with patch("httpx.AsyncClient") as mock_client:
                # Mock cache response
                mock_cache.return_value = {"4046": {"player_id": "4046"}}

                # Mock HTTP response for Sleeper API
                mock_response = AsyncMock()
                mock_response.json = lambda: {"season": "2024", "week": 10}
                mock_response.raise_for_status = lambda: None

                mock_instance = AsyncMock()
                mock_instance.get.return_value = mock_response
                mock_instance.__aenter__.return_value = mock_instance
                mock_instance.__aexit__.return_value = None
                mock_client.return_value = mock_instance

                # Test health check
                result = await sleeper_mcp.health_check.fn()
                assert "status" in result
                assert result["status"] in ["healthy", "degraded", "unhealthy"]
                assert "components" in result
                assert "timestamp" in result
