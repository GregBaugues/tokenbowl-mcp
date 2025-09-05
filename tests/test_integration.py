"""Simple integration tests for the MCP server."""

import pytest
import sys
import os

# Import the module to test
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMCPServer:
    """Test MCP server basic functionality."""

    def test_imports(self):
        """Test that all modules can be imported."""
        import sleeper_mcp
        import players_cache_redis

        # Check that key functions exist
        assert hasattr(sleeper_mcp, "mcp")
        assert hasattr(players_cache_redis, "get_all_players")
        assert hasattr(players_cache_redis, "get_player_by_name")
        assert hasattr(players_cache_redis, "get_player_by_id")

    def test_constants(self):
        """Test that constants are properly defined."""
        import sleeper_mcp

        assert sleeper_mcp.LEAGUE_ID == "1266471057523490816"
        assert sleeper_mcp.BASE_URL == "https://api.sleeper.app/v1"

    def test_mcp_tools_defined(self):
        """Test that MCP tools are defined."""
        import sleeper_mcp

        # Check that the mcp object has the tool decorator
        assert hasattr(sleeper_mcp.mcp, "tool")

        # Check tool functions are defined (they'll be wrapped by decorator)
        tool_names = [
            "get_league_info",
            "get_league_rosters",
            "get_league_users",
            "get_league_matchups",
            "get_nfl_players",
            "search_player_by_name",
            "get_player_by_sleeper_id",
            "get_players_cache_status",
            "refresh_players_cache",
        ]

        for tool_name in tool_names:
            assert hasattr(sleeper_mcp, tool_name), f"Tool {tool_name} not found"

    @pytest.mark.asyncio
    async def test_cache_functions(self):
        """Test that cache functions can be imported and have correct signatures."""
        from players_cache_redis import (
            get_all_players,
            get_player_by_name,
            get_player_by_id,
            get_cache_status,
            force_refresh,
        )

        # These should all be async functions
        import inspect

        assert inspect.iscoroutinefunction(get_all_players)
        assert inspect.iscoroutinefunction(get_player_by_name)
        assert inspect.iscoroutinefunction(get_player_by_id)
        assert inspect.iscoroutinefunction(get_cache_status)
        assert inspect.iscoroutinefunction(force_refresh)
