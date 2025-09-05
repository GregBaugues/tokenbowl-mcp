"""Tests for Sleeper MCP tools."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import sys
import os

# Import the module to test
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sleeper_mcp

# Test data
MOCK_LEAGUE_DATA = {
    "league_id": "1266471057523490816",
    "name": "Token Bowl",
    "season": "2024",
    "sport": "nfl",
    "scoring_settings": {},
    "roster_positions": ["QB", "RB", "WR", "TE", "FLEX"],
    "total_rosters": 12,
}

MOCK_ROSTER_DATA = [
    {
        "roster_id": 1,
        "owner_id": "user_1",
        "players": ["1234", "5678"],
        "starters": ["1234"],
        "settings": {"wins": 5, "losses": 3},
    },
    {
        "roster_id": 2,
        "owner_id": "user_2",
        "players": ["9999", "8888"],
        "starters": ["9999"],
        "settings": {"wins": 7, "losses": 1},
    },
]

MOCK_USER_DATA = [
    {
        "user_id": "user_1",
        "username": "testuser1",
        "display_name": "Test User 1",
        "avatar": "avatar_1",
    },
    {
        "user_id": "user_2",
        "username": "testuser2",
        "display_name": "Test User 2",
        "avatar": "avatar_2",
    },
]

MOCK_PLAYER_DATA = {
    "1234": {
        "player_id": "1234",
        "first_name": "Patrick",
        "last_name": "Mahomes",
        "team": "KC",
        "position": "QB",
        "status": "Active",
    },
    "5678": {
        "player_id": "5678",
        "first_name": "Travis",
        "last_name": "Kelce",
        "team": "KC",
        "position": "TE",
        "status": "Active",
    },
}


class TestLeagueTools:
    """Test league-related MCP tools."""

    @pytest.mark.asyncio
    @pytest.mark.vcr()
    async def test_get_league_info(self):
        """Test getting league information."""
        result = await sleeper_mcp.get_league_info()

        assert "league_id" in result
        assert result["league_id"] == "1266471057523490816"
        assert "name" in result
        assert "season" in result
        assert "sport" in result

    @pytest.mark.asyncio
    @pytest.mark.vcr()
    async def test_get_league_rosters(self):
        """Test getting league rosters."""
        result = await sleeper_mcp.get_league_rosters()

        assert isinstance(result, list)
        if result:  # If we have data
            assert "roster_id" in result[0]
            assert "owner_id" in result[0]
            assert "players" in result[0]

    @pytest.mark.asyncio
    @pytest.mark.vcr()
    async def test_get_league_users(self):
        """Test getting league users."""
        result = await sleeper_mcp.get_league_users()

        assert isinstance(result, list)
        if result:  # If we have data
            assert "user_id" in result[0]
            assert "username" in result[0]

    @pytest.mark.asyncio
    @pytest.mark.vcr()
    async def test_get_league_matchups(self):
        """Test getting league matchups for a specific week."""
        result = await sleeper_mcp.get_league_matchups(week=1)

        assert isinstance(result, list)
        # Matchups might be empty depending on the week
        if result:
            assert "roster_id" in result[0]
            assert "matchup_id" in result[0]

    @pytest.mark.asyncio
    @pytest.mark.vcr()
    async def test_get_league_transactions(self):
        """Test getting league transactions."""
        result = await sleeper_mcp.get_league_transactions(round=1)

        assert isinstance(result, list)
        # Transactions might be empty
        if result:
            assert "transaction_id" in result[0]
            assert "type" in result[0]


class TestUserTools:
    """Test user-related MCP tools."""

    @pytest.mark.asyncio
    @pytest.mark.vcr()
    async def test_get_user(self):
        """Test getting user information by username."""
        # This will need a real username from the league
        result = await sleeper_mcp.get_user(username_or_id="testuser")

        # Result might be None if user doesn't exist
        if result:
            assert "user_id" in result
            assert "username" in result

    @pytest.mark.asyncio
    async def test_get_user_leagues_mock(self):
        """Test getting user leagues with mocked response."""
        mock_response = [{"league_id": "123", "name": "Test League", "season": "2024"}]

        with patch("httpx.AsyncClient") as mock_client:
            mock_async_client = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_async_client

            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status = MagicMock()
            mock_async_client.get.return_value = mock_response_obj

            result = await sleeper_mcp.get_user_leagues(
                user_id="test_user", sport="nfl", season="2024"
            )

            assert result == mock_response
            assert len(result) == 1
            assert result[0]["league_id"] == "123"


class TestPlayerTools:
    """Test player-related MCP tools."""

    @pytest.mark.asyncio
    async def test_search_player_by_name_mock(self):
        """Test searching for a player by name with mocked cache."""
        # Mock the imported function directly
        with patch("sleeper_mcp.get_player_by_name") as mock_get_player:
            mock_get_player.return_value = [
                {
                    "player_id": "1234",
                    "first_name": "Patrick",
                    "last_name": "Mahomes",
                    "team": "KC",
                    "position": "QB",
                }
            ]

            result = await sleeper_mcp.search_player_by_name(name="Mahomes")

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["last_name"] == "Mahomes"
            assert result[0]["position"] == "QB"

    @pytest.mark.asyncio
    async def test_get_player_by_sleeper_id_mock(self):
        """Test getting a player by Sleeper ID with mocked cache."""
        with patch("sleeper_mcp.get_player_by_id") as mock_get_player:
            mock_get_player.return_value = {
                "player_id": "1234",
                "first_name": "Patrick",
                "last_name": "Mahomes",
                "team": "KC",
                "position": "QB",
                "status": "Active",
            }

            result = await sleeper_mcp.get_player_by_sleeper_id(player_id="1234")

            assert result is not None
            assert result["player_id"] == "1234"
            assert result["last_name"] == "Mahomes"

    @pytest.mark.asyncio
    @pytest.mark.vcr()
    async def test_get_trending_players(self):
        """Test getting trending players."""
        result = await sleeper_mcp.get_trending_players(
            type="add", lookback_hours=24, limit=10
        )

        assert isinstance(result, list)
        # Result might be empty depending on current trends
        if result:
            assert "player_id" in result[0]
            assert "count" in result[0]


class TestDraftTools:
    """Test draft-related MCP tools."""

    @pytest.mark.asyncio
    async def test_get_draft_mock(self):
        """Test getting draft information with mocked response."""
        mock_draft = {
            "draft_id": "987654321",
            "league_id": "1266471057523490816",
            "status": "complete",
            "type": "snake",
            "settings": {"rounds": 15, "teams": 12},
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_async_client = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_async_client

            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_draft
            mock_response_obj.raise_for_status = MagicMock()
            mock_async_client.get.return_value = mock_response_obj

            result = await sleeper_mcp.get_draft(draft_id="987654321")

            assert result["draft_id"] == "987654321"
            assert result["league_id"] == "1266471057523490816"
            assert result["type"] == "snake"


class TestCacheOperations:
    """Test cache-related operations."""

    @pytest.mark.asyncio
    async def test_get_players_cache_status_mock(self):
        """Test getting cache status with mocked cache."""
        with patch("sleeper_mcp.get_cache_status") as mock_get_status:
            mock_get_status.return_value = {
                "cached": True,
                "player_count": 1000,
                "last_updated": "2024-01-01T00:00:00Z",
                "ttl_seconds": 86400,
            }

            result = await sleeper_mcp.get_players_cache_status()

            assert result["cached"] is True
            assert result["player_count"] == 1000
            assert "last_updated" in result

    @pytest.mark.asyncio
    async def test_refresh_players_cache_mock(self):
        """Test refreshing the players cache with mocked cache."""
        with (
            patch("sleeper_mcp.force_refresh") as mock_refresh,
            patch("sleeper_mcp.get_cache_status") as mock_status,
        ):
            mock_refresh.return_value = None
            mock_status.return_value = {
                "cached": True,
                "player_count": 1500,
                "last_updated": "2024-01-01T00:00:00Z",
                "ttl_seconds": 86400,
            }

            result = await sleeper_mcp.refresh_players_cache()

            assert "success" in result
            assert "message" in result


@pytest.mark.asyncio
async def test_mcp_server_initialization():
    """Test that the MCP server initializes correctly."""
    from fastmcp import FastMCP

    # Create a test MCP instance
    mcp = FastMCP("sleeper-test")

    # Check that the server is created
    assert mcp.name == "sleeper-test"

    # Check that we can list tools (though they won't be registered in test)
    assert hasattr(mcp, "tool")


@pytest.mark.asyncio
async def test_get_waiver_wire_players_mock():
    """Test getting waiver wire players with mocked data."""
    # Mock player data
    mock_players = {
        "1234": {
            "player_id": "1234",
            "full_name": "John Rostered",
            "position": "RB",
            "team": "SF",
            "status": "Active"
        },
        "5678": {
            "player_id": "5678",
            "full_name": "Jane Rostered",
            "position": "WR",
            "team": "NYG",
            "status": "Active"
        },
        "9999": {
            "player_id": "9999",
            "full_name": "Mike Available",
            "position": "QB",
            "team": "DAL",
            "status": "Active"
        },
        "8888": {
            "player_id": "8888",
            "full_name": "Sarah Free",
            "position": "WR",
            "team": "LAR",
            "status": "Active",
            "age": 25
        },
        "7777": {
            "player_id": "7777",
            "full_name": "Tom Waiver",
            "position": "TE",
            "team": "KC",
            "status": "Active"
        }
    }
    
    with (
        patch("sleeper_mcp.httpx.AsyncClient") as mock_client,
        patch("sleeper_mcp.get_all_players") as mock_get_players,
        patch("sleeper_mcp.get_cache_status") as mock_cache_status,
    ):
        # Setup mocks
        mock_response = AsyncMock()
        mock_response.json.return_value = MOCK_ROSTER_DATA
        mock_response.raise_for_status = MagicMock()
        
        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        mock_get_players.return_value = mock_players
        mock_cache_status.return_value = {
            "last_refresh_time": "2024-01-01T00:00:00Z",
            "is_stale": False
        }
        
        # Test without filters
        result = await sleeper_mcp.get_waiver_wire_players()
        
        assert result["total_available"] == 3  # Players 9999, 8888, 7777
        assert result["filtered_count"] == 3
        assert len(result["players"]) == 3
        
        # Verify non-rostered players are included
        player_ids = [p["player_id"] for p in result["players"]]
        assert "9999" in player_ids  # Mike Available
        assert "8888" in player_ids  # Sarah Free
        assert "7777" in player_ids  # Tom Waiver
        
        # Verify rostered players are excluded
        assert "1234" not in player_ids  # John Rostered
        assert "5678" not in player_ids  # Jane Rostered


@pytest.mark.asyncio
async def test_get_waiver_wire_players_with_position_filter():
    """Test waiver wire with position filtering."""
    mock_players = {
        "1234": {"player_id": "1234", "full_name": "Player A", "position": "QB", "status": "Active"},
        "5678": {"player_id": "5678", "full_name": "Player B", "position": "WR", "status": "Active"},
        "9999": {"player_id": "9999", "full_name": "Player C", "position": "WR", "status": "Active"},
    }
    
    with (
        patch("sleeper_mcp.httpx.AsyncClient") as mock_client,
        patch("sleeper_mcp.get_all_players") as mock_get_players,
        patch("sleeper_mcp.get_cache_status") as mock_cache_status,
    ):
        # Setup mocks - empty rosters so all players are available
        mock_response = AsyncMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()
        
        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        mock_get_players.return_value = mock_players
        mock_cache_status.return_value = {"last_refresh_time": "2024-01-01", "is_stale": False}
        
        # Test WR position filter
        result = await sleeper_mcp.get_waiver_wire_players(position="WR")
        
        assert result["filtered_count"] == 2
        positions = [p["position"] for p in result["players"]]
        assert all(pos == "WR" for pos in positions)


@pytest.mark.asyncio
async def test_get_waiver_wire_players_with_search_term():
    """Test waiver wire with name search."""
    mock_players = {
        "1234": {"player_id": "1234", "full_name": "Justin Jefferson", "position": "WR", "status": "Active"},
        "5678": {"player_id": "5678", "full_name": "Justin Herbert", "position": "QB", "status": "Active"},
        "9999": {"player_id": "9999", "full_name": "Mike Evans", "position": "WR", "status": "Active"},
    }
    
    with (
        patch("sleeper_mcp.httpx.AsyncClient") as mock_client,
        patch("sleeper_mcp.get_all_players") as mock_get_players,
        patch("sleeper_mcp.get_cache_status") as mock_cache_status,
    ):
        # Setup mocks
        mock_response = AsyncMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()
        
        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        mock_get_players.return_value = mock_players
        mock_cache_status.return_value = {"last_refresh_time": "2024-01-01", "is_stale": False}
        
        # Test search for "justin"
        result = await sleeper_mcp.get_waiver_wire_players(search_term="justin")
        
        assert result["filtered_count"] == 2
        names = [p["name"] for p in result["players"]]
        assert "Justin Jefferson" in names
        assert "Justin Herbert" in names
        assert "Mike Evans" not in names
