"""Test Sleeper MCP tools with mocked API responses."""

import pytest
from unittest.mock import patch, AsyncMock
import sleeper_mcp


class TestLeagueToolsMocked:
    """Test league-related MCP tools with mocked responses."""

    @pytest.mark.asyncio
    async def test_get_league_info(self):
        """Test getting league information with mocked response."""
        mock_response = {
            "league_id": "1266471057523490816",
            "name": "Token Bowl",
            "season": "2025",
            "sport": "nfl",
            "status": "in_season",
            "settings": {"max_keepers": 0, "playoff_teams": 6},
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance

            mock_resp = AsyncMock()
            mock_resp.json = lambda: mock_response
            mock_resp.raise_for_status = lambda: None
            mock_instance.get.return_value = mock_resp

            result = await sleeper_mcp.get_league_info.fn()

            assert "league_id" in result
            assert result["league_id"] == "1266471057523490816"
            assert "name" in result
            assert "season" in result
            assert "sport" in result

    @pytest.mark.asyncio
    async def test_get_league_rosters(self):
        """Test getting league rosters with mocked response (minimal by default)."""
        mock_response = [
            {
                "roster_id": 1,
                "owner_id": "123456",
                "players": ["4046", "4034"],
                "starters": ["4046"],
                "settings": {"wins": 5, "losses": 2},
            }
        ]

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance

            mock_resp = AsyncMock()
            mock_resp.json = lambda: mock_response
            mock_resp.raise_for_status = lambda: None
            mock_instance.get.return_value = mock_resp

            result = await sleeper_mcp.get_league_rosters.fn()

            assert isinstance(result, list)
            assert len(result) > 0
            assert "roster_id" in result[0]
            # Default is minimal mode - no players field
            assert "wins" in result[0]
            assert "losses" in result[0]

    @pytest.mark.asyncio
    async def test_get_league_rosters_with_details(self):
        """Test getting league rosters with full details."""
        mock_response = [
            {
                "roster_id": 1,
                "owner_id": "123456",
                "players": ["4046", "4034"],
                "starters": ["4046"],
                "settings": {"wins": 5, "losses": 2},
            }
        ]

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance

            mock_resp = AsyncMock()
            mock_resp.json = lambda: mock_response
            mock_resp.raise_for_status = lambda: None
            mock_instance.get.return_value = mock_resp

            result = await sleeper_mcp.get_league_rosters.fn(include_details=True)

            assert isinstance(result, list)
            assert len(result) > 0
            assert "roster_id" in result[0]
            assert "players" in result[0]

    @pytest.mark.asyncio
    async def test_get_league_users(self):
        """Test getting league users with mocked response."""
        mock_response = [
            {
                "user_id": "123456",
                "username": "testuser",
                "display_name": "Test User",
                "avatar": "abc123",
            }
        ]

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance

            mock_resp = AsyncMock()
            mock_resp.json = lambda: mock_response
            mock_resp.raise_for_status = lambda: None
            mock_instance.get.return_value = mock_resp

            result = await sleeper_mcp.get_league_users.fn()

            assert isinstance(result, list)
            assert len(result) > 0
            assert "user_id" in result[0]
            assert "username" in result[0]

    @pytest.mark.asyncio
    async def test_get_league_matchups(self):
        """Test getting league matchups with mocked response."""
        mock_response = [
            {
                "matchup_id": 1,
                "roster_id": 1,
                "points": 120.5,
                "starters_points": [25.5, 18.2],
            }
        ]

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance

            mock_resp = AsyncMock()
            mock_resp.json = lambda: mock_response
            mock_resp.raise_for_status = lambda: None
            mock_instance.get.return_value = mock_resp

            result = await sleeper_mcp.get_league_matchups.fn(week=1)

            assert isinstance(result, list)
            assert len(result) > 0
            assert "matchup_id" in result[0]
            assert "roster_id" in result[0]

    @pytest.mark.asyncio
    async def test_get_league_transactions(self):
        """Test getting league transactions with mocked response."""
        mock_response = [
            {
                "transaction_id": "987654321",
                "type": "waiver",
                "roster_ids": [1],
                "adds": {"4046": 1},
                "drops": {},
                "status": "complete",
            }
        ]

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance

            mock_resp = AsyncMock()
            mock_resp.json = lambda: mock_response
            mock_resp.raise_for_status = lambda: None
            mock_instance.get.return_value = mock_resp

            result = await sleeper_mcp.get_league_transactions.fn(round=1)

            assert isinstance(result, list)
            if result:  # Transactions might be empty
                assert "type" in result[0]
                assert "status" in result[0]

    @pytest.mark.asyncio
    async def test_get_recent_transactions(self):
        """Test getting recent transactions across multiple rounds with mocked response."""
        # Mock responses for different rounds
        mock_round1 = [
            {
                "transaction_id": "1",
                "type": "free_agent",
                "status": "complete",
                "status_updated": 1757000000,  # Older
                "adds": {"123": 1},
                "drops": {"456": 1},
            }
        ]

        mock_round2 = [
            {
                "transaction_id": "2",
                "type": "waiver",
                "status": "complete",
                "status_updated": 1757200000,  # Newer
                "adds": {"789": 2},
                "drops": {"012": 2},
            },
            {
                "transaction_id": "3",
                "type": "trade",
                "status": "failed",
                "status_updated": 1757100000,  # Middle
                "adds": {"345": 3},
                "drops": {"678": 3},
            },
        ]

        # Mock the cache function
        with patch("cache_client.get_player_by_id") as mock_cache:
            # Return minimal player data for enrichment
            def get_player_mock(player_id):
                return {
                    "full_name": f"Player {player_id}",
                    "position": "RB",
                    "team": "SF",
                }

            mock_cache.side_effect = get_player_mock

            # Helper to create fresh mock responses for each test
            def create_mock_responses():
                def create_mock_response(data):
                    mock_resp = AsyncMock()
                    mock_resp.status_code = 200
                    mock_resp.json = lambda: data
                    return mock_resp

                return [
                    create_mock_response(mock_round1),  # Round 1
                    create_mock_response(mock_round2),  # Round 2
                    create_mock_response([]),  # Round 3
                    create_mock_response([]),  # Round 4
                    create_mock_response([]),  # Round 5
                    create_mock_response([]),  # Round 6
                    create_mock_response([]),  # Round 7
                    create_mock_response([]),  # Round 8
                    create_mock_response([]),  # Round 9
                    create_mock_response([]),  # Round 10
                ]

            # Test default behavior
            with patch("httpx.AsyncClient") as mock_client:
                mock_instance = AsyncMock()
                mock_client.return_value.__aenter__.return_value = mock_instance
                mock_instance.get = AsyncMock(side_effect=create_mock_responses())

                result = await sleeper_mcp.get_recent_transactions.fn()

                assert isinstance(result, list)
                assert len(result) == 2  # Should exclude failed by default
                assert result[0]["transaction_id"] == "2"  # Newest first
                assert result[1]["transaction_id"] == "1"

            # Test with include_failed=True
            with patch("httpx.AsyncClient") as mock_client:
                mock_instance = AsyncMock()
                mock_client.return_value.__aenter__.return_value = mock_instance
                mock_instance.get = AsyncMock(side_effect=create_mock_responses())

                result = await sleeper_mcp.get_recent_transactions.fn(
                    include_failed=True
                )
                assert len(result) == 3

            # Test with transaction_type filter
            with patch("httpx.AsyncClient") as mock_client:
                mock_instance = AsyncMock()
                mock_client.return_value.__aenter__.return_value = mock_instance
                mock_instance.get = AsyncMock(side_effect=create_mock_responses())

                result = await sleeper_mcp.get_recent_transactions.fn(
                    transaction_type="waiver"
                )
                assert len(result) == 1
                assert result[0]["type"] == "waiver"

            # Test with limit
            with patch("httpx.AsyncClient") as mock_client:
                mock_instance = AsyncMock()
                mock_client.return_value.__aenter__.return_value = mock_instance
                mock_instance.get = AsyncMock(side_effect=create_mock_responses())

                result = await sleeper_mcp.get_recent_transactions.fn(limit=1)
                assert len(result) == 1


class TestUserToolsMocked:
    """Test user-related MCP tools with mocked responses."""

    @pytest.mark.asyncio
    async def test_get_user(self):
        """Test getting user information with mocked response."""
        mock_response = {
            "user_id": "123456",
            "username": "testuser",
            "display_name": "Test User",
            "avatar": "abc123",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance

            mock_resp = AsyncMock()
            mock_resp.json = lambda: mock_response
            mock_resp.raise_for_status = lambda: None
            mock_instance.get.return_value = mock_resp

            result = await sleeper_mcp.get_user.fn(username_or_id="testuser")

            assert "user_id" in result
            assert "username" in result
            assert result["username"] == "testuser"


class TestPlayerToolsMocked:
    """Test player-related MCP tools with mocked responses."""

    @pytest.mark.asyncio
    async def test_get_trending_players(self):
        """Test getting trending players with mocked response."""
        mock_response = [
            {"player_id": "4046", "count": 150},
            {"player_id": "4034", "count": 120},
        ]

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance

            mock_resp = AsyncMock()
            mock_resp.json = lambda: mock_response
            mock_resp.raise_for_status = lambda: None
            mock_instance.get.return_value = mock_resp

            # Mock the cache function
            with patch("sleeper_mcp.get_players_from_cache") as mock_cache:
                mock_cache.return_value = {
                    "4046": {
                        "player_id": "4046",
                        "full_name": "Patrick Mahomes",
                        "position": "QB",
                    },
                    "4034": {
                        "player_id": "4034",
                        "full_name": "Davante Adams",
                        "position": "WR",
                    },
                }

                result = await sleeper_mcp.get_trending_players.fn(type="add")

                assert isinstance(result, list)
                if result:
                    assert "player_id" in result[0]
                    assert "count" in result[0]
