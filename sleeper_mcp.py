#!/usr/bin/env python3
"""Sleeper API MCP Server - Hardcoded for league 1266471057523490816"""

import httpx
import asyncio
import os
import logging
from fastmcp import FastMCP
from typing import Optional, List, Dict, Any
from players_cache_redis import (
    get_all_players,
    get_player_by_name,
    get_player_by_id,
    get_cache_status,
    force_refresh,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("sleeper-mcp")

# Base URL for Sleeper API
BASE_URL = "https://api.sleeper.app/v1"

# Hardcoded league ID
LEAGUE_ID = "1266471057523490816"


@mcp.tool()
async def get_league_info() -> Dict[str, Any]:
    """Get information about the league"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/league/{LEAGUE_ID}")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_league_rosters() -> List[Dict[str, Any]]:
    """Get all rosters in the league"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/league/{LEAGUE_ID}/rosters")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_league_users() -> List[Dict[str, Any]]:
    """Get all users in the league"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/league/{LEAGUE_ID}/users")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_league_matchups(week: int) -> List[Dict[str, Any]]:
    """Get matchups for a specific week in the league"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/league/{LEAGUE_ID}/matchups/{week}")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_league_transactions(round: int = 1) -> List[Dict[str, Any]]:
    """Get transactions for the league in a specific round"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/league/{LEAGUE_ID}/transactions/{round}"
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_league_traded_picks() -> List[Dict[str, Any]]:
    """Get all traded draft picks in the league"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/league/{LEAGUE_ID}/traded_picks")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_league_drafts() -> List[Dict[str, Any]]:
    """Get all drafts for the league"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/league/{LEAGUE_ID}/drafts")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_league_winners_bracket() -> List[Dict[str, Any]]:
    """Get playoff winners bracket for the league"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/league/{LEAGUE_ID}/winners_bracket")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_user(username_or_id: str) -> Dict[str, Any]:
    """Get user information by username or user ID"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/user/{username_or_id}")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_user_leagues(
    user_id: str, sport: str = "nfl", season: str = "2024"
) -> List[Dict[str, Any]]:
    """Get all leagues for a user in a specific sport and season"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/user/{user_id}/leagues/{sport}/{season}"
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_user_drafts(
    user_id: str, sport: str = "nfl", season: str = "2024"
) -> List[Dict[str, Any]]:
    """Get all drafts for a user in a specific sport and season"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/user/{user_id}/drafts/{sport}/{season}"
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_nfl_players() -> Dict[str, Any]:
    """Get all NFL players from cache (updated daily). Returns a large dataset."""
    try:
        return await get_all_players()
    except Exception as e:
        logger.error(f"Error getting players: {e}")
        return {"error": f"Failed to get players: {str(e)}"}


@mcp.tool()
async def search_player_by_name(name: str) -> List[Dict[str, Any]]:
    """Search for NFL players by name (uses cached data)"""
    try:
        if not name or len(name) < 2:
            return {"error": "Name must be at least 2 characters"}
        return await get_player_by_name(name)
    except Exception as e:
        logger.error(f"Error searching for player {name}: {e}")
        return {"error": f"Failed to search players: {str(e)}"}


@mcp.tool()
async def get_player_by_sleeper_id(player_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific NFL player by their Sleeper ID (uses cached data)"""
    try:
        if not player_id:
            return {"error": "Player ID is required"}
        result = await get_player_by_id(player_id)
        if result:
            return result
        return {"error": f"Player with ID {player_id} not found"}
    except Exception as e:
        logger.error(f"Error getting player {player_id}: {e}")
        return {"error": f"Failed to get player: {str(e)}"}


@mcp.tool()
async def get_players_cache_status() -> Dict[str, Any]:
    """Get the status of the NFL players cache (last updated, TTL, etc.)"""
    try:
        return await get_cache_status()
    except Exception as e:
        logger.error(f"Error getting cache status: {e}")
        return {"error": f"Failed to get cache status: {str(e)}"}


@mcp.tool()
async def refresh_players_cache() -> Dict[str, Any]:
    """Force refresh the NFL players cache from the Sleeper API"""
    try:
        result = await force_refresh()
        return {"success": True, "players_cached": len(result)}
    except Exception as e:
        logger.error(f"Error refreshing cache: {e}")
        return {"error": f"Failed to refresh cache: {str(e)}"}


@mcp.tool()
async def get_trending_players(
    type: str = "add", lookback_hours: Optional[int] = 24, limit: Optional[int] = 25
) -> List[Dict[str, Any]]:
    """
    Get trending players being added or dropped.

    Args:
        type: Either 'add' or 'drop' to see trending adds or drops
        lookback_hours: Number of hours to look back (6, 12, or 24)
        limit: Number of results to return (max 200)
    """
    params = {}
    if lookback_hours:
        params["lookback_hours"] = lookback_hours
    if limit:
        params["limit"] = limit

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/players/nfl/trending/{type}", params=params
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_draft(draft_id: str) -> Dict[str, Any]:
    """Get specific draft information"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/draft/{draft_id}")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_draft_picks(draft_id: str) -> List[Dict[str, Any]]:
    """Get all picks from a specific draft"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/draft/{draft_id}/picks")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_draft_traded_picks(draft_id: str) -> List[Dict[str, Any]]:
    """Get all traded picks in a draft"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/draft/{draft_id}/traded_picks")
        response.raise_for_status()
        return response.json()


if __name__ == "__main__":
    # Run the MCP server with HTTP transport
    import sys
    import os

    # Check for environment variable or command line argument
    if os.getenv("RENDER") or (len(sys.argv) > 1 and sys.argv[1] == "http"):
        # Use PORT env variable (required by Render) or command line arg
        port = int(os.getenv("PORT", 8000))
        if len(sys.argv) > 2:
            port = int(sys.argv[2])

        # Bind to 0.0.0.0 for external access (required for cloud deployment)
        mcp.run(transport="sse", port=port, host="0.0.0.0")
    else:
        # Default to stdio for backward compatibility (Claude Desktop)
        mcp.run()
