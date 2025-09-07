#!/usr/bin/env python3
"""Token Bowl MCP Server - Fantasy football league management via Sleeper API"""

import httpx
import os
import logging
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from fastmcp import FastMCP
from typing import Optional, List, Dict, Any, Union
from cache_client import (
    get_players_from_cache,
    search_players as search_players_unified,
    get_player_by_id,
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
LEAGUE_ID = os.environ.get("SLEEPER_LEAGUE_ID")
logger.info(f"Initializing Token Bowl MCP Server with league_id={LEAGUE_ID}")

# Initialize FastMCP server
mcp = FastMCP("tokenbowl-mcp")

# Base URL for Sleeper API
BASE_URL = "https://api.sleeper.app/v1"

# Get league ID from environment variable with fallback to Token Bowl


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
    - Useful meta information (projected points for starters, bench points, etc.)

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
        all_players = get_players_from_cache(active_only=False)
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

        # Initialize roster structure with current datetime in EDT
        edt_time = datetime.now(ZoneInfo("America/New_York"))
        formatted_datetime = edt_time.strftime("%A, %B %d, %Y at %I:%M %p EDT")

        enriched_roster = {
            "current_datetime": formatted_datetime,
            "season": None,  # Will be populated from player projections
            "week": None,  # Will be populated from player projections
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

        # Track season and week from projections (will be extracted from first player with projections)
        projection_season = None
        projection_week = None

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

                            # Extract season and week for top-level (only from first player with projections)
                            if projection_season is None and proj.get("season"):
                                projection_season = proj.get("season")
                            if projection_week is None and proj.get("week"):
                                projection_week = proj.get("week")

                            # Include projection data WITHOUT season and week
                            player_info["projections"] = {
                                "points": round(pts, 2),
                                "low": round(float(proj.get("proj_pts_low", pts)), 2)
                                if proj.get("proj_pts_low")
                                else None,
                                "high": round(float(proj.get("proj_pts_high", pts)), 2)
                                if proj.get("proj_pts_high")
                                else None,
                            }

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

                # Add news if available
                if enriched.get("news") and len(enriched["news"]) > 0:
                    # Include latest 3 news items
                    player_info["news"] = enriched["news"][:3]

            # Categorize player by roster position
            if player_id in reserve_ids:
                enriched_roster["reserve"].append(player_info)
            elif player_id in taxi_ids:
                enriched_roster["taxi"].append(player_info)
            elif player_id in starters_ids:
                enriched_roster["starters"].append(player_info)
            else:
                enriched_roster["bench"].append(player_info)

        # Update season and week at top level
        enriched_roster["season"] = projection_season
        enriched_roster["week"] = projection_week

        # Add comprehensive meta information
        enriched_roster["meta"] = {
            "total_players": len(all_player_ids),
            "starters_count": len(enriched_roster["starters"]),
            "bench_count": len(enriched_roster["bench"]),
            "projected_points": round(starters_projected, 2),
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
    """Get comprehensive NFL player data with Fantasy Nerds enrichment (active players on teams only).

    Returns unified player data including:
    - Sleeper base data (name, team, position, status, age, etc.)
    - Fantasy Nerds enrichment (ADP, injuries, projections)
    - Player IDs for both systems
    - Only includes players where active=true and team is not null

    Data is cached in Redis (24-hour TTL) with active players on teams only.

    Returns:
        Dict with player_id as keys and unified player data as values (active players on teams only)
    """
    try:
        logger.debug("Fetching active players from unified cache")
        result = get_players_from_cache(active_only=True)  # Sync function, don't await
        logger.info(f"Successfully retrieved {len(result)} active players from cache")
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
            return []  # Return empty list instead of error dict

        # Run sync function in executor
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, search_players_unified, name)
        return result if result else []
    except Exception as e:
        logger.error(f"Error searching for player {name}: {e}")
        return []  # Return empty list on error


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
            return None  # Return None instead of error dict

        # Run sync function in executor
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, get_player_by_id, player_id)
        return result if result else None
    except Exception as e:
        logger.error(f"Error getting player {player_id}: {e}")
        return None  # Return None on error


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
    - Full player information including name, position, team
    - FFNerd enrichment data (projections, injuries when available)
    - Count of adds/drops
    - Useful for identifying breakout players or injury news
    - Great for waiver wire decisions

    Returns:
        List of dictionaries with enriched player data and add/drop counts
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
        trending_data = response.json()

    # Get cached player data for enrichment
    all_players = get_players_from_cache(active_only=False)

    # Enrich trending data with full player information
    enriched_trending = []
    for item in trending_data:
        player_id = str(item.get("player_id"))
        if player_id in all_players:
            player_data = all_players[player_id].copy()
            player_data["count"] = item.get("count", 0)
            enriched_trending.append(player_data)
        else:
            # If player not in cache, return basic info
            item["player_id"] = player_id
            enriched_trending.append(item)

    return enriched_trending


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

        # Get all NFL players from cache (sync function, don't await)
        all_players = get_players_from_cache(active_only=False)

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

            # Add projections if available from Fantasy Nerds enrichment
            if "data" in player_data and player_data["data"].get("projections"):
                proj = player_data["data"]["projections"]
                if proj.get("proj_pts"):
                    try:
                        player_info["projected_points"] = round(
                            float(proj.get("proj_pts", 0)), 2
                        )
                    except (ValueError, TypeError):
                        pass

            # Add trending count if available
            if player_id in trending_data:
                player_info["trending_add_count"] = trending_data[player_id]

            available_players.append(player_info)

        # Sort players by relevance
        # Priority: 1) Active status, 2) Trending adds, 3) Projected points, 4) Name
        def sort_key(player):
            # Active players first
            status_priority = 0 if player.get("status") == "Active" else 1
            # Then by trending adds (negative for descending)
            trending = -player.get("trending_add_count", 0)
            # Then by projected points (negative for descending)
            proj_points = -player.get("projected_points", 0)
            # Then alphabetically
            name = player.get("name", "")
            return (status_priority, trending, proj_points, name)

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
async def get_nfl_schedule(week: Union[int, None] = None) -> Dict[str, Any]:
    """Get NFL schedule for a specific week or the current week.

    Args:
        week: NFL week number (1-18 for regular season + playoffs).
              If not provided, returns schedule for the current week.

    Returns schedule information including:
    - Season year and current week
    - List of games for the specified week with:
      - Game date/time and TV station
      - Home and away teams
      - Scores (if game has been played)
      - Winner (if game is complete)

    Uses Fantasy Nerds API for comprehensive schedule data.

    Returns:
        Dict with week schedule and game information
    """
    try:
        # Get Fantasy Nerds API key
        api_key = os.environ.get("FFNERD_API_KEY")
        if not api_key:
            return {
                "error": "Fantasy Nerds API key not configured",
                "message": "Set FFNERD_API_KEY environment variable",
            }

        # Fetch schedule from Fantasy Nerds
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.fantasynerds.com/v1/nfl/schedule",
                params={"apikey": api_key},
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()

        # Extract current week from response
        current_week = data.get("current_week", 1)
        season = data.get("season", 2025)

        # Use current week if no week specified
        target_week = week if week is not None else current_week

        # Validate week number
        if target_week < 1 or target_week > 18:
            return {
                "error": f"Invalid week number: {target_week}",
                "message": "Week must be between 1 and 18",
            }

        # Filter games for the specified week
        all_games = data.get("schedule", [])
        week_games = [game for game in all_games if game.get("week") == target_week]

        # Sort games by date/time
        week_games.sort(key=lambda x: x.get("game_date", ""))

        # Format response
        return {
            "season": season,
            "current_week": current_week,
            "requested_week": target_week,
            "games_count": len(week_games),
            "games": week_games,
        }

    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching NFL schedule: {e}")
        return {"error": "Failed to fetch NFL schedule", "details": str(e)}
    except Exception as e:
        logger.error(f"Error getting NFL schedule: {e}")
        return {"error": "Failed to get NFL schedule", "details": str(e)}


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
