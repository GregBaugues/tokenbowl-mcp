#!/usr/bin/env python3
"""Token Bowl MCP Server - Fantasy football league management via Sleeper API"""

import httpx
import os
import logging
from dotenv import load_dotenv
from fastmcp import FastMCP
from typing import Optional, List, Dict, Any
from cache_client import (
    get_enriched_players_from_cache as get_all_players,
    search_enriched_players as search_players_unified,
    get_enriched_player_by_id as get_player_by_id,
    get_cache_status as get_unified_cache_status,
)
from build_cache import cache_enriched_players as update_unified_cache
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
async def get_roster(roster_id: int) -> Dict[str, Any]:
    """Get detailed roster information with full player data for a specific team.

    Args:
        roster_id: The roster ID (1-10) for the team you want to view.
                  Note: Roster ID 2 is Bill Beliclaude.

    Returns a comprehensive roster including:
    - Team information (owner, record, points)
    - Full player details for all rostered players
    - Current week projections and scoring
    - Organized into starters, bench, taxi, and IR
    - Useful meta information (total projected points, etc.)

    Returns:
        Dict with roster info and enriched player data
    """
    try:
        # Get all rosters to find the specific one
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/league/{LEAGUE_ID}/rosters")
            response.raise_for_status()
            rosters = response.json()

        # Find the specific roster
        roster = None
        for r in rosters:
            if r.get("roster_id") == roster_id:
                roster = r
                break

        if not roster:
            return {"error": f"Roster ID {roster_id} not found"}

        # Get all player data from cache (sync function, don't await)
        all_players = get_all_players()
        if not all_players:
            return {"error": "Failed to load player data from cache"}

        # Get league users to find owner name
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/league/{LEAGUE_ID}/users")
            response.raise_for_status()
            users = response.json()

        # Find owner info
        owner_info = None
        for user in users:
            if user.get("user_id") == roster.get("owner_id"):
                owner_info = {
                    "user_id": user.get("user_id"),
                    "username": user.get("username"),
                    "display_name": user.get("display_name"),
                    "team_name": user.get("metadata", {}).get(
                        "team_name", user.get("display_name")
                    ),
                }
                break

        # Initialize roster structure
        enriched_roster = {
            "roster_id": roster_id,
            "owner": owner_info,
            "settings": roster.get("settings", {}),
            "starters": [],
            "bench": [],
            "taxi": [],
            "reserve": [],
        }

        # Get player IDs by category
        starters_ids = roster.get("starters", [])
        all_player_ids = roster.get("players", [])
        taxi_ids = roster.get("taxi", []) or []
        reserve_ids = roster.get("reserve", []) or []

        # Track totals for meta information
        total_projected = 0.0
        starters_projected = 0.0

        # Process each player
        for player_id in all_player_ids:
            if not player_id:
                continue

            # Get player data directly from cache
            player_data = all_players.get(player_id, {})

            # Build simplified player info with all cached data
            player_info = {
                "player_id": player_id,
                "name": player_data.get("full_name", f"{player_id} (Unknown)"),
                "position": player_data.get("position"),
                "team": player_data.get("team"),
                "status": player_data.get("status"),
            }

            # Handle team defenses
            if len(player_id) <= 3 and player_id.isalpha():
                player_info["name"] = f"{player_id} Defense"
                player_info["position"] = "DEF"
                player_info["team"] = player_id

            # Add enriched data if available
            if "data" in player_data:
                enriched = player_data["data"]

                # Add current week projections
                if enriched.get("projections"):
                    proj = enriched["projections"]
                    proj_pts = proj.get("proj_pts")
                    if proj_pts:
                        try:
                            pts = float(proj_pts)
                            player_info["projected_points"] = round(pts, 2)
                            player_info["projection_week"] = proj.get("week")

                            # Add to totals
                            total_projected += pts
                            if player_id in starters_ids:
                                starters_projected += pts
                        except (ValueError, TypeError):
                            pass

                # Add injury info
                if enriched.get("injury"):
                    injury = enriched["injury"]
                    player_info["injury"] = {
                        "status": injury.get("game_status"),
                        "description": injury.get("injury"),
                        "last_update": injury.get("last_update"),
                    }

            # Categorize player by roster position
            if player_id in reserve_ids:
                enriched_roster["reserve"].append(player_info)
            elif player_id in taxi_ids:
                enriched_roster["taxi"].append(player_info)
            elif player_id in starters_ids:
                enriched_roster["starters"].append(player_info)
            else:
                enriched_roster["bench"].append(player_info)

        # Add comprehensive meta information
        enriched_roster["meta"] = {
            "total_players": len(all_player_ids),
            "starters_count": len(enriched_roster["starters"]),
            "bench_count": len(enriched_roster["bench"]),
            "total_projected_points": round(total_projected, 2),
            "starters_projected_points": round(starters_projected, 2),
            "bench_projected_points": round(total_projected - starters_projected, 2),
            "injured_count": sum(
                1
                for cat in ["starters", "bench", "taxi", "reserve"]
                for p in enriched_roster[cat]
                if "injury" in p
            ),
            "record": f"{roster['settings'].get('wins', 0)}-{roster['settings'].get('losses', 0)}",
            "points_for": roster["settings"].get("fpts", 0),
            "points_against": roster["settings"].get("fpts_against", 0),
        }

        return enriched_roster

    except Exception as e:
        logger.error(f"Error getting roster {roster_id}: {e}")
        return {"error": f"Failed to get roster: {str(e)}"}


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


# Commented out - this MCP server is for a specific league (Token Bowl)
# @mcp.tool()
# async def get_user_leagues(
#     user_id: str, sport: str = "nfl", season: str = "2025"
# ) -> List[Dict[str, Any]]:
#     """Get all fantasy leagues a user is participating in for a specific sport and season.
#
#     Args:
#         user_id: The numeric user ID of the Sleeper user (not username).
#         sport: The sport type (default: "nfl"). Options: "nfl", "nba", "lcs".
#         season: The year as a string (default: "2025"). Must be a valid 4-digit year.
#
#     Returns league information for each league including:
#     - League ID and name
#     - Total number of teams
#     - Scoring settings type
#     - League avatar
#     - Draft status and ID
#     - Season type and status
#
#     Useful for finding all leagues a user is in or checking league activity.
#
#     Returns:
#         List of league dictionaries the user is participating in
#     """
#     async with httpx.AsyncClient() as client:
#         response = await client.get(
#             f"{BASE_URL}/user/{user_id}/leagues/{sport}/{season}"
#         )
#         response.raise_for_status()
#         return response.json()


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
async def get_players() -> Dict[str, Any]:
    """Get comprehensive NFL player data with Fantasy Nerds enrichment.

    Returns unified player data including:
    - Sleeper base data (name, team, position, status, age, etc.)
    - Fantasy Nerds enrichment (ADP, injuries, projections)
    - Player IDs for both systems

    Data is cached in Redis (24-hour TTL) with ~1,200+ players enriched.

    WARNING: Returns large dataset (3,800+ players).
    Consider using search_players() for specific players.

    Returns:
        Dict with player_id as keys and unified player data as values
    """
    try:
        logger.debug("Fetching all players from unified cache")
        result = await get_all_players()
        logger.info(f"Successfully retrieved {len(result)} players from cache")
        return result
    except Exception as e:
        logger.error(f"Error getting players: {e}", exc_info=True)
        return {"error": f"Failed to get players: {str(e)}"}


@mcp.tool()
async def search_players_by_name(name: str) -> List[Dict[str, Any]]:
    """Search for players by name with unified Sleeper + Fantasy Nerds data.

    Args:
        name: Player name to search for (minimum 2 characters).

              Format examples:
              - Last name only: "mahomes", "jefferson", "hill"
              - First name only: "patrick", "justin", "tyreek"
              - Full name: "patrick mahomes", "justin jefferson"
              - Partial name: "dav" (matches Davante, David, etc.)

              Notes:
              - Case-insensitive matching
              - Spaces are optional: "patrickMahomes" works
              - Partial matches supported: "jeff" finds Jefferson
              - Returns top 10 matches sorted by relevance

    Returns matching players with:
    - Basic info (name, team, position, age, status)
    - Sleeper ID for roster operations
    - Fantasy Nerds enrichment (ADP, injuries, projections when available)
    - Search results sorted by Sleeper search rank

    Returns:
        List of player dictionaries with unified data (max 10 results)
    """
    try:
        if not name or len(name) < 2:
            return {"error": "Name must be at least 2 characters"}
        return await search_players_unified(name)
    except Exception as e:
        logger.error(f"Error searching for player {name}: {e}")
        return {"error": f"Failed to search players: {str(e)}"}


@mcp.tool()
async def get_player_by_sleeper_id(player_id: str) -> Optional[Dict[str, Any]]:
    """Get unified player data by Sleeper ID.

    Args:
        player_id: The Sleeper player ID (numeric string).
                  Example: "4046" for Patrick Mahomes

    Returns complete unified player information:
    - All Sleeper data fields (name, age, position, team, etc.)
    - Fantasy Nerds enrichment (ADP, injuries, projections)
    - Both Sleeper ID and Fantasy Nerds ID when mapped

    Returns:
        Dict with unified player data or error if not found
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


# Cache status removed - cache management should be handled elsewhere, not in MCP server


# Note: refresh_players_cache removed - cache refresh should be handled by cron job
# The cache auto-refreshes on miss after 24-hour TTL expiration


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
        }

    except Exception as e:
        logger.error(f"Error fetching waiver wire players: {e}")
        return {
            "error": f"Failed to fetch waiver wire players: {str(e)}",
            "total_available": 0,
            "filtered_count": 0,
            "players": [],
        }


@mcp.tool()
async def refresh_players_cache() -> Dict[str, Any]:
    """Refresh the unified player cache with latest Sleeper and Fantasy Nerds data.

    This tool fetches fresh data from both APIs and updates the Redis cache:
    - Sleeper API: All NFL players with current info (team, status, age, etc.)
    - Fantasy Nerds API: Enrichment data (ADP, injuries, projections, rankings)
    - Performs ID mapping between the two systems
    - Compresses and stores in Redis with 24-hour TTL

    Use this when:
    - Player projections appear outdated or missing
    - You need the latest injury reports or ADP data
    - Weekly projections need to be refreshed
    - Cache has expired (check with get_players_cache_status first)

    Note: This operation takes 10-30 seconds as it fetches and processes ~4000 players.

    Returns:
        Dict with refresh results including player counts and enrichment stats
    """
    try:
        logger.info("Starting unified cache refresh...")

        # Get current status before refresh
        before_status = await get_unified_cache_status()

        # Perform the cache refresh
        data = await update_unified_cache()

        # Count enriched players
        enriched_count = sum(1 for p in data.values() if "ffnerd_data" in p)

        # Get new status after refresh
        after_status = await get_unified_cache_status()

        logger.info(
            f"Cache refresh complete: {len(data)} players, {enriched_count} enriched"
        )

        return {
            "success": True,
            "message": "Cache refreshed successfully",
            "statistics": {
                "total_players": len(data),
                "enriched_players": enriched_count,
                "enrichment_rate": f"{(enriched_count / len(data) * 100):.1f}%",
            },
            "cache_info": {
                "ttl_seconds": after_status.get("ttl_seconds", 86400),
                "compressed_size_mb": after_status.get("compressed_size_mb", 0),
                "redis_memory_used_mb": after_status.get("redis_memory_used_mb", 0),
            },
            "before_status": {
                "was_valid": before_status.get("valid", False),
                "previous_players": before_status.get("total_players", 0),
                "previous_enriched": before_status.get("enriched_players", 0),
            },
        }

    except Exception as e:
        logger.error(f"Error refreshing cache: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to refresh cache. Check REDIS_URL and FFNERD_API_KEY env vars.",
        }


@mcp.tool()
async def get_players_cache_status() -> Dict[str, Any]:
    """Get the current status of the unified players cache.

    Returns information about:
    - Cache validity and last update time
    - Total players and enrichment statistics
    - TTL (time to live) remaining before expiry
    - Memory usage and compression stats
    - Data source availability (Sleeper + Fantasy Nerds)

    Use this to check if cache needs refreshing before making player queries.

    Returns:
        Dict with cache status and statistics
    """
    try:
        status = await get_unified_cache_status()

        if status.get("valid"):
            return {
                "valid": True,
                "total_players": status.get("total_players", 0),
                "enriched_players": status.get("enriched_players", 0),
                "enrichment_rate": f"{(status.get('enriched_players', 0) / max(status.get('total_players', 1), 1) * 100):.1f}%",
                "last_updated": status.get("last_updated", "Unknown"),
                "ttl_remaining_seconds": status.get("ttl_seconds", 0),
                "ttl_remaining_hours": f"{status.get('ttl_seconds', 0) / 3600:.1f}",
                "cache_size_mb": status.get("compressed_size_mb", 0),
                "redis_memory_mb": status.get("redis_memory_used_mb", 0),
                "recommendation": "Cache is valid and fresh"
                if status.get("ttl_seconds", 0) > 3600
                else "Consider refreshing cache soon",
            }
        else:
            return {
                "valid": False,
                "error": status.get("error", "Cache invalid or missing"),
                "recommendation": "Run refresh_players_cache to populate cache",
            }

    except Exception as e:
        logger.error(f"Error checking cache status: {e}")
        return {
            "valid": False,
            "error": str(e),
            "recommendation": "Check Redis connection and run refresh_players_cache",
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


# Unified player tools removed - consolidated into main player tools above

if __name__ == "__main__":
    # Run the MCP server with HTTP transport
    import sys
    import os

    # Check for environment variable or command line argument
    if os.getenv("RENDER") or (len(sys.argv) > 1 and sys.argv[1] == "http"):
        # Start background cache refresh if enabled (for Render deployment)
        if os.getenv("ENABLE_BACKGROUND_REFRESH", "false").lower() == "true":
            from background_refresh import start_background_refresh

            start_background_refresh()
            logger.info("Background cache refresh enabled")

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
