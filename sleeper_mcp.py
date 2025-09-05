#!/usr/bin/env python3
"""Token Bowl MCP Server - Fantasy football league management via Sleeper API"""

import httpx
import os
import logging
from dotenv import load_dotenv
from fastmcp import FastMCP
from typing import Optional, List, Dict, Any
from players_cache_redis import (
    get_all_players,
    get_player_by_name,
    get_player_by_id,
    get_cache_status,
    force_refresh,
)
import logfire

# Load environment variables from .env file
load_dotenv()

# Initialize Logfire (reads LOGFIRE_TOKEN from env)
logfire.configure()

# Configure logging to use Logfire as the handler
logging.basicConfig(
    level=logging.INFO,
    handlers=[logfire.LogfireLoggingHandler()],
    format="%(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Auto-instrument httpx for HTTP request tracing
logfire.instrument_httpx()

# Log that the server is starting
league_id = os.environ.get("SLEEPER_LEAGUE_ID", "1266471057523490816")
logger.info(f"Initializing Token Bowl MCP Server with league_id={league_id}")

# Initialize FastMCP server
mcp = FastMCP("tokenbowl-mcp")

# Base URL for Sleeper API
BASE_URL = "https://api.sleeper.app/v1"

# Get league ID from environment variable with fallback to Token Bowl
LEAGUE_ID = os.environ.get("SLEEPER_LEAGUE_ID", "1266471057523490816")


@mcp.tool()
async def get_league_info() -> Dict[str, Any]:
    """Get comprehensive information about the Token Bowl fantasy football league.

    Returns detailed league settings including:
    - League name, season, and current status
    - Roster positions and requirements
    - Scoring settings and rules
    - Playoff configuration and schedule
    - Draft settings and keeper rules
    - League ID: Configured via SLEEPER_LEAGUE_ID env var (default: 1266471057523490816)

    Returns:
        Dict containing all league configuration and settings
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/league/{LEAGUE_ID}")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_league_rosters() -> List[Dict[str, Any]]:
    """Get all team rosters in the Token Bowl league with player assignments.

    Returns roster information for each team including:
    - Roster ID and owner user ID
    - List of player IDs on the roster (starters and bench)
    - Roster settings (wins, losses, ties, points for/against)
    - Taxi squad and injured reserve assignments
    - Keeper information if applicable

    Returns:
        List of roster dictionaries, one for each team in the league
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/league/{LEAGUE_ID}/rosters")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_league_users() -> List[Dict[str, Any]]:
    """Get all users (team owners) participating in the Token Bowl league.

    Returns user information including:
    - User ID and username
    - Display name and avatar
    - Team name for this league
    - Is_owner flag for league commissioners

    Note: Match user_id with roster owner_id to link users to their teams.

    Returns:
        List of user dictionaries for all league participants
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/league/{LEAGUE_ID}/users")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_league_matchups(week: int) -> List[Dict[str, Any]]:
    """Get head-to-head matchups for a specific week in the Token Bowl league.

    Args:
        week: The NFL week number (1-18 for regular season + playoffs).
              Week 1-14 are typically regular season,
              Week 15-17/18 are typically playoffs.

    Returns matchup information including:
    - Roster IDs for competing teams
    - Points scored by each team
    - Player points breakdown (starters and bench)
    - Matchup ID for tracking

    Returns:
        List of matchup dictionaries for the specified week
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/league/{LEAGUE_ID}/matchups/{week}")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_league_transactions(round: int = 1) -> List[Dict[str, Any]]:
    """Get waiver wire and trade transactions for the Token Bowl league.

    Args:
        round: The transaction round/week number (default: 1).
               Transactions are grouped by processing rounds.
               Higher rounds represent more recent transactions.

    Returns transaction details including:
    - Transaction type (waiver, free_agent, trade)
    - Players added and dropped with roster IDs
    - FAAB bid amounts (if applicable)
    - Transaction status and timestamps
    - Trade details if applicable

    Returns:
        List of transaction dictionaries for the specified round
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/league/{LEAGUE_ID}/transactions/{round}"
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_league_traded_picks() -> List[Dict[str, Any]]:
    """Get all future draft picks that have been traded in the Token Bowl league.

    Returns information about traded picks including:
    - Season and round of the pick
    - Original owner roster ID
    - New owner roster ID after trade
    - Previous owner roster ID (if traded multiple times)

    Useful for tracking draft capital and evaluating keeper/dynasty trades.

    Returns:
        List of traded draft pick dictionaries
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/league/{LEAGUE_ID}/traded_picks")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_league_drafts() -> List[Dict[str, Any]]:
    """Get all draft information for the Token Bowl league.

    Returns draft details including:
    - Draft ID and type (snake, auction, linear)
    - Draft status (pre_draft, drafting, complete)
    - Draft order and slot assignments
    - Start time and settings
    - Season year

    Use draft_id with get_draft_picks() for detailed pick information.

    Returns:
        List of draft dictionaries for all league drafts
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/league/{LEAGUE_ID}/drafts")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_league_winners_bracket() -> List[Dict[str, Any]]:
    """Get the playoff winners bracket for the Token Bowl league championship.

    Returns playoff bracket information including:
    - Round number (1 = first round, increases each week)
    - Matchup ID and competing roster IDs
    - Winner and loser roster IDs (when determined)
    - Points scored by each team (when games complete)
    - Playoff seed assignments

    Typically covers weeks 15-17 of the NFL season.

    Returns:
        List of playoff matchup dictionaries for the winners bracket
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/league/{LEAGUE_ID}/winners_bracket")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_user(username_or_id: str) -> Dict[str, Any]:
    """Get detailed information about a Sleeper user by username or user ID.

    Args:
        username_or_id: Either the unique username (string) or user_id (numeric string)
                       of the Sleeper user to look up.

    Returns user profile including:
    - User ID (unique numeric identifier)
    - Username (unique handle)
    - Display name (shown in leagues)
    - Avatar ID for profile picture
    - Account creation date

    Example: get_user("JohnDoe123") or get_user("123456789")

    Returns:
        Dict containing user profile information
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/user/{username_or_id}")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_user_leagues(
    user_id: str, sport: str = "nfl", season: str = "2025"
) -> List[Dict[str, Any]]:
    """Get all fantasy leagues a user is participating in for a specific sport and season.

    Args:
        user_id: The numeric user ID of the Sleeper user (not username).
        sport: The sport type (default: "nfl"). Options: "nfl", "nba", "lcs".
        season: The year as a string (default: "2025"). Must be a valid 4-digit year.

    Returns league information for each league including:
    - League ID and name
    - Total number of teams
    - Scoring settings type
    - League avatar
    - Draft status and ID
    - Season type and status

    Useful for finding all leagues a user is in or checking league activity.

    Returns:
        List of league dictionaries the user is participating in
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/user/{user_id}/leagues/{sport}/{season}"
        )
        response.raise_for_status()
        return response.json()


# @mcp.tool()
# async def get_user_drafts(
#     user_id: str, sport: str = "nfl", season: str = "2025"
# ) -> List[Dict[str, Any]]:
#     """Get all fantasy drafts a user has participated in for a specific sport and season.

#     Args:
#         user_id: The numeric user ID of the Sleeper user (not username).
#         sport: The sport type (default: "nfl"). Options: "nfl", "nba", "lcs".
#         season: The year as a string (default: "2025"). Must be a valid 4-digit year.

#     Returns draft information including:
#     - Draft ID and status (pre_draft, drafting, complete)
#     - Draft type (snake, auction, linear)
#     - Start time and created date
#     - Number of teams and rounds
#     - League ID associated with draft
#     - User's draft position/slot

#     Use draft_id with get_draft_picks() for detailed pick information.

#     Returns:
#         List of draft dictionaries the user has participated in
#     """
#     async with httpx.AsyncClient() as client:
#         response = await client.get(
#             f"{BASE_URL}/user/{user_id}/drafts/{sport}/{season}"
#         )
#         response.raise_for_status()
#         return response.json()


@mcp.tool()
async def get_nfl_players() -> Dict[str, Any]:
    """Get comprehensive data for ALL NFL players from Redis cache.

    WARNING: Returns a LARGE dataset (5MB+) with 5000+ players.
    Consider using search_player_by_name() for specific players.

    Data is cached in Redis and refreshed daily to avoid API rate limits.

    Returns player data including:
    - Player ID (Sleeper's unique identifier)
    - Full name, position, team
    - Age, height, weight, college
    - Injury status and fantasy relevance
    - Years of experience
    - Active/inactive status

    Returns:
        Dict with player_id as keys and player data as values
    """
    try:
        logger.debug("Fetching all NFL players from cache")
        result = await get_all_players()
        logger.info(f"Successfully retrieved {len(result)} players from cache")
        return result
    except Exception as e:
        logger.error(f"Error getting players: {e}", exc_info=True)
        return {"error": f"Failed to get players: {str(e)}"}


@mcp.tool()
async def search_player_by_name(name: str) -> List[Dict[str, Any]]:
    """Search for NFL players by name using cached player database.

    Args:
        name: Player name to search for (minimum 2 characters).
              Supports partial matching and case-insensitive search.
              Examples: "mahomes", "patrick", "davante adams"

    Returns matching players with:
    - Player ID for roster operations
    - Full name and common name variations
    - Current team and position
    - Fantasy-relevant information
    - Injury status if applicable

    Search is performed on locally cached data for instant results.

    Returns:
        List of player dictionaries matching the search term
    """
    try:
        if not name or len(name) < 2:
            return {"error": "Name must be at least 2 characters"}
        return await get_player_by_name(name)
    except Exception as e:
        logger.error(f"Error searching for player {name}: {e}")
        return {"error": f"Failed to search players: {str(e)}"}


@mcp.tool()
async def get_player_by_sleeper_id(player_id: str) -> Optional[Dict[str, Any]]:
    """Get detailed information for a specific NFL player by their Sleeper ID.

    Args:
        player_id: The unique Sleeper player ID (numeric string).
                  This ID is consistent across all Sleeper leagues.
                  Example: "4046" for Patrick Mahomes

    Returns complete player information:
    - Personal details (name, age, height, weight)
    - Team and position
    - Fantasy eligibility and status
    - Injury information
    - Years of experience
    - College and draft info

    Data retrieved from Redis cache for optimal performance.

    Returns:
        Dict with player information or error if not found
    """
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
    """Get the current status and health of the NFL players Redis cache.

    Returns cache information including:
    - Last update timestamp
    - Time until next refresh (TTL)
    - Number of players cached
    - Cache size in memory
    - Redis connection status
    - Any error states

    Cache automatically refreshes every 24 hours.
    Use refresh_players_cache() to force immediate update.

    Returns:
        Dict with cache status metrics and health information
    """
    try:
        return await get_cache_status()
    except Exception as e:
        logger.error(f"Error getting cache status: {e}")
        return {"error": f"Failed to get cache status: {str(e)}"}


@mcp.tool()
async def refresh_players_cache() -> Dict[str, Any]:
    """Force an immediate refresh of the NFL players cache from Sleeper API.

    This operation:
    - Fetches latest player data from Sleeper API
    - Updates Redis cache with new data
    - Resets 24-hour TTL timer
    - May take 3-5 seconds to complete

    Use sparingly to avoid API rate limits.
    Cache normally auto-refreshes daily.

    Returns:
        Dict with success status and number of players cached
    """
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
    """Get trending NFL players based on recent add/drop activity across all Sleeper leagues.

    Args:
        type: Transaction type to track (default: "add")
              - "add": Players being picked up from waivers/free agency
              - "drop": Players being dropped to waivers

        lookback_hours: Time window for trending data (default: 24)
                       Options: 6, 12, or 24 hours
                       Shorter windows show immediate trends.

        limit: Number of players to return (default: 25, max: 200)
               Returns most trending players first.

    Returns player trending data with:
    - Player ID and count of adds/drops
    - Useful for identifying breakout players or injury news
    - Great for waiver wire decisions

    Returns:
        List of dictionaries with player_id and add/drop counts
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
async def get_waiver_wire_players(
    position: Optional[str] = None,
    search_term: Optional[str] = None,
    include_trending: bool = False,
    limit: int = 50,
) -> Dict[str, Any]:
    """Get NFL players available on the waiver wire (not on any team roster).

    This tool identifies free agents by comparing all NFL players against
    currently rostered players in the Token Bowl league.

    Args:
        position: Filter by position (QB, RB, WR, TE, DEF, K).
                 None returns all positions.

        search_term: Search for players by name (case-insensitive).
                    Partial matches are supported.

        include_trending: Include trending add counts from last 24 hours.
                         Helps identify hot waiver pickups.

        limit: Maximum number of players to return (default: 50, max: 200).
              Players are sorted by relevance (active players first).

    Returns waiver wire data including:
    - Total available players count
    - Filtered results based on criteria
    - Player details (name, position, team, status)
    - Trending add counts (if requested)
    - Cache freshness information

    Note: Cache refreshes daily. Recent adds/drops may not be reflected
    immediately in player details, but roster data is fetched live.

    Returns:
        Dict with available players and metadata
    """
    try:
        # Get all current rosters to find rostered players
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/league/{LEAGUE_ID}/rosters")
            response.raise_for_status()
            rosters = response.json()

        # Collect all rostered player IDs
        rostered_players = set()
        for roster in rosters:
            if roster.get("players"):
                rostered_players.update(roster["players"])

        # Get all NFL players from cache
        all_players = await get_all_players()

        # Get trending data if requested
        trending_data = {}
        if include_trending:
            try:
                trending_response = await get_trending_players.fn(
                    type="add", lookback_hours=24, limit=200
                )
                trending_data = {
                    item["player_id"]: item["count"] for item in trending_response
                }
            except Exception as e:
                logger.warning(f"Could not fetch trending data: {e}")

        # Filter to find available players
        available_players = []
        for player_id, player_data in all_players.items():
            # Skip if player is rostered
            if player_id in rostered_players:
                continue

            # Skip if player doesn't match position filter
            if position and player_data.get("position") != position.upper():
                continue

            # Skip if player doesn't match search term
            if search_term:
                player_name = (
                    player_data.get("full_name", "")
                    or f"{player_data.get('first_name', '')} {player_data.get('last_name', '')}"
                ).lower()
                if search_term.lower() not in player_name:
                    continue

            # Add player to available list
            player_info = {
                "player_id": player_id,
                "name": player_data.get("full_name")
                or f"{player_data.get('first_name', '')} {player_data.get('last_name', '')}",
                "position": player_data.get("position"),
                "team": player_data.get("team"),
                "status": player_data.get("status"),
                "age": player_data.get("age"),
                "injury_status": player_data.get("injury_status"),
            }

            # Add trending count if available
            if player_id in trending_data:
                player_info["trending_add_count"] = trending_data[player_id]

            available_players.append(player_info)

        # Sort players by relevance
        # Priority: 1) Active status, 2) Trending adds, 3) Name
        def sort_key(player):
            # Active players first
            status_priority = 0 if player.get("status") == "Active" else 1
            # Then by trending adds (negative for descending)
            trending = -player.get("trending_add_count", 0)
            # Then alphabetically
            name = player.get("name", "")
            return (status_priority, trending, name)

        available_players.sort(key=sort_key)

        # Apply limit
        filtered_players = available_players[: min(limit, 200)]

        # Get cache status
        cache_status = await get_cache_status()

        return {
            "total_available": len(available_players),
            "filtered_count": len(filtered_players),
            "players": filtered_players,
            "filters_applied": {
                "position": position,
                "search_term": search_term,
                "include_trending": include_trending,
                "limit": limit,
            },
            "cache_info": {
                "last_updated": cache_status.get("last_refresh_time"),
                "stale_warning": cache_status.get("is_stale", False),
            },
        }

    except Exception as e:
        logger.error(f"Error fetching waiver wire players: {e}")
        return {
            "error": f"Failed to fetch waiver wire players: {str(e)}",
            "total_available": 0,
            "filtered_count": 0,
            "players": [],
        }


# @mcp.tool()
# async def get_draft(draft_id: str) -> Dict[str, Any]:
#     """Get comprehensive information about a specific fantasy draft.

#     Args:
#         draft_id: The unique draft identifier from Sleeper.
#                  Obtain from get_league_drafts() or get_user_drafts().

#     Returns draft details including:
#     - Draft type (snake, auction, linear)
#     - Current status (pre_draft, drafting, complete)
#     - Start time and settings
#     - Number of rounds and timer settings
#     - Draft order and slot assignments
#     - Team count and sport
#     - Scoring type and season

#     Use with get_draft_picks() to see actual player selections.

#     Returns:
#         Dict containing all draft configuration and metadata
#     """
#     async with httpx.AsyncClient() as client:
#         response = await client.get(f"{BASE_URL}/draft/{draft_id}")
#         response.raise_for_status()
#         return response.json()


# @mcp.tool()
# async def get_draft_picks(draft_id: str) -> List[Dict[str, Any]]:
#     """Get all player selections from a completed or in-progress draft.

#     Args:
#         draft_id: The unique draft identifier from Sleeper.
#                  Obtain from get_league_drafts() or get_user_drafts().

#     Returns pick information including:
#     - Pick number and round
#     - Player ID of selected player
#     - Roster ID that made the pick
#     - Draft slot position
#     - Keeper status if applicable
#     - Pick metadata (is_keeper, pick_no)

#     Picks are returned in draft order.
#     Use with player data to get player names and details.

#     Returns:
#         List of pick dictionaries in chronological draft order
#     """
#     async with httpx.AsyncClient() as client:
#         response = await client.get(f"{BASE_URL}/draft/{draft_id}/picks")
#         response.raise_for_status()
#         return response.json()


# @mcp.tool()
# async def get_draft_traded_picks(draft_id: str) -> List[Dict[str, Any]]:
#     """Get information about draft picks that were traded before or during a draft.

#     Args:
#         draft_id: The unique draft identifier from Sleeper.
#                  Obtain from get_league_drafts() or get_user_drafts().

#     Returns traded pick details including:
#     - Season and round of the traded pick
#     - Original owner roster ID
#     - New owner roster ID after trade
#     - Previous owner if traded multiple times

#     Useful for tracking draft pick trades in keeper/dynasty leagues.
#     Empty list if no picks were traded.

#     Returns:
#         List of traded draft pick dictionaries
#     """
#     async with httpx.AsyncClient() as client:
#         response = await client.get(f"{BASE_URL}/draft/{draft_id}/traded_picks")
#         response.raise_for_status()
#         return response.json()


@mcp.tool()
async def get_unified_players() -> Dict[str, Any]:
    """Get unified player data combining Sleeper and Fantasy Nerds information.

    Returns enriched player data including:
    - Sleeper base data (name, team, position, status)
    - Fantasy Nerds enrichment (ADP, injuries, projections)
    - Cached for performance with 24-hour refresh

    This provides a comprehensive view of each player combining
    data from multiple sources for better fantasy decisions.

    Returns:
        Dict mapping player IDs to unified player data
    """
    from unified_players_cache import get_unified_players as get_unified

    return await get_unified()


@mcp.tool()
async def search_unified_players(
    name: str, include_ffnerd: bool = True
) -> List[Dict[str, Any]]:
    """Search for players in the unified dataset by name.

    Args:
        name: Player name to search for (min 2 characters).
              Supports partial matching.

        include_ffnerd: Include Fantasy Nerds enrichment data
                       (ADP, injuries, projections) in results.

    Returns player information including:
    - Basic info (name, team, position, age)
    - Sleeper ID for roster operations
    - Fantasy Nerds data if available and requested
    - Search results sorted by relevance

    Returns:
        List of matching players with unified data
    """
    from unified_players_cache import search_unified_players as search_unified

    if len(name) < 2:
        return {"error": "Search term must be at least 2 characters"}

    return await search_unified(name, include_ffnerd)


@mcp.tool()
async def get_unified_player_by_id(sleeper_id: str) -> Optional[Dict[str, Any]]:
    """Get unified player data by Sleeper ID.

    Args:
        sleeper_id: The Sleeper player ID

    Returns complete unified player information:
    - All Sleeper data fields
    - Fantasy Nerds enrichment if available
    - Injury status and ADP
    - Weekly projections

    Returns:
        Dict with unified player data or None if not found
    """
    from unified_players_cache import get_unified_player_by_id as get_unified_by_id

    return await get_unified_by_id(sleeper_id)


@mcp.tool()
async def get_unified_cache_status() -> Dict[str, Any]:
    """Get status of the unified player cache.

    Returns cache information including:
    - Last update timestamp
    - Time until next refresh (TTL)
    - Number of players cached
    - Number of players enriched with FFNerd data
    - Cache size and memory usage
    - Redis connection status

    Useful for monitoring data freshness and debugging.

    Returns:
        Dict with cache status and health metrics
    """
    from unified_players_cache import get_unified_cache_status as get_status

    return await get_status()


@mcp.tool()
async def refresh_unified_cache() -> Dict[str, Any]:
    """Force refresh the unified player cache from both APIs.

    This operation:
    - Fetches latest from Sleeper API
    - Fetches latest from Fantasy Nerds API
    - Maps and merges the datasets
    - Updates Redis cache with unified data
    - Resets 24-hour TTL timer

    May take 5-10 seconds to complete.
    Use sparingly to avoid API rate limits.

    Returns:
        Dict with unified player data and statistics
    """
    from unified_players_cache import update_unified_cache

    data = await update_unified_cache()

    enriched_count = sum(1 for p in data.values() if "ffnerd_data" in p)

    return {
        "success": True,
        "total_players": len(data),
        "enriched_players": enriched_count,
        "message": f"Successfully refreshed unified cache with {len(data)} players ({enriched_count} enriched)",
    }


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
        logger.info(f"Starting MCP server in HTTP/SSE mode on port {port}")
        mcp.run(transport="sse", port=port, host="0.0.0.0")
    else:
        # Default to stdio for backward compatibility (Claude Desktop)
        logger.info("Starting MCP server in STDIO mode for Claude Desktop")
        mcp.run()
