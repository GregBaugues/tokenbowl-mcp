"""Tests for parameter validation in Sleeper MCP tools."""

import pytest
import sys
import os

# Import the module to test
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sleeper_mcp


class TestParameterValidation:
    """Test parameter validation for MCP tools."""

    @pytest.mark.asyncio
    async def test_get_roster_validation(self):
        """Test get_roster parameter validation."""
        # Test with invalid type (string that can't be converted)
        result = await sleeper_mcp.get_roster.fn("invalid")
        assert "error" in result
        assert "Roster ID must be" in result["error"]
        assert "integer" in result["error"]

        # Test with out of range roster_id
        result = await sleeper_mcp.get_roster.fn(0)
        assert "error" in result
        assert "must be between 1 and 10" in result["error"]

        result = await sleeper_mcp.get_roster.fn(11)
        assert "error" in result
        assert "must be between 1 and 10" in result["error"]

        # Test with None
        result = await sleeper_mcp.get_roster.fn(None)
        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_league_matchups_validation(self):
        """Test get_league_matchups parameter validation."""
        # Test with invalid type
        result = await sleeper_mcp.get_league_matchups.fn("not_a_number")
        assert len(result) > 0
        assert "error" in result[0]
        assert "Week must be" in result[0]["error"]
        assert "integer" in result[0]["error"]

        # Test with out of range week
        result = await sleeper_mcp.get_league_matchups.fn(0)
        assert len(result) > 0
        assert "error" in result[0]
        assert "must be between 1 and 18" in result[0]["error"]

        result = await sleeper_mcp.get_league_matchups.fn(19)
        assert len(result) > 0
        assert "error" in result[0]
        assert "must be between 1 and 18" in result[0]["error"]

    @pytest.mark.asyncio
    async def test_get_league_transactions_validation(self):
        """Test get_league_transactions parameter validation."""
        # Test with invalid type
        result = await sleeper_mcp.get_league_transactions.fn("invalid")
        assert len(result) > 0
        assert "error" in result[0]
        assert "Invalid round parameter" in result[0]["error"]

        # Test with negative round
        result = await sleeper_mcp.get_league_transactions.fn(0)
        assert len(result) > 0
        assert "error" in result[0]
        assert "Round must be 1 or greater" in result[0]["error"]

    @pytest.mark.asyncio
    async def test_get_recent_transactions_validation(self):
        """Test get_recent_transactions parameter validation."""
        # Test limit validation
        result = await sleeper_mcp.get_recent_transactions.fn(limit="not_a_number")
        assert len(result) > 0
        assert "error" in result[0]
        assert "Invalid limit parameter" in result[0]["error"]

        result = await sleeper_mcp.get_recent_transactions.fn(limit=0)
        assert len(result) > 0
        assert "error" in result[0]
        assert "Limit must be at least 1" in result[0]["error"]

        # Test transaction_type validation
        result = await sleeper_mcp.get_recent_transactions.fn(
            transaction_type="invalid_type"
        )
        assert len(result) > 0
        assert "error" in result[0]
        assert "Invalid transaction_type parameter" in result[0]["error"]

        # Test days_ago validation
        result = await sleeper_mcp.get_recent_transactions.fn(min_days_ago=-1)
        assert len(result) > 0
        assert "error" in result[0]
        assert "Invalid min_days_ago parameter" in result[0]["error"]

        result = await sleeper_mcp.get_recent_transactions.fn(max_days_ago="invalid")
        assert len(result) > 0
        assert "error" in result[0]
        assert "Invalid max_days_ago parameter" in result[0]["error"]

    @pytest.mark.asyncio
    async def test_get_user_validation(self):
        """Test get_user parameter validation."""
        # Test with empty string
        result = await sleeper_mcp.get_user.fn("")
        assert "error" in result
        assert "username_or_id parameter is required" in result["error"]

        # Test with None
        result = await sleeper_mcp.get_user.fn(None)
        assert "error" in result
        assert "username_or_id parameter is required" in result["error"]

    @pytest.mark.asyncio
    async def test_search_players_by_name_validation(self):
        """Test search_players_by_name parameter validation."""
        # Test with empty string
        result = await sleeper_mcp.search_players_by_name.fn("")
        assert len(result) > 0
        assert "error" in result[0]
        assert "Name parameter is required" in result[0]["error"]

        # Test with too short name
        result = await sleeper_mcp.search_players_by_name.fn("a")
        assert len(result) > 0
        assert "error" in result[0]
        assert "at least 2 characters" in result[0]["error"]

    @pytest.mark.asyncio
    async def test_get_player_by_sleeper_id_validation(self):
        """Test get_player_by_sleeper_id parameter validation."""
        # Test with empty string
        result = await sleeper_mcp.get_player_by_sleeper_id.fn("")
        assert "error" in result
        assert "player_id parameter is required" in result["error"]

        # Test with None
        result = await sleeper_mcp.get_player_by_sleeper_id.fn(None)
        assert "error" in result
        assert "player_id parameter is required" in result["error"]

    @pytest.mark.asyncio
    async def test_get_trending_players_validation(self):
        """Test get_trending_players parameter validation."""
        # Test with invalid type
        result = await sleeper_mcp.get_trending_players.fn(type="invalid")
        assert len(result) > 0
        assert "error" in result[0]
        assert "Invalid type parameter" in result[0]["error"]
        assert "valid_values" in result[0]

    @pytest.mark.asyncio
    async def test_get_player_stats_all_weeks_validation(self):
        """Test get_player_stats_all_weeks parameter validation."""
        # Test with empty player_id
        result = await sleeper_mcp.get_player_stats_all_weeks.fn("")
        assert "error" in result
        assert "player_id parameter is required" in result["error"]

        # Test with invalid season
        result = await sleeper_mcp.get_player_stats_all_weeks.fn(
            "1234", season="invalid"
        )
        assert "error" in result
        assert "Invalid season parameter" in result["error"]

        # Test with out of range season
        result = await sleeper_mcp.get_player_stats_all_weeks.fn("1234", season="2008")
        assert "error" in result
        assert "Invalid season parameter" in result["error"]

        result = await sleeper_mcp.get_player_stats_all_weeks.fn("1234", season="2031")
        assert "error" in result
        assert "Invalid season parameter" in result["error"]

    @pytest.mark.asyncio
    async def test_get_waiver_wire_players_validation(self):
        """Test get_waiver_wire_players parameter validation."""
        # Test position validation
        result = await sleeper_mcp.get_waiver_wire_players.fn(position="INVALID")
        assert "error" in result
        assert "Position must be one of" in result["error"]

        # Test limit validation
        result = await sleeper_mcp.get_waiver_wire_players.fn(limit=0)
        assert "error" in result
        assert "Limit must be" in result["error"]

        result = await sleeper_mcp.get_waiver_wire_players.fn(limit="not_a_number")
        assert "error" in result
        assert "Limit must be" in result["error"]

    @pytest.mark.asyncio
    async def test_get_waiver_analysis_validation(self):
        """Test get_waiver_analysis parameter validation."""
        # Test position validation
        result = await sleeper_mcp.get_waiver_analysis.fn(position="INVALID")
        assert "error" in result
        assert "Position must be one of" in result["error"]

        # Test days_back validation
        result = await sleeper_mcp.get_waiver_analysis.fn(days_back=0)
        assert "error" in result
        assert "days_back must be between" in result["error"]

        result = await sleeper_mcp.get_waiver_analysis.fn(days_back=31)
        assert "error" in result
        assert "days_back must be between" in result["error"]

        # Test limit validation
        result = await sleeper_mcp.get_waiver_analysis.fn(limit=0)
        assert "error" in result
        assert "Limit must be" in result["error"]

    @pytest.mark.asyncio
    async def test_get_trending_context_validation(self):
        """Test get_trending_context parameter validation."""
        # Test with empty list
        result = await sleeper_mcp.get_trending_context.fn([])
        assert "error" in result
        assert "player_ids parameter is required" in result["error"]

        # Test with non-list
        result = await sleeper_mcp.get_trending_context.fn("not_a_list")
        assert "error" in result
        assert "expected list" in result["error"]

        # Test max_players validation
        result = await sleeper_mcp.get_trending_context.fn(["1234"], max_players=0)
        assert "error" in result
        assert "Invalid max_players parameter" in result["error"]

        result = await sleeper_mcp.get_trending_context.fn(
            ["1234"], max_players="invalid"
        )
        assert "error" in result
        assert "Invalid max_players parameter" in result["error"]

    @pytest.mark.asyncio
    async def test_evaluate_waiver_priority_cost_validation(self):
        """Test evaluate_waiver_priority_cost parameter validation."""
        # Test current_position validation
        result = await sleeper_mcp.evaluate_waiver_priority_cost.fn(0, 5.0)
        assert "error" in result
        assert "Current position must be between" in result["error"]

        result = await sleeper_mcp.evaluate_waiver_priority_cost.fn(11, 5.0)
        assert "error" in result
        assert "Current position must be between" in result["error"]

        result = await sleeper_mcp.evaluate_waiver_priority_cost.fn("invalid", 5.0)
        assert "error" in result
        assert "Current position must be between" in result["error"]

        # Test projected_points_gain validation
        result = await sleeper_mcp.evaluate_waiver_priority_cost.fn(1, -1.0)
        assert "error" in result
        assert "non-negative" in result["error"]

        result = await sleeper_mcp.evaluate_waiver_priority_cost.fn(1, "invalid")
        assert "error" in result
        assert ("non-negative number" in result["error"] or "could not convert" in result["error"])

        # Test weeks_remaining validation
        result = await sleeper_mcp.evaluate_waiver_priority_cost.fn(
            1, 5.0, weeks_remaining=0
        )
        assert "error" in result
        assert "Weeks remaining must be between" in result["error"]

        result = await sleeper_mcp.evaluate_waiver_priority_cost.fn(
            1, 5.0, weeks_remaining=19
        )
        assert "error" in result
        assert "Weeks remaining must be between" in result["error"]

    @pytest.mark.asyncio
    async def test_get_nfl_schedule_validation(self):
        """Test get_nfl_schedule parameter validation."""
        # Test with invalid week
        result = await sleeper_mcp.get_nfl_schedule.fn(week=0)
        assert "error" in result
        assert "Week must be between" in result["error"]

        result = await sleeper_mcp.get_nfl_schedule.fn(week=19)
        assert "error" in result
        assert "Week must be between" in result["error"]

        result = await sleeper_mcp.get_nfl_schedule.fn(week="invalid")
        assert "error" in result
        assert "Week must be" in result["error"]
        assert "integer" in result["error"]

    @pytest.mark.asyncio
    async def test_search_validation(self):
        """Test search parameter validation."""
        # Test with empty query
        result = await sleeper_mcp.search.fn("")
        assert "results" in result
        assert "error" in result
        assert "Query parameter is required" in result["error"]

        # Test with None
        result = await sleeper_mcp.search.fn(None)
        assert "results" in result
        assert "error" in result
        assert "Query parameter is required" in result["error"]

    @pytest.mark.asyncio
    async def test_fetch_validation(self):
        """Test fetch parameter validation."""
        # Test with empty id
        result = await sleeper_mcp.fetch.fn("")
        assert "error" in result
        assert "ID parameter is required" in result["error"]

        # Test with invalid format (no underscore)
        result = await sleeper_mcp.fetch.fn("invalidformat")
        assert "error" in result
        assert "Invalid ID format" in result["error"]

        # Test with None
        result = await sleeper_mcp.fetch.fn(None)
        assert "error" in result
        assert "ID parameter is required" in result["error"]
