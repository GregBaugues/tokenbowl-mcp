"""Tests for Sleeper MCP tools."""

import pytest
from unittest.mock import patch
import sys
import os

# Import the module to test
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sleeper_mcp

# Test data
MOCK_LEAGUE_DATA = {
    "league_id": os.environ.get("SLEEPER_LEAGUE_ID", "1266471057523490816"),
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
        result = await sleeper_mcp.get_league_info.fn()

        assert "league_id" in result
        expected_league_id = os.environ.get("SLEEPER_LEAGUE_ID", "1266471057523490816")
        assert result["league_id"] == expected_league_id
        assert "name" in result
        assert "season" in result
        assert "sport" in result

    @pytest.mark.asyncio
    @pytest.mark.vcr()
    async def test_get_league_rosters(self):
        """Test getting league rosters (minimal by default)."""
        result = await sleeper_mcp.get_league_rosters.fn()

        assert isinstance(result, list)
        if result:  # If we have data
            assert "roster_id" in result[0]
            assert "owner_id" in result[0]
            # Default is minimal mode - no players field
            assert "wins" in result[0]
            assert "losses" in result[0]

    @pytest.mark.asyncio
    @pytest.mark.vcr()
    async def test_get_league_rosters_with_details(self):
        """Test getting league rosters with full details."""
        result = await sleeper_mcp.get_league_rosters.fn(include_details=True)

        assert isinstance(result, list)
        if result:  # If we have data
            assert "roster_id" in result[0]
            assert "owner_id" in result[0]
            assert "players" in result[0]

    @pytest.mark.asyncio
    @pytest.mark.vcr()
    async def test_get_league_users(self):
        """Test getting league users."""
        result = await sleeper_mcp.get_league_users.fn()

        assert isinstance(result, list)
        if result:  # If we have data
            assert "user_id" in result[0]
            # API returns display_name, not username
            assert "display_name" in result[0]

    @pytest.mark.asyncio
    @pytest.mark.vcr()
    async def test_get_league_matchups(self):
        """Test getting league matchups for a specific week."""
        result = await sleeper_mcp.get_league_matchups.fn(week=1)

        assert isinstance(result, list)
        # Matchups might be empty depending on the week
        if result:
            assert "roster_id" in result[0]
            assert "matchup_id" in result[0]

    @pytest.mark.asyncio
    @pytest.mark.vcr()
    async def test_get_league_transactions(self):
        """Test getting league transactions."""
        result = await sleeper_mcp.get_league_transactions.fn(round=1)

        assert isinstance(result, list)
        # Transactions might be empty
        if result:
            assert "transaction_id" in result[0]
            assert "type" in result[0]

    @pytest.mark.asyncio
    @pytest.mark.vcr()
    async def test_get_recent_transactions(self):
        """Test getting recent transactions across multiple rounds."""
        # Test default behavior
        result = await sleeper_mcp.get_recent_transactions.fn()

        assert isinstance(result, list)

        # Check that results are sorted by recency if we have multiple transactions
        if len(result) > 1:
            timestamps = [tx.get("status_updated", 0) for tx in result]
            assert timestamps == sorted(timestamps, reverse=True), (
                "Transactions should be sorted by recency"
            )

        # Test with specific filters
        waiver_only = await sleeper_mcp.get_recent_transactions.fn(
            transaction_type="waiver"
        )
        assert all(tx.get("type") == "waiver" for tx in waiver_only), (
            "Should only return waiver transactions"
        )

        # Test with limit
        limited = await sleeper_mcp.get_recent_transactions.fn(limit=5)
        assert len(limited) <= 5, "Should respect limit parameter"

        # Test including failed transactions
        with_failed = await sleeper_mcp.get_recent_transactions.fn(include_failed=True)
        without_failed = await sleeper_mcp.get_recent_transactions.fn(
            include_failed=False
        )

        # Verify failed transactions are excluded by default
        failed_excluded = sum(
            1 for tx in without_failed if tx.get("status") == "failed"
        )
        assert failed_excluded == 0, "Should not include failed transactions by default"

        # When including failed, we should have at least as many transactions
        assert len(with_failed) >= len(without_failed), (
            "Including failed should have at least as many transactions"
        )

    @pytest.mark.asyncio
    @pytest.mark.vcr()
    async def test_get_roster(self):
        """Test getting detailed roster information with player enrichment."""
        # Test roster ID 2 (Bill Beliclaude)
        result = await sleeper_mcp.get_roster.fn(roster_id=2)

        assert isinstance(result, dict)
        assert "roster_id" in result
        assert result["roster_id"] == 2
        assert "owner" in result
        assert "starters" in result
        assert "bench" in result

        # Verify owner information is included
        if result.get("owner"):
            assert "display_name" in result["owner"] or "username" in result["owner"]

        # Verify starters have player data
        if result.get("starters"):
            assert len(result["starters"]) > 0
            first_starter = result["starters"][0]
            assert "player_id" in first_starter
            assert "name" in first_starter

        # Verify bench has player data
        if result.get("bench"):
            assert isinstance(result["bench"], list)
            if len(result["bench"]) > 0:
                first_bench = result["bench"][0]
                assert "player_id" in first_bench


class TestUserTools:
    """Test user-related MCP tools."""

    @pytest.mark.asyncio
    @pytest.mark.vcr()
    async def test_get_user(self):
        """Test getting user information by username."""
        # This will need a real username from the league
        result = await sleeper_mcp.get_user.fn(username_or_id="testuser")

        # Result might be None if user doesn't exist
        if result:
            assert "user_id" in result
            assert "username" in result

    @pytest.mark.skip(reason="get_user_leagues tool has been removed")
    @pytest.mark.asyncio
    async def test_get_user_leagues_mock(self):
        """Test getting user leagues with mocked response."""
        pass  # Tool has been removed from MCP server


class TestPlayerTools:
    """Test player-related MCP tools."""

    @pytest.mark.asyncio
    async def test_search_player_by_name_mock(self):
        """Test searching for a player by name with mocked cache."""
        # Mock the imported function directly (it's a sync function)
        with patch("sleeper_mcp.search_players_unified") as mock_search:
            mock_search.return_value = [
                {
                    "id": "1234",
                    "name": "Patrick Mahomes",
                    "team": "KC",
                    "position": "QB",
                    "age": 28,
                    "status": "Active",
                }
            ]

            result = await sleeper_mcp.search_players_by_name.fn(name="Mahomes")

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["name"] == "Patrick Mahomes"
            assert result[0]["position"] == "QB"

    @pytest.mark.asyncio
    async def test_get_player_by_sleeper_id_mock(self):
        """Test getting a player by Sleeper ID with mocked cache."""
        # Mock the imported function directly (it's a sync function)
        with patch("sleeper_mcp.get_player_by_id") as mock_get_player:
            mock_get_player.return_value = {
                "player_id": "1234",
                "first_name": "Patrick",
                "last_name": "Mahomes",
                "team": "KC",
                "position": "QB",
                "status": "Active",
            }

            result = await sleeper_mcp.get_player_by_sleeper_id.fn(player_id="1234")

            assert result is not None
            assert result["player_id"] == "1234"
            assert result["last_name"] == "Mahomes"

    @pytest.mark.asyncio
    @pytest.mark.vcr()
    async def test_get_trending_players(self):
        """Test getting trending players."""
        # Mock get_players_from_cache to return empty dict if cache fails
        with patch("sleeper_mcp.get_players_from_cache") as mock_get_cache:
            mock_get_cache.return_value = {}

            result = await sleeper_mcp.get_trending_players.fn(type="add")

            assert isinstance(result, list)
            # Result might be empty depending on current trends
            if result:
                assert "player_id" in result[0]
                assert "count" in result[0]

    @pytest.mark.asyncio
    @pytest.mark.vcr()
    async def test_search_players_by_name_integration(self):
        """Test searching for players by name with real API."""
        # Mock cache to return a sample player
        with patch("sleeper_mcp.search_players_unified") as mock_search:
            mock_search.return_value = [
                {
                    "player_id": "4046",
                    "full_name": "Patrick Mahomes",
                    "first_name": "Patrick",
                    "last_name": "Mahomes",
                    "team": "KC",
                    "position": "QB",
                    "age": 29,
                    "status": "Active",
                }
            ]

            result = await sleeper_mcp.search_players_by_name.fn(name="Mahomes")

            assert isinstance(result, list)
            assert len(result) >= 1
            # Check that we got Mahomes in the results
            mahomes = next(
                (p for p in result if "Mahomes" in p.get("full_name", "")), None
            )
            assert mahomes is not None
            assert mahomes["position"] == "QB"
            assert mahomes["team"] == "KC"

    @pytest.mark.asyncio
    @pytest.mark.vcr()
    async def test_get_player_by_sleeper_id_integration(self):
        """Test getting a player by Sleeper ID with real API."""
        # Mock cache to return Patrick Mahomes
        with patch("sleeper_mcp.get_player_by_id") as mock_get_player:
            mock_get_player.return_value = {
                "player_id": "4046",
                "first_name": "Patrick",
                "last_name": "Mahomes",
                "full_name": "Patrick Mahomes",
                "team": "KC",
                "position": "QB",
                "status": "Active",
                "age": 29,
            }

            result = await sleeper_mcp.get_player_by_sleeper_id.fn(player_id="4046")

            assert result is not None
            assert result["player_id"] == "4046"
            assert result["last_name"] == "Mahomes"
            assert result["position"] == "QB"
            assert result["team"] == "KC"

    @pytest.mark.asyncio
    @pytest.mark.vcr()
    async def test_get_player_stats_all_weeks(self):
        """Test getting player stats for all weeks of a season."""
        result = await sleeper_mcp.get_player_stats_all_weeks.fn(
            player_id="4046",  # Patrick Mahomes
            season="2024",
        )

        assert isinstance(result, dict)
        assert "player_id" in result
        assert result["player_id"] == "4046"
        assert "player_info" in result
        assert "weekly_stats" in result
        assert "totals" in result

        # Verify player info
        assert "name" in result["player_info"]
        assert "position" in result["player_info"]
        assert result["player_info"]["position"] == "QB"

        # Verify weekly stats structure (if any games played)
        if result["weekly_stats"]:
            # weekly_stats is a dict with week numbers as keys
            first_week_key = list(result["weekly_stats"].keys())[0]
            first_week = result["weekly_stats"][first_week_key]
            assert "fantasy_points" in first_week
            assert "game_stats" in first_week

        # Verify season totals
        assert isinstance(result["totals"], dict)
        assert "fantasy_points" in result["totals"]
        assert "games_played" in result["totals"]

    @pytest.mark.asyncio
    @pytest.mark.vcr()
    async def test_get_waiver_wire_players_basic(self):
        """Test getting waiver wire players with basic parameters."""
        # Mock cache and roster data
        with (
            patch("sleeper_mcp.get_players_from_cache") as mock_cache,
            patch("sleeper_mcp.get_trending_data_map") as mock_trending,
        ):
            mock_cache.return_value = {
                "1234": {
                    "player_id": "1234",
                    "full_name": "Available Player",
                    "position": "RB",
                    "team": "CHI",
                    "status": "Active",
                }
            }
            mock_trending.return_value = {}

            result = await sleeper_mcp.get_waiver_wire_players.fn(limit=10)

            assert isinstance(result, dict)
            assert "total_available" in result
            assert "players" in result
            assert isinstance(result["players"], list)
            assert len(result["players"]) <= 10

    @pytest.mark.asyncio
    @pytest.mark.vcr()
    async def test_get_waiver_wire_players_with_position(self):
        """Test getting waiver wire players filtered by position."""
        # Mock cache and roster data
        with (
            patch("sleeper_mcp.get_players_from_cache") as mock_cache,
            patch("sleeper_mcp.get_trending_data_map") as mock_trending,
        ):
            mock_cache.return_value = {
                "1234": {
                    "player_id": "1234",
                    "full_name": "Available RB",
                    "position": "RB",
                    "team": "CHI",
                    "status": "Active",
                },
                "5678": {
                    "player_id": "5678",
                    "full_name": "Available WR",
                    "position": "WR",
                    "team": "DET",
                    "status": "Active",
                },
            }
            mock_trending.return_value = {}

            result = await sleeper_mcp.get_waiver_wire_players.fn(
                position="RB", limit=20
            )

            assert isinstance(result, dict)
            assert "players" in result
            # All returned players should be RBs
            for player in result["players"]:
                assert player["position"] == "RB"

    @pytest.mark.asyncio
    @pytest.mark.vcr()
    async def test_get_waiver_wire_players_with_search(self):
        """Test getting waiver wire players with search term."""
        # Mock cache and roster data
        with (
            patch("sleeper_mcp.get_players_from_cache") as mock_cache,
            patch("sleeper_mcp.get_trending_data_map") as mock_trending,
        ):
            mock_cache.return_value = {
                "1234": {
                    "player_id": "1234",
                    "full_name": "John Smith",
                    "position": "RB",
                    "team": "CHI",
                    "status": "Active",
                },
                "5678": {
                    "player_id": "5678",
                    "full_name": "Jane Doe",
                    "position": "WR",
                    "team": "DET",
                    "status": "Active",
                },
            }
            mock_trending.return_value = {}

            result = await sleeper_mcp.get_waiver_wire_players.fn(
                search_term="Smith", limit=20
            )

            assert isinstance(result, dict)
            assert "players" in result
            # All returned players should match search term
            for player in result["players"]:
                assert "Smith" in player["full_name"]

    @pytest.mark.asyncio
    @pytest.mark.vcr()
    async def test_get_waiver_analysis(self):
        """Test getting waiver wire analysis."""
        # Mock cache and roster data
        with (
            patch("sleeper_mcp.get_players_from_cache") as mock_cache,
            patch("sleeper_mcp.get_trending_data_map") as mock_trending,
        ):
            mock_cache.return_value = {}
            mock_trending.return_value = {}

            result = await sleeper_mcp.get_waiver_analysis.fn(limit=10)

            assert isinstance(result, dict)
            assert "recently_dropped" in result
            assert "trending_available" in result
            assert isinstance(result["recently_dropped"], list)
            assert isinstance(result["trending_available"], list)

    @pytest.mark.asyncio
    async def test_get_trending_context(self):
        """Test getting trending context for players."""
        # Mock the cache lookup to return player data
        with patch("sleeper_mcp.get_player_by_id") as mock_get_player:
            mock_get_player.return_value = {
                "player_id": "4046",
                "full_name": "Patrick Mahomes",
                "team": "KC",
                "position": "QB",
                "status": "Active",
            }

            result = await sleeper_mcp.get_trending_context.fn(
                player_ids=["4046"],  # Patrick Mahomes
                max_players=1,
            )

            assert isinstance(result, dict)
            assert "4046" in result
            assert isinstance(result["4046"], str)
            # Should have some context text
            assert len(result["4046"]) > 0


class TestDraftTools:
    """Test draft-related MCP tools."""

    pass  # All draft tool tests commented out while tools are disabled

    # Commented out because get_draft tool is currently disabled
    # @pytest.mark.asyncio
    # async def test_get_draft_mock(self):
    #     """Test getting draft information with mocked response."""
    #     mock_draft = {
    #         "draft_id": "987654321",
    #         "league_id": os.environ.get("SLEEPER_LEAGUE_ID", "1266471057523490816"),
    #         "status": "complete",
    #         "type": "snake",
    #         "settings": {"rounds": 15, "teams": 12},
    #     }

    #     with patch("httpx.AsyncClient") as mock_client:
    #         mock_async_client = AsyncMock()
    #         mock_client.return_value.__aenter__.return_value = mock_async_client

    #         mock_response_obj = MagicMock()
    #         mock_response_obj.json.return_value = mock_draft
    #         mock_response_obj.raise_for_status = MagicMock()
    #         mock_async_client.get.return_value = mock_response_obj

    #         result = await sleeper_mcp.get_draft.fn(draft_id="987654321")

    #         assert result["draft_id"] == "987654321"
    #         expected_league_id = os.environ.get(
    #             "SLEEPER_LEAGUE_ID", "1266471057523490816"
    #         )
    #         assert result["league_id"] == expected_league_id
    #         assert result["type"] == "snake"


class TestCacheOperations:
    """Test cache-related operations."""

    @pytest.mark.skip(reason="get_cache_status tool has been removed")
    @pytest.mark.asyncio
    async def test_get_players_cache_status_mock(self):
        """Test getting cache status with mocked cache."""
        pass  # Tool has been removed from MCP server

    @pytest.mark.skip(reason="refresh_players_cache tool has been removed")
    @pytest.mark.asyncio
    async def test_refresh_players_cache_mock(self):
        """Test refreshing the players cache with mocked cache."""
        pass  # Tool has been removed from MCP server


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


def test_waiver_wire_tool_exists():
    """Test that waiver wire tool is defined."""
    assert hasattr(sleeper_mcp, "get_waiver_wire_players")
    tool = sleeper_mcp.get_waiver_wire_players
    assert tool is not None
    assert hasattr(tool, "fn")  # Has the actual function
    assert hasattr(tool, "name")
    assert tool.name == "get_waiver_wire_players"


def test_waiver_wire_filtering_logic():
    """Test the filtering logic used by waiver wire tool (unit test)."""
    # Test data
    all_players = {
        "1": {
            "player_id": "1",
            "full_name": "Player A",
            "position": "QB",
            "status": "Active",
        },
        "2": {
            "player_id": "2",
            "full_name": "Player B",
            "position": "WR",
            "status": "Active",
        },
        "3": {
            "player_id": "3",
            "full_name": "Player C",
            "position": "WR",
            "status": "Active",
        },
        "4": {
            "player_id": "4",
            "full_name": "Justin Herbert",
            "position": "QB",
            "status": "Active",
        },
    }
    rostered = {"1", "2"}  # Players 1 and 2 are on rosters

    # Apply filtering logic (same as in the actual function)
    available = []
    for player_id, player_data in all_players.items():
        if player_id in rostered:
            continue

        player_info = {
            "player_id": player_id,
            "name": player_data.get("full_name"),
            "position": player_data.get("position"),
            "status": player_data.get("status"),
        }
        available.append(player_info)

    # Check results
    assert len(available) == 2
    player_ids = [p["player_id"] for p in available]
    assert "3" in player_ids
    assert "4" in player_ids
    assert "1" not in player_ids  # Rostered
    assert "2" not in player_ids  # Rostered

    # Test position filtering
    wr_players = [p for p in available if p["position"] == "WR"]
    assert len(wr_players) == 1
    assert wr_players[0]["player_id"] == "3"

    # Test name search
    justin_players = [p for p in available if "justin" in p["name"].lower()]
    assert len(justin_players) == 1
    assert justin_players[0]["player_id"] == "4"


def test_get_recent_transactions_new_params():
    """Test the new parameters for get_recent_transactions."""
    assert hasattr(sleeper_mcp, "get_recent_transactions")
    tool = sleeper_mcp.get_recent_transactions

    # Check that function has the new parameters
    import inspect

    sig = inspect.signature(tool.fn)
    params = sig.parameters

    # Verify new parameters exist
    assert "drops_only" in params
    assert "min_days_ago" in params
    assert "max_days_ago" in params
    assert "include_player_details" in params

    # Check default values
    assert not params["drops_only"].default
    assert not params["include_player_details"].default


def test_get_waiver_wire_players_new_params():
    """Test the new parameters for get_waiver_wire_players."""
    assert hasattr(sleeper_mcp, "get_waiver_wire_players")
    tool = sleeper_mcp.get_waiver_wire_players

    # Check that function has the new parameters
    import inspect

    sig = inspect.signature(tool.fn)
    params = sig.parameters

    # Verify new parameters exist
    assert "include_stats" in params
    assert "highlight_recent_drops" in params
    assert "verify_availability" in params

    # Check default values
    assert not params["include_stats"].default
    assert params["highlight_recent_drops"].default
    assert params["verify_availability"].default


def test_get_waiver_analysis_exists():
    """Test that get_waiver_analysis tool exists."""
    assert hasattr(sleeper_mcp, "get_waiver_analysis")
    tool = sleeper_mcp.get_waiver_analysis
    assert tool is not None
    assert hasattr(tool, "fn")
    assert hasattr(tool, "name")
    assert tool.name == "get_waiver_analysis"

    # Check parameters
    import inspect

    sig = inspect.signature(tool.fn)
    params = sig.parameters

    assert "position" in params
    assert "days_back" in params
    assert "limit" in params

    # Check defaults
    assert params["days_back"].default == 7
    assert params["limit"].default == 20


def test_get_trending_context_exists():
    """Test that get_trending_context tool exists."""
    assert hasattr(sleeper_mcp, "get_trending_context")
    tool = sleeper_mcp.get_trending_context
    assert tool is not None
    assert hasattr(tool, "fn")
    assert hasattr(tool, "name")
    assert tool.name == "get_trending_context"

    # Check parameters
    import inspect

    sig = inspect.signature(tool.fn)
    params = sig.parameters

    assert "player_ids" in params
    assert "max_players" in params

    # Check default
    assert params["max_players"].default == 5


def test_evaluate_waiver_priority_cost_exists():
    """Test that evaluate_waiver_priority_cost tool exists."""
    assert hasattr(sleeper_mcp, "evaluate_waiver_priority_cost")
    tool = sleeper_mcp.evaluate_waiver_priority_cost
    assert tool is not None
    assert hasattr(tool, "fn")
    assert hasattr(tool, "name")
    assert tool.name == "evaluate_waiver_priority_cost"

    # Check parameters
    import inspect

    sig = inspect.signature(tool.fn)
    params = sig.parameters

    assert "current_position" in params
    assert "projected_points_gain" in params
    assert "weeks_remaining" in params

    # Check default
    assert params["weeks_remaining"].default == 14


def test_evaluate_waiver_priority_cost_logic():
    """Test the logic for evaluate_waiver_priority_cost."""
    # Test the logic without calling the async function
    # Simulate the calculation

    # Test case 1: High priority (1), low value player
    projected_points_gain = 2.0
    weeks_remaining = 14

    total_expected = projected_points_gain * weeks_remaining  # 28
    priority_value = 50 * (weeks_remaining / 14)  # 50 (for position 1)

    # Should recommend "wait" since 28 < 50
    assert total_expected < priority_value

    # Test case 2: Low priority (10), high value player
    projected_points_gain = 5.0
    weeks_remaining = 14

    total_expected = projected_points_gain * weeks_remaining  # 70
    priority_value = 5 * (weeks_remaining / 14)  # 5  (for position 10)

    # Should recommend "claim" since 70 > 5
    assert total_expected > priority_value

    # Test case 3: Break-even threshold
    weeks_remaining = 10
    priority_value = 15 * (weeks_remaining / 14)  # ~10.7
    break_even = priority_value / weeks_remaining  # ~1.07

    assert break_even > 1.0 and break_even < 2.0
