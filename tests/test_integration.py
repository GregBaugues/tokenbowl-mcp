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
        import cache_client

        # Check that key functions exist
        assert hasattr(sleeper_mcp, "mcp")
        assert hasattr(cache_client, "get_players_from_cache")
        assert hasattr(cache_client, "search_players")
        assert hasattr(cache_client, "get_player_by_id")

    def test_constants(self):
        """Test that constants are properly defined."""
        import sleeper_mcp

        # LEAGUE_ID should be either from env var or default
        expected_league_id = os.environ.get("SLEEPER_LEAGUE_ID", "1266471057523490816")
        assert sleeper_mcp.LEAGUE_ID == expected_league_id
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
            "get_players",
            "search_players_by_name",
            "get_player_by_sleeper_id",
            "get_trending_players",
            "get_waiver_wire_players",
        ]

        for tool_name in tool_names:
            assert hasattr(sleeper_mcp, tool_name), f"Tool {tool_name} not found"

    def test_cache_functions(self):
        """Test that cache functions can be imported and have correct signatures."""
        from cache_client import (
            get_players_from_cache as get_all_players,
            search_players,
            get_player_by_id,
            get_cache_status,
        )

        # These are now regular functions (not async)
        import inspect

        # Verify these are regular functions, not coroutines
        assert callable(get_all_players)
        assert callable(search_players)
        assert callable(get_player_by_id)
        assert callable(get_cache_status)
        
        # They should NOT be async functions
        assert not inspect.iscoroutinefunction(get_all_players)
        assert not inspect.iscoroutinefunction(search_players)
        assert not inspect.iscoroutinefunction(get_player_by_id)
        assert not inspect.iscoroutinefunction(get_cache_status)
