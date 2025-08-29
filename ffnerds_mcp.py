#!/usr/bin/env python3
"""Fantasy Nerds API MCP Server"""

import httpx
import os
from fastmcp import FastMCP
from typing import Optional, List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("ffnerds-mcp")

# Base URL for Fantasy Nerds API
BASE_URL = "https://api.fantasynerds.com/v1/nfl"

async def _make_request(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """Helper function to make API requests"""
    # Get API key from environment at request time
    api_key = os.getenv("FANTASY_NERDS_API_KEY", "")
    
    if not api_key:
        return {"error": "FANTASY_NERDS_API_KEY environment variable not set"}
    
    if params is None:
        params = {}
    params["apikey"] = api_key
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}{endpoint}", params=params)
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_auction_values(
    teams: Optional[int] = 12,
    budget: Optional[int] = 200,
    format: Optional[str] = "standard"
) -> Dict[str, Any]:
    """Get fantasy football auction values"""
    params = {
        "teams": teams,
        "budget": budget,
        "format": format
    }
    return await _make_request("/auction", params)


@mcp.tool()
async def get_adp(
    teams: Optional[int] = 12,
    format: Optional[str] = "standard"
) -> Dict[str, Any]:
    """Get Average Draft Position (ADP) data"""
    params = {
        "teams": teams,
        "format": format
    }
    return await _make_request("/adp", params)


@mcp.tool()
async def get_bestball_rankings() -> Dict[str, Any]:
    """Get Best Ball rankings"""
    return await _make_request("/bestball")


@mcp.tool()
async def get_bye_weeks() -> Dict[str, Any]:
    """Get current season bye weeks"""
    return await _make_request("/byes")


@mcp.tool()
async def get_defense_rankings() -> Dict[str, Any]:
    """Get defensive team rankings"""
    return await _make_request("/defense-rankings")


@mcp.tool()
async def get_depth_charts() -> Dict[str, Any]:
    """Get NFL team depth charts"""
    return await _make_request("/depth")


@mcp.tool()
async def get_draft_projections() -> Dict[str, Any]:
    """Get draft projections"""
    return await _make_request("/draft-projections")


@mcp.tool()
async def get_draft_rankings(format: Optional[str] = "standard") -> Dict[str, Any]:
    """Get draft rankings and injury risk"""
    params = {"format": format}
    return await _make_request("/draft-rankings", params)


@mcp.tool()
async def get_dynasty_rankings() -> Dict[str, Any]:
    """Get dynasty league rankings"""
    return await _make_request("/dynasty-rankings")


@mcp.tool()
async def get_fantasy_leaders(position: Optional[str] = None) -> Dict[str, Any]:
    """Get fantasy football leaders"""
    params = {}
    if position:
        params["position"] = position
    return await _make_request("/fantasy-leaders", params)


@mcp.tool()
async def get_idp_rankings() -> Dict[str, Any]:
    """Get Individual Defensive Player (IDP) rankings"""
    return await _make_request("/idp-rankings")


@mcp.tool()
async def get_injuries() -> Dict[str, Any]:
    """Get current NFL injury reports"""
    return await _make_request("/injuries")


@mcp.tool()
async def get_nfl_news(player_id: Optional[str] = None) -> Dict[str, Any]:
    """Get NFL news and updates"""
    params = {}
    if player_id:
        params["playerId"] = player_id
    return await _make_request("/news", params)


@mcp.tool()
async def get_nfl_schedule() -> Dict[str, Any]:
    """Get NFL game schedule"""
    return await _make_request("/schedule")


@mcp.tool()
async def get_nfl_teams() -> Dict[str, Any]:
    """Get NFL teams information"""
    return await _make_request("/teams")


@mcp.tool()
async def get_player_adds_drops() -> Dict[str, Any]:
    """Get trending player adds and drops"""
    return await _make_request("/players-add-drop")


@mcp.tool()
async def get_player_details(player_id: str) -> Dict[str, Any]:
    """Get detailed player information"""
    return await _make_request(f"/player/{player_id}")


@mcp.tool()
async def get_player_list(position: Optional[str] = None) -> Dict[str, Any]:
    """Get list of NFL players"""
    params = {}
    if position:
        params["position"] = position
    return await _make_request("/players", params)


@mcp.tool()
async def get_player_tiers(position: Optional[str] = None) -> Dict[str, Any]:
    """Get player tier rankings"""
    params = {}
    if position:
        params["position"] = position
    return await _make_request("/tiers", params)


@mcp.tool()
async def get_playoff_projections() -> Dict[str, Any]:
    """Get fantasy playoff projections"""
    return await _make_request("/playoff-projections")


@mcp.tool()
async def get_ros_projections() -> Dict[str, Any]:
    """Get Rest of Season projections"""
    return await _make_request("/ros-projections")


@mcp.tool()
async def get_weekly_projections(week: Optional[int] = None) -> Dict[str, Any]:
    """Get weekly fantasy projections"""
    params = {}
    if week:
        params["week"] = week
    return await _make_request("/weekly-projections", params)


@mcp.tool()
async def get_weekly_rankings(
    week: Optional[int] = None,
    position: Optional[str] = None,
    format: Optional[str] = "standard"
) -> Dict[str, Any]:
    """Get weekly fantasy rankings"""
    params = {"format": format}
    if week:
        params["week"] = week
    if position:
        params["position"] = position
    return await _make_request("/weekly-rankings", params)


if __name__ == "__main__":
    # This file is meant to be imported, not run directly
    # The main composition server will handle running
    pass