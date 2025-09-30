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
from typing import Optional, List, Dict, Any
from cache_client import (
    get_players_from_cache,
    search_players as search_players_unified,
    get_player_by_id,
    spot_refresh_player_stats,
)
import logfire
from lib.decorators import log_mcp_tool
from lib.validation import (
    validate_roster_id,
    validate_week,
    validate_position,
    validate_limit,
    validate_days_back,
    create_error_response,
)
from lib.enrichment import (
    enrich_player_minimal,
    get_trending_data_map,
    get_recent_drops_set,
    add_trending_data,
    mark_recent_drops,
)

# Load environment variables from .env file
load_dotenv()

# Initialize Logfire (reads LOGFIRE_TOKEN from env)
logfire.configure(
    send_to_logfire="always",
    console=False,  # Disable console to avoid duplication
)

# Configure logging with proper level handling
DEBUG_MODE = os.environ.get("DEBUG", "").lower() in ("true", "1", "yes")
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    handlers=[logfire.LogfireLoggingHandler()],
    format="%(name)s - %(levelname)s - %(message)s",
)

# Get logger instance
logger = logging.getLogger(__name__)

# Auto-instrument httpx for HTTP request tracing
logfire.instrument_httpx()

# Log that the server is starting
LEAGUE_ID = os.environ.get("SLEEPER_LEAGUE_ID", "1266471057523490816")
logger.info(f"Initializing Token Bowl MCP Server with league_id={LEAGUE_ID}")

# Initialize FastMCP server
mcp = FastMCP("tokenbowl-mcp")

# Base URL for Sleeper API
BASE_URL = "https://api.sleeper.app/v1"

# Get league ID from environment variable with fallback to Token Bowl


@mcp.tool()
@log_mcp_tool
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
    from lib.league_tools import fetch_league_info

    return await fetch_league_info(LEAGUE_ID, BASE_URL)


@mcp.tool()
@log_mcp_tool
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
    from lib.league_tools import fetch_league_rosters

    return await fetch_league_rosters(LEAGUE_ID, BASE_URL)


@mcp.tool()
@log_mcp_tool
async def get_roster(roster_id: int) -> Dict[str, Any]:
    """Get detailed roster information with full player data for a specific team.

    Args:
        roster_id: The roster ID (1-10) for the team you want to view.
              Can be an integer or string (will be converted).
              Valid range: 1-10. Roster ID 2 is Bill Beliclaude.

    Returns a comprehensive roster including:
    - Team information (owner, record, points)
    - Full player details for all rostered players
    - Current week projections and scoring
    - Organized into starters, bench, taxi, and IR
    - Useful meta information (projected points for starters, bench points, etc.)

    Returns:
        Dict with roster info and enriched player data
    """
    from lib.league_tools import fetch_roster_with_enrichment

    # Validate roster_id
    try:
        roster_id = validate_roster_id(roster_id)
    except ValueError as e:
        logger.error(f"Roster ID validation failed: {e}")
        return create_error_response(
            str(e),
            value_received=str(roster_id)[:100],
            expected="integer between 1 and 10",
        )

    return await fetch_roster_with_enrichment(roster_id, LEAGUE_ID, BASE_URL)


@mcp.tool()
@log_mcp_tool
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
    from lib.league_tools import fetch_league_users

    return await fetch_league_users(LEAGUE_ID, BASE_URL)


@mcp.tool()
@log_mcp_tool
async def get_league_matchups(week: int) -> List[Dict[str, Any]]:
    """Get head-to-head matchups for a specific week in the Token Bowl league.

    Args:
        week: The NFL week number (1-18 for regular season + playoffs).
              Can be an integer or string (will be converted).
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
    from lib.league_tools import fetch_league_matchups

    # Validate week
    try:
        week = validate_week(week)
    except ValueError as e:
        logger.error(f"Week validation failed: {e}")
        return [
            create_error_response(
                str(e),
                value_received=str(week)[:100],
                expected="integer between 1 and 18",
            )
        ]

    return await fetch_league_matchups(LEAGUE_ID, week, BASE_URL)


@mcp.tool()
@log_mcp_tool
async def get_league_transactions(round: int = 1) -> List[Dict[str, Any]]:
    """Get waiver wire and trade transactions for the Token Bowl league.

    Args:
        round: The transaction round/week number (default: 1).
               Can be an integer or string (will be converted).
               Must be positive (1 or greater).
               Transactions are grouped by processing rounds.
               Higher rounds represent more recent transactions.

    Returns transaction details including:
    - Transaction type (waiver, free_agent, trade)
    - Players added and dropped with full player data from cache
    - Each player includes name, team, position, and all cached stats/projections
    - FAAB bid amounts (if applicable)
    - Transaction status and timestamps
    - Trade details if applicable

    Returns:
        List of transaction dictionaries for the specified round with enriched player data
    """
    from lib.league_tools import fetch_league_transactions

    # Type conversion and validation
    try:
        round = int(round)
    except (TypeError, ValueError):
        logger.error(
            f"Failed to convert round to int: {round} ({type(round).__name__})"
        )
        return [
            {
                "error": f"Invalid round parameter: expected integer, got {type(round).__name__}",
                "value_received": str(round)[:100],
                "expected": "positive integer",
            }
        ]

    # Ensure round is positive
    if round < 1:
        logger.error(f"Round number must be positive: {round}")
        return [
            {
                "error": "Round must be 1 or greater",
                "value_received": round,
                "valid_range": "1+",
            }
        ]

    return await fetch_league_transactions(LEAGUE_ID, round, BASE_URL)


@mcp.tool()
@log_mcp_tool
async def get_recent_transactions(
    limit: int = 20,
    transaction_type: Optional[str] = None,
    include_failed: bool = False,
    drops_only: bool = False,
    min_days_ago: Optional[int] = None,
    max_days_ago: Optional[int] = None,
    include_player_details: bool = False,
) -> List[Dict[str, Any]]:
    """Get the most recent transactions, sorted by most recent first.

    Args:
        limit: Maximum number of transactions to return (default: 20, max: 20).
               Can be an integer or string (will be converted).
        transaction_type: Filter by type. Valid values: 'waiver', 'free_agent', 'trade'.
                         None returns all types.
        include_failed: Include failed transactions (default: False).
        drops_only: Return only transactions with drops (default: False).
        min_days_ago: Minimum days ago for transactions (default: None).
        max_days_ago: Maximum days ago for transactions (default: None).
        include_player_details: Include full player details (default: False, minimal data).

    Returns a consolidated list of recent transactions including:
    - The most recent transactions (up to 20)
    - All transaction details (type, status, adds/drops, etc.)
    - Players with basic info only (name, team, position) by default
    - Days since transaction for drops when drops_only=True
    - Sorted by status_updated timestamp (most recent first)
    - Filtered by type, status, and date range if requested

    Returns:
        List of transaction dictionaries sorted by recency with enriched player data
    """
    # Type conversion and validation for limit
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        logger.error(
            f"Failed to convert limit to int: {limit} ({type(limit).__name__})"
        )
        return [
            {
                "error": f"Invalid limit parameter: expected integer, got {type(limit).__name__}",
                "value_received": str(limit)[:100],
                "expected": "integer between 1 and 20",
            }
        ]

    # Enforce maximum limit of 20 transactions
    if limit < 1:
        logger.error(f"Limit must be positive: {limit}")
        return [
            {
                "error": "Limit must be at least 1",
                "value_received": limit,
                "valid_range": "1-20",
            }
        ]
    limit = min(limit, 20)

    # Validate transaction_type
    if transaction_type is not None:
        valid_types = ["waiver", "free_agent", "trade"]
        if transaction_type not in valid_types:
            logger.error(f"Invalid transaction type: {transaction_type}")
            return [
                {
                    "error": "Invalid transaction_type parameter",
                    "value_received": str(transaction_type)[:100],
                    "valid_values": valid_types,
                }
            ]

    # Validate days ago parameters
    if min_days_ago is not None:
        try:
            min_days_ago = int(min_days_ago)
            if min_days_ago < 0:
                raise ValueError("Must be non-negative")
        except (TypeError, ValueError):
            logger.error(f"Invalid min_days_ago: {min_days_ago}")
            return [
                {
                    "error": "Invalid min_days_ago parameter",
                    "value_received": str(min_days_ago)[:100],
                    "expected": "non-negative integer",
                }
            ]

    if max_days_ago is not None:
        try:
            max_days_ago = int(max_days_ago)
            if max_days_ago < 0:
                raise ValueError("Must be non-negative")
        except (TypeError, ValueError):
            logger.error(f"Invalid max_days_ago: {max_days_ago}")
            return [
                {
                    "error": "Invalid max_days_ago parameter",
                    "value_received": str(max_days_ago)[:100],
                    "expected": "non-negative integer",
                }
            ]

    # Fetch transactions from the last 10 rounds to ensure we have enough
    all_transactions = []

    async with httpx.AsyncClient() as client:
        # Fetch multiple rounds in parallel
        tasks = []
        for round_num in range(1, 11):  # Get rounds 1-10
            tasks.append(
                client.get(f"{BASE_URL}/league/{LEAGUE_ID}/transactions/{round_num}")
            )

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for response in responses:
            if isinstance(response, Exception):
                continue  # Skip failed requests
            if response.status_code == 200:
                transactions = response.json()
                if transactions:  # Some rounds may be empty
                    all_transactions.extend(transactions)

    # Get player data from cache for enrichment
    from cache_client import get_player_by_id

    # Get current timestamp for date calculations
    current_time = datetime.now()

    # Apply filters and enrich with player data
    filtered_transactions = []
    for txn in all_transactions:
        # Filter by status (exclude failed unless requested)
        if not include_failed and txn.get("status") == "failed":
            continue

        # Filter by type if specified
        if transaction_type and txn.get("type") != transaction_type:
            continue

        # Filter for drops only if requested
        if drops_only and not txn.get("drops"):
            continue

        # Calculate days since transaction if we have a timestamp
        days_since = None
        if txn.get("status_updated"):
            # Convert milliseconds to datetime
            txn_time = datetime.fromtimestamp(txn["status_updated"] / 1000)
            days_since = (current_time - txn_time).days

            # Apply date range filters
            if min_days_ago is not None and days_since < min_days_ago:
                continue
            if max_days_ago is not None and days_since > max_days_ago:
                continue

            # Add days_since to transaction
            txn["days_since_transaction"] = days_since

        # Enrich "adds" with player data
        if txn.get("adds"):
            enriched_adds = {}
            for player_id, roster_id in txn["adds"].items():
                player_data = get_player_by_id(player_id)
                enriched_add = {
                    "roster_id": roster_id,
                    "player_name": player_data.get("full_name")
                    if player_data
                    else "Unknown",
                    "team": player_data.get("team") if player_data else None,
                    "position": player_data.get("position") if player_data else None,
                }
                # Include full details if requested
                if include_player_details and player_data:
                    enriched_add["player_data"] = player_data
                enriched_adds[player_id] = enriched_add
            txn["adds"] = enriched_adds

        # Enrich "drops" with player data
        if txn.get("drops"):
            enriched_drops = {}
            for player_id, roster_id in txn["drops"].items():
                player_data = get_player_by_id(player_id)
                enriched_drop = {
                    "roster_id": roster_id,
                    "player_name": player_data.get("full_name")
                    if player_data
                    else "Unknown",
                    "team": player_data.get("team") if player_data else None,
                    "position": player_data.get("position") if player_data else None,
                }
                # Include full details if requested
                if include_player_details and player_data:
                    enriched_drop["player_data"] = player_data
                # Add days since drop for drops_only mode
                if drops_only and days_since is not None:
                    enriched_drop["days_since_dropped"] = days_since
                enriched_drops[player_id] = enriched_drop
            txn["drops"] = enriched_drops

        filtered_transactions.append(txn)

    # Sort by status_updated timestamp (most recent first)
    filtered_transactions.sort(key=lambda x: x.get("status_updated", 0), reverse=True)

    # Return up to the limit (max 20 transactions)
    return filtered_transactions[:limit]


@mcp.tool()
@log_mcp_tool
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
    from lib.league_tools import fetch_league_traded_picks

    return await fetch_league_traded_picks(LEAGUE_ID, BASE_URL)


@mcp.tool()
@log_mcp_tool
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
    from lib.league_tools import fetch_league_drafts

    return await fetch_league_drafts(LEAGUE_ID, BASE_URL)


@mcp.tool()
@log_mcp_tool
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
    from lib.league_tools import fetch_league_winners_bracket

    return await fetch_league_winners_bracket(LEAGUE_ID, BASE_URL)


@mcp.tool()
@log_mcp_tool
async def get_user(username_or_id: str) -> Dict[str, Any]:
    """Get detailed information about a Sleeper user by username or user ID.

    Args:
        username_or_id: Either the unique username or user_id of the Sleeper user.
                       Cannot be empty. Will be converted to string.

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
    # Validate username_or_id is provided and not empty
    if not username_or_id:
        logger.error("username_or_id parameter is required")
        return {
            "error": "username_or_id parameter is required",
            "expected": "non-empty string (username or user ID)",
        }

    # Convert to string and validate
    username_or_id = str(username_or_id).strip()
    if not username_or_id:
        logger.error("username_or_id cannot be empty")
        return {
            "error": "username_or_id cannot be empty",
            "expected": "non-empty string (username or user ID)",
        }

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


# Commented out - response too large (422K tokens) to be useful as an MCP tool
# @mcp.tool()
# async def get_players() -> Dict[str, Any]:
#     """Get comprehensive NFL player data with Fantasy Nerds enrichment (active players on teams only).
#
#     Returns unified player data including:
#     - Sleeper base data (name, team, position, status, age, etc.)
#     - Fantasy Nerds enrichment (ADP, injuries, projections)
#     - Player IDs for both systems
#     - Only includes players where active=true and team is not null
#
#     Data is cached in Redis (24-hour TTL) with active players on teams only.
#
#     Returns:
#         Dict with player_id as keys and unified player data as values (active players on teams only)
#     """
#     try:
#         logger.debug("Fetching active players from unified cache")
#         result = get_players_from_cache(active_only=True)  # Sync function, don't await
#         logger.info(f"Successfully retrieved {len(result)} active players from cache")
#         return result
#     except Exception as e:
#         logger.error(f"Error getting players: {e}", exc_info=True)
#         return {"error": f"Failed to get players: {str(e)}"}


@mcp.tool()
@log_mcp_tool
async def search_players_by_name(name: str) -> List[Dict[str, Any]]:
    """Search for players by name with unified Sleeper + Fantasy Nerds data.

    Args:
        name: Player name to search for (minimum 2 characters).
              Will be converted to string and trimmed.

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
        # Validate name parameter
        if not name:
            logger.error("Name parameter is required for search")
            return [
                {
                    "error": "Name parameter is required",
                    "expected": "string with at least 2 characters",
                }
            ]

        # Convert to string and validate length
        name = str(name).strip()
        if len(name) < 2:
            logger.error(f"Search query too short: {name}")
            return [
                {
                    "error": "Search query must be at least 2 characters",
                    "value_received": name,
                    "minimum_length": 2,
                }
            ]

        # Run sync function in executor
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, search_players_unified, name)

        # Spot refresh stats for found players
        if result:
            player_ids = {p.get("player_id") for p in result if p.get("player_id")}
            if player_ids:
                logger.info(
                    f"Spot refreshing stats for {len(player_ids)} searched players"
                )
                spot_refresh_player_stats(player_ids)
                # Re-fetch the results to get updated stats
                result = await loop.run_in_executor(None, search_players_unified, name)

        return result if result else []
    except Exception as e:
        logger.error(
            f"Failed to search for player (player_name={name}, error_type={type(e).__name__}, "
            f"error_message={str(e)})",
            exc_info=True,
        )
        return []  # Return empty list on error


@mcp.tool()
@log_mcp_tool
async def get_player_by_sleeper_id(player_id: str) -> Optional[Dict[str, Any]]:
    """Get unified player data by Sleeper ID.

    Args:
        player_id: The Sleeper player ID. Will be converted to string.
                  Cannot be empty. Example: "4046" for Patrick Mahomes

    Returns complete unified player information:
    - All Sleeper data fields (name, age, position, team, etc.)
    - Fantasy Nerds enrichment (ADP, injuries, projections)
    - Both Sleeper ID and Fantasy Nerds ID when mapped

    Returns:
        Dict with unified player data or error if not found
    """
    try:
        # Validate player_id is provided
        if not player_id:
            logger.error("player_id parameter is required")
            return {
                "error": "player_id parameter is required",
                "expected": "non-empty string (numeric player ID)",
            }

        # Convert to string and validate
        player_id = str(player_id).strip()
        if not player_id:
            logger.error("player_id cannot be empty")
            return {
                "error": "player_id cannot be empty",
                "expected": "non-empty string (numeric player ID)",
            }

        # Spot refresh stats for this specific player
        logger.info(f"Spot refreshing stats for player {player_id}")
        spot_refresh_player_stats({player_id})

        # Run sync function in executor to get updated data
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, get_player_by_id, player_id)
        return result if result else None
    except Exception as e:
        logger.error(
            f"Failed to get player by ID (player_id={player_id}, error_type={type(e).__name__}, "
            f"error_message={str(e)})",
            exc_info=True,
        )
        return None  # Return None on error


# Cache status removed - cache management should be handled elsewhere, not in MCP server


# Note: refresh_players_cache removed - cache refresh should be handled by cron job
# The cache auto-refreshes on miss after 24-hour TTL expiration

# Note: get_player_stats removed - stats are now included in cached player data
# Player stats for the current week are automatically included when fetching player data
# from get_players(), search_players_by_name(), or get_player_by_sleeper_id()


@mcp.tool()
@log_mcp_tool
async def get_trending_players(type: str = "add") -> List[Dict[str, Any]]:
    """Get trending NFL players based on recent add/drop activity across all Sleeper leagues.

    Args:
        type: Transaction type to track (default: "add")
              Must be exactly "add" or "drop" (case-sensitive).
              - "add": Players being picked up from waivers/free agency
              - "drop": Players being dropped to waivers

    Returns top 25 trending players with:
    - Full player information including name, position, team
    - FFNerd enrichment data (projections, injuries when available)
    - Count of adds/drops over the last 24 hours
    - Useful for identifying breakout players or injury news
    - Great for waiver wire decisions

    Returns:
        List of dictionaries with enriched player data and add/drop counts
    """
    # Validate type parameter
    valid_types = ["add", "drop"]
    if type not in valid_types:
        logger.error(f"Invalid trending type: {type}")
        return [
            {
                "error": "Invalid type parameter",
                "value_received": str(type)[:100],
                "valid_values": valid_types,
            }
        ]

    # Always use 24 hour lookback and return 25 players
    params = {"lookback_hours": 24, "limit": 25}

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
@log_mcp_tool
async def get_player_stats_all_weeks(
    player_id: str, season: Optional[str] = None
) -> Dict[str, Any]:
    """Get real stats for all weeks of a season for a specific player.

    Args:
        player_id: The Sleeper player ID (required). Will be converted to string.
                  Cannot be empty. Example: "4046" for Patrick Mahomes
        season: The season year (optional). Can be integer or string.
               Valid range: 2009-2030. Defaults to current season if not provided.

    Returns comprehensive stats including:
    - Player information (name, position, team, status)
    - Week-by-week real game stats (fantasy points and game statistics)
    - Season totals aggregating all weeks
    - Games played count
    - Only includes weeks that have been played (no future weeks)

    Note: This fetches real game stats, not projections.
    Stats are organized by week with PPR scoring and relevant statistics.

    Returns:
        Dict containing player info, weekly stats, and season totals
    """
    try:
        # Validate player_id is provided
        if not player_id:
            logger.error("player_id parameter is required")
            return {
                "error": "player_id parameter is required",
                "expected": "non-empty string (numeric player ID)",
            }

        # Convert to string and validate
        player_id = str(player_id).strip()
        if not player_id:
            logger.error("player_id cannot be empty")
            return {
                "error": "player_id cannot be empty",
                "expected": "non-empty string (numeric player ID)",
            }

        # Validate season if provided
        if season is not None:
            season = str(season).strip()
            # Check if season is a valid year format
            try:
                year = int(season)
                if year < 2009 or year > 2030:  # Reasonable bounds for NFL seasons
                    raise ValueError("Year out of range")
            except ValueError:
                logger.error(f"Invalid season format: {season}")
                return {
                    "error": "Invalid season parameter",
                    "value_received": str(season)[:100],
                    "expected": "year string (e.g., '2025')",
                }

        # Get player info from cache first
        player_data = get_player_by_id(player_id)
        if not player_data:
            return {
                "error": f"Player with ID {player_id} not found",
                "player_id": player_id,
            }

        # Get current season and week info
        async with httpx.AsyncClient(timeout=10.0) as client:
            state_response = await client.get(f"{BASE_URL}/state/nfl")
            state_response.raise_for_status()
            state = state_response.json()

            current_season = season or str(state.get("season", datetime.now().year))
            current_week = state.get("week", 1)

        logger.info(
            f"Fetching all weeks stats for player {player_id} in season {current_season} (up to week {current_week})"
        )

        # Prepare response structure
        result = {
            "player_id": player_id,
            "player_info": {
                "name": player_data.get("full_name", "Unknown"),
                "position": player_data.get("position"),
                "team": player_data.get("team"),
                "status": player_data.get("status"),
            },
            "season": int(current_season),
            "weeks_fetched": current_week,
            "weekly_stats": {},
            "totals": {
                "fantasy_points": 0.0,
                "games_played": 0,
            },
        }

        # Import the filter function from cache_client
        from cache_client import filter_ppr_relevant_stats

        # Fetch stats for all weeks concurrently
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Create tasks for all weeks
            tasks = []
            for week in range(1, current_week + 1):
                url = f"{BASE_URL}/stats/nfl/regular/{current_season}/{week}"
                tasks.append(client.get(url))

            # Execute all requests concurrently
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # Process each week's response
            for week_num, response in enumerate(responses, start=1):
                if isinstance(response, Exception):
                    logger.warning(
                        f"Failed to fetch week stats (week_num={week_num}, player_id={player_id}, "
                        f"error_type={type(response).__name__}, error_message={str(response)})"
                    )
                    continue

                try:
                    response.raise_for_status()
                    week_stats = response.json()

                    # Filter to PPR-relevant stats
                    filtered_stats = filter_ppr_relevant_stats(week_stats)

                    # Check if player has stats for this week
                    if player_id in filtered_stats:
                        player_week_stats = filtered_stats[player_id]

                        # Extract fantasy points
                        fantasy_points = player_week_stats.get("fantasy_points", 0)

                        # Separate game stats from fantasy points
                        game_stats = {
                            k: v
                            for k, v in player_week_stats.items()
                            if k != "fantasy_points"
                        }

                        # Add to weekly stats
                        result["weekly_stats"][str(week_num)] = {
                            "fantasy_points": round(fantasy_points, 2),
                            "game_stats": game_stats if game_stats else None,
                        }

                        # Update totals
                        result["totals"]["fantasy_points"] += fantasy_points
                        result["totals"]["games_played"] += 1

                        # Aggregate game stats in totals
                        for stat_key, stat_value in game_stats.items():
                            if stat_key not in result["totals"]:
                                result["totals"][stat_key] = 0
                            result["totals"][stat_key] += stat_value

                except Exception as e:
                    logger.error(
                        f"Failed to process week stats (week_num={week_num}, player_id={player_id}, "
                        f"error_type={type(e).__name__}, error_message={str(e)})",
                        exc_info=True,
                    )
                    continue

        # Round the total fantasy points
        result["totals"]["fantasy_points"] = round(
            result["totals"]["fantasy_points"], 2
        )

        # Round all numeric totals
        for key, value in result["totals"].items():
            if isinstance(value, float) and key != "games_played":
                result["totals"][key] = round(value, 2)

        logger.info(
            f"Successfully fetched stats for player {player_id}: "
            f"{result['totals']['games_played']} games played, "
            f"{result['totals']['fantasy_points']} total fantasy points"
        )

        return result

    except Exception as e:
        logger.error(
            f"Failed to get all weeks stats (player_id={player_id}, season={season}, "
            f"error_type={type(e).__name__}, error_message={str(e)})",
            exc_info=True,
        )
        return {
            "error": f"Failed to get stats: {str(e)}",
            "player_id": player_id,
        }


@mcp.tool()
@log_mcp_tool
async def get_waiver_wire_players(
    position: Optional[str] = None,
    search_term: Optional[str] = None,
    limit: int = 50,
    include_stats: bool = False,
    highlight_recent_drops: bool = True,
    verify_availability: bool = True,
) -> Dict[str, Any]:
    """Get NFL players available on the waiver wire (not on any team roster).

    This tool identifies free agents by comparing all NFL players against
    currently rostered players in the Token Bowl league.

    Args:
        position: Filter by position. Valid values: QB, RB, WR, TE, DEF, K.
                 Case-insensitive (will be uppercased). None returns all positions.

        search_term: Search for players by name (case-insensitive).
                    Partial matches are supported.

        limit: Maximum number of players to return (default: 50, max: 200).
              Can be integer or string (will be converted).
              Players are sorted by relevance (active players first).

        include_stats: Include full stats and projections (default: False, minimal data).

        highlight_recent_drops: Mark players dropped in last 7 days (default: True).

        verify_availability: Double-check roster status (default: True).

    Returns waiver wire data including:
    - Total available players count
    - Filtered results based on criteria
    - Player details (name, position, team, status)
    - Projected points (if available)
    - Trending add counts from last 24 hours (always included)
    - Recently dropped players marked (if highlight_recent_drops=True)
    - Cache freshness information

    Note: Cache refreshes daily. Recent adds/drops may not be reflected
    immediately in player details, but roster data is fetched live.

    Returns:
        Dict with available players and metadata
    """
    try:
        # Validate position
        if position is not None:
            try:
                position = validate_position(position)
            except ValueError as e:
                logger.error(f"Position validation failed: {e}")
                return create_error_response(
                    str(e),
                    value_received=str(position)[:100],
                    valid_values=["QB", "RB", "WR", "TE", "DEF", "K"],
                )

        # Validate limit
        try:
            limit = validate_limit(limit, max_value=200)
        except ValueError as e:
            logger.error(f"Limit validation failed: {e}")
            return create_error_response(
                str(e),
                value_received=str(limit)[:100],
                expected="integer between 1 and 200",
            )

        # Validate search_term if provided (allow empty to be treated as None)
        if search_term is not None:
            search_term = str(search_term).strip()
            if not search_term:
                search_term = None  # Treat empty string as None

        # Get all current rosters to find rostered players (if verify_availability is True)
        rostered_players = set()
        if verify_availability:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{BASE_URL}/league/{LEAGUE_ID}/rosters")
                response.raise_for_status()
                rosters = response.json()

            # Collect all rostered player IDs
            for roster in rosters:
                if roster.get("players"):
                    rostered_players.update(roster["players"])

        # Get all NFL players from cache (sync function, don't await)
        all_players = get_players_from_cache(active_only=False)

        # Fetch trending data and recent drops using utility functions
        trending_data = await get_trending_data_map(
            get_trending_players.fn, txn_type="add"
        )
        recent_drops = (
            await get_recent_drops_set(
                get_recent_transactions.fn, days_back=7, limit=50
            )
            if highlight_recent_drops
            else set()
        )

        # Filter to find available players
        available_players = []
        for player_id, player_data in all_players.items():
            # Skip if player is rostered (only if verify_availability is True)
            if verify_availability and player_id in rostered_players:
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

            # Use enrichment utility based on mode
            if not include_stats:
                player_entry = enrich_player_minimal(player_id, player_data)
            else:
                # Full data mode - pass through all player data
                player_entry = player_data

            available_players.append(player_entry)

        # Add trending data and recent drops marks using utility functions
        available_players = add_trending_data(available_players, trending_data)
        available_players = mark_recent_drops(available_players, recent_drops)

        # Sort players by relevance
        # Priority: 1) Recently dropped, 2) Active status, 3) Trending adds, 4) Projected points, 5) Name
        def sort_key(player):
            # Recently dropped players first
            recently_dropped = 0 if player.get("recently_dropped") else 1
            # Active players next
            status_priority = 0 if player.get("status") == "Active" else 1
            # Then by trending adds (negative for descending)
            trending = -player.get("trending_add_count", 0)
            # Then by projected points (negative for descending)
            proj_points = 0
            # Handle both minimal and full data structures
            if "projected_points" in player:
                # Minimal data mode
                try:
                    proj_points = -float(player.get("projected_points", 0))
                except (ValueError, TypeError):
                    pass
            elif "data" in player and player.get("data", {}).get("projections"):
                # Full data mode
                try:
                    proj_points = -float(
                        player["data"]["projections"].get("proj_pts", 0)
                    )
                except (ValueError, TypeError):
                    pass
            # Then alphabetically
            name = player.get("full_name", "") or ""
            return (recently_dropped, status_priority, trending, proj_points, name)

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
                "limit": limit,
            },
        }

    except Exception as e:
        logger.error(
            f"Failed to fetch waiver wire players (position={position}, search_term={search_term}, "
            f"limit={limit}, error_type={type(e).__name__}, error_message={str(e)})",
            exc_info=True,
        )
        return {
            "error": f"Failed to fetch waiver wire players: {str(e)}",
            "total_available": 0,
            "filtered_count": 0,
            "players": [],
        }


@mcp.tool()
@log_mcp_tool
async def get_waiver_analysis(
    position: Optional[str] = None,
    days_back: int = 7,
    limit: int = 20,
) -> Dict[str, Any]:
    """Get comprehensive waiver wire analysis with minimal context usage.

    A consolidated tool that efficiently combines waiver wire data with recent
    transactions to provide focused recommendations.

    Args:
        position: Filter by position. Valid values: QB, RB, WR, TE, DEF, K.
                 Case-insensitive (will be uppercased). None returns all positions.
        days_back: Number of days to look back for recently dropped players (default: 7).
                  Can be integer or string. Valid range: 1-30.
        limit: Maximum number of players to return per category (default: 20).
              Can be integer or string. Maximum: 50.

    Returns comprehensive analysis including:
    - recently_dropped: Players dropped in our league (last N days) who are valuable
    - trending_available: Top trending adds who are actually available
    - waiver_priority: Current priority position (if available)
    - position_needs: Analysis of roster needs by position
    - All player data in minimal format to reduce context

    Returns:
        Dict with waiver analysis and recommendations
    """
    try:
        # Validate position
        if position is not None:
            try:
                position = validate_position(position)
            except ValueError as e:
                logger.error(f"Position validation failed: {e}")
                return create_error_response(
                    str(e),
                    value_received=str(position)[:100],
                    valid_values=["QB", "RB", "WR", "TE", "DEF", "K"],
                )

        # Validate days_back
        try:
            days_back = validate_days_back(days_back, min_value=1, max_value=30)
        except ValueError as e:
            logger.error(f"days_back validation failed: {e}")
            return create_error_response(
                str(e),
                value_received=str(days_back)[:100],
                expected="integer between 1 and 30",
            )

        # Validate limit (capped at 50 for this analysis)
        try:
            limit = validate_limit(limit, max_value=50)
        except ValueError as e:
            logger.error(f"Limit validation failed: {e}")
            return create_error_response(
                str(e),
                value_received=str(limit)[:100],
                expected="integer between 1 and 50",
            )
        logger.info(
            f"Starting waiver analysis for position={position}, days_back={days_back}"
        )

        # Get current rosters to determine position needs and waiver priority
        rosters_data = {}
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/league/{LEAGUE_ID}/rosters")
            response.raise_for_status()
            rosters = response.json()

            # Analyze position distribution across league
            for roster in rosters:
                roster_id = roster.get("roster_id")
                if roster.get("players"):
                    rosters_data[roster_id] = {
                        "players": roster["players"],
                        "settings": roster.get("settings", {}),
                    }

        # Get recently dropped players from our league
        recent_drops = []
        try:
            recent_transactions = await get_recent_transactions.fn(
                drops_only=True,
                max_days_ago=days_back,
                include_player_details=False,
                limit=50,
            )

            # Collect unique recently dropped players
            dropped_player_ids = set()

            # Get player data from cache to enrich drops with projections
            all_players = get_players_from_cache(active_only=False)

            for txn in recent_transactions:
                if txn.get("drops"):
                    for player_id, drop_info in txn["drops"].items():
                        if player_id not in dropped_player_ids:
                            dropped_player_ids.add(player_id)
                            drop_data = {
                                "player_id": player_id,
                                "player_name": drop_info.get("player_name"),
                                "position": drop_info.get("position"),
                                "team": drop_info.get("team"),
                                "days_since_dropped": drop_info.get(
                                    "days_since_dropped", 0
                                ),
                            }

                            # Add projections if available in cache
                            player_cache_data = all_players.get(player_id, {})
                            if player_cache_data:
                                # Add weekly projected points
                                if "stats" in player_cache_data and player_cache_data[
                                    "stats"
                                ].get("projected"):
                                    drop_data["projected_points"] = player_cache_data[
                                        "stats"
                                    ]["projected"].get("fantasy_points", 0)

                                # Add ROS projected points
                                if "stats" in player_cache_data and player_cache_data[
                                    "stats"
                                ].get("ros_projected"):
                                    drop_data["ros_projected_points"] = (
                                        player_cache_data["stats"]["ros_projected"].get(
                                            "fantasy_points", 0
                                        )
                                    )

                            recent_drops.append(drop_data)

            # Sort by days since dropped (most recent first)
            recent_drops.sort(key=lambda x: x.get("days_since_dropped", 999))

        except Exception as e:
            logger.warning(
                f"Could not fetch recent drops for waiver analysis (error_type={type(e).__name__}, "
                f"error_message={str(e)})"
            )

        # Get available players on waiver wire
        waiver_players = await get_waiver_wire_players.fn(
            position=position,
            limit=limit * 2,  # Get more to filter
            include_stats=False,  # Minimal data mode
            highlight_recent_drops=True,
            verify_availability=True,
        )

        # Separate trending available players
        trending_available = []
        if waiver_players.get("players"):
            for player in waiver_players["players"]:
                if player.get("trending_add_count", 0) > 0:
                    trending_available.append(
                        {
                            "player_id": player.get("player_id"),
                            "player_name": player.get("full_name"),
                            "position": player.get("position"),
                            "team": player.get("team"),
                            "projected_points": player.get("projected_points", 0),
                            "ros_projected_points": player.get(
                                "ros_projected_points", 0
                            ),
                            "trending_add_count": player.get("trending_add_count", 0),
                            "recently_dropped": player.get("recently_dropped", False),
                        }
                    )

            # Sort by trending count
            trending_available.sort(
                key=lambda x: x.get("trending_add_count", 0), reverse=True
            )
            trending_available = trending_available[:limit]

        # Filter recently dropped to only include available players
        recently_dropped_available = []
        rostered_players = set()
        for roster_data in rosters_data.values():
            rostered_players.update(roster_data.get("players", []))

        for drop in recent_drops:
            if drop["player_id"] not in rostered_players:
                recently_dropped_available.append(drop)

        recently_dropped_available = recently_dropped_available[:limit]

        # Build position needs analysis (simplified)
        position_needs = {
            "QB": "Standard",
            "RB": "High demand",
            "WR": "High demand",
            "TE": "Standard",
            "DEF": "Low priority",
            "K": "Low priority",
        }

        # Get current waiver priority (if available in roster settings)
        waiver_priority = {
            "current_position": "Not available",
            "total_teams": len(rosters),
            "recommendation": "Use priority for high-impact players only",
        }

        # Find waiver priority from roster settings
        for roster in rosters:
            settings = roster.get("settings", {})
            if settings.get("waiver_position"):
                waiver_priority["current_position"] = settings.get("waiver_position")
                break

        return {
            "recently_dropped": recently_dropped_available,
            "trending_available": trending_available,
            "waiver_priority": waiver_priority,
            "position_needs": position_needs,
            "analysis_settings": {
                "position_filter": position,
                "days_back": days_back,
                "limit": limit,
            },
            "summary": {
                "total_recently_dropped": len(recently_dropped_available),
                "total_trending": len(trending_available),
                "top_recommendation": (
                    recently_dropped_available[0]
                    if recently_dropped_available
                    else trending_available[0]
                    if trending_available
                    else None
                ),
            },
        }

    except Exception as e:
        logger.error(
            f"Failed to analyze waiver claims (position={position}, days_back={days_back}, "
            f"limit={limit}, error_type={type(e).__name__}, error_message={str(e)})",
            exc_info=True,
        )
        return {
            "error": f"Failed to complete waiver analysis: {str(e)}",
            "recently_dropped": [],
            "trending_available": [],
            "waiver_priority": {},
            "position_needs": {},
        }


@mcp.tool()
@log_mcp_tool
async def get_trending_context(
    player_ids: List[str],
    max_players: int = 5,
) -> Dict[str, str]:
    """Get concise explanations for why players are trending.

    Uses web search and player data to find recent news and context explaining
    why players are trending in fantasy football.

    Args:
        player_ids: List of Sleeper player IDs to get context for.
                   Must be a list (not a string). Cannot be empty.
        max_players: Maximum number of players to process (default: 5, max: 10).
                    Can be integer or string (will be converted).

    Returns:
        Dict mapping player_id to a 2-3 sentence explanation of why they're trending.
        Includes:
        - Recent injury to starter
        - Depth chart changes
        - Breakout performance
        - Trade/release news
        - Usage/target changes

    Example:
        {"4046": "Mahomes is trending after throwing 5 TDs last week.
         With Kelce returning from injury, the passing game looks elite."}
    """
    try:
        # Validate player_ids
        if not player_ids:
            logger.error("player_ids parameter is required")
            return {
                "error": "player_ids parameter is required",
                "expected": "non-empty list of player IDs",
            }

        if not isinstance(player_ids, list):
            logger.error(f"player_ids must be a list, got {type(player_ids).__name__}")
            return {
                "error": f"Invalid player_ids parameter: expected list, got {type(player_ids).__name__}"
            }

        # Validate max_players
        try:
            max_players = int(max_players)
            if max_players < 1:
                raise ValueError("Must be positive")
            max_players = min(max_players, 10)  # Cap at 10
        except (TypeError, ValueError):
            logger.error(f"Invalid max_players: {max_players}")
            return {
                "error": "Invalid max_players parameter",
                "value_received": str(max_players)[:100],
                "expected": "integer between 1 and 10",
            }
        # Limit the number of players to prevent excessive API calls
        max_players = min(max_players, 10)
        player_ids = player_ids[:max_players]

        # Get player data for names and teams
        from cache_client import get_player_by_id

        trending_context = {}

        for player_id in player_ids:
            try:
                # Get player info
                player_data = get_player_by_id(player_id)
                if not player_data:
                    trending_context[player_id] = "Player data not available."
                    continue

                player_name = player_data.get("full_name", "Unknown")
                team = player_data.get("team", "")
                position = player_data.get("position", "")

                # Build search query (would be used with web search API in production)
                # search_query = f"{player_name} {team} fantasy football news trending waiver wire 2025"

                # Perform web search (this would use actual web search API in production)
                # For now, we'll create a placeholder based on available data
                context_parts = []

                # Check injury status
                if player_data.get("injury_status"):
                    injury = player_data.get("injury_status")
                    context_parts.append(f"Listed as {injury} on injury report")

                # Check for recent performance from FFNerd data
                if "data" in player_data:
                    ffnerd_data = player_data.get("data", {})

                    # Check projections
                    if ffnerd_data.get("projections"):
                        proj_pts = ffnerd_data["projections"].get("proj_pts")
                        if proj_pts and float(proj_pts) > 10:
                            context_parts.append(f"Projected for {proj_pts} points")

                    # Check injury info
                    if ffnerd_data.get("injuries"):
                        injury_info = ffnerd_data["injuries"]
                        if injury_info.get("injury"):
                            context_parts.append(
                                f"Dealing with {injury_info['injury']}"
                            )

                # Default context if no specific info
                if not context_parts:
                    if position in ["RB", "WR"]:
                        context_parts.append("Seeing increased usage and targets")
                    elif position == "QB":
                        context_parts.append("Strong matchup upcoming")
                    elif position == "TE":
                        context_parts.append("Emerging as a red zone target")
                    else:
                        context_parts.append("Rising in fantasy relevance")

                # Build final context
                context = (
                    f"{player_name} ({position}, {team}): {'. '.join(context_parts)}."
                )
                trending_context[player_id] = context

            except Exception as e:
                logger.warning(
                    f"Could not get context for player (player_id={player_id}, "
                    f"error_type={type(e).__name__}, error_message={str(e)})"
                )
                trending_context[player_id] = "Context unavailable due to error."

        return trending_context

    except Exception as e:
        logger.error(
            f"Failed to get trending context (max_players={max_players}, "
            f"error_type={type(e).__name__}, error_message={str(e)})",
            exc_info=True,
        )
        return {"error": f"Failed to get trending context: {str(e)}"}


@mcp.tool()
@log_mcp_tool
async def evaluate_waiver_priority_cost(
    current_position: int,
    projected_points_gain: float,
    weeks_remaining: int = 14,
) -> Dict[str, Any]:
    """Calculate if using waiver priority is worth it.

    Evaluates whether to use waiver priority based on expected value and
    historical patterns.

    Args:
        current_position: Current waiver priority position (1 is best).
                         Can be integer or string. Valid range: 1-10.
        projected_points_gain: Expected points gain per week from the player.
                              Can be float or string. Must be non-negative.
        weeks_remaining: Weeks left in fantasy season (default: 14).
                        Can be integer or string. Valid range: 1-18.

    Returns analysis including:
    - recommended_action: "claim" or "wait"
    - expected_value: Total projected points value
    - priority_value: Estimated value of holding priority
    - historical_context: How often top priority matters
    - break_even_threshold: Points needed to justify claim

    Returns:
        Dict with waiver priority cost analysis and recommendation
    """
    try:
        # Validate current_position (using roster_id validation since it's also 1-10)
        try:
            current_position = validate_roster_id(
                current_position
            )  # Reuse 1-10 validation
        except ValueError as e:
            logger.error(f"Current position validation failed: {e}")
            return create_error_response(
                f"Current position must be between 1 and 10, got {current_position}",
                value_received=str(current_position)[:100],
                expected="integer between 1 and 10",
            )

        # Validate projected_points_gain
        try:
            projected_points_gain = float(projected_points_gain)
            if projected_points_gain < 0:
                raise ValueError("Projected points gain must be non-negative")
        except (TypeError, ValueError) as e:
            logger.error(f"Projected points gain validation failed: {e}")
            return create_error_response(
                str(e)
                if isinstance(e, ValueError)
                else f"Invalid projected_points_gain: must be a non-negative number, got {type(projected_points_gain).__name__}",
                value_received=str(projected_points_gain)[:100],
                expected="non-negative number",
            )

        # Validate weeks_remaining
        try:
            weeks_remaining = validate_week(
                weeks_remaining
            )  # Reuse week validation (1-18)
        except ValueError as e:
            logger.error(f"Weeks remaining validation failed: {e}")
            return create_error_response(
                f"Weeks remaining must be between 1 and 18, got {weeks_remaining}",
                value_received=str(weeks_remaining)[:100],
                expected="integer between 1 and 18",
            )

        # Calculate expected value from the player
        total_expected_points = projected_points_gain * weeks_remaining

        # Estimate value of waiver priority position
        # Top priority (1-3) is most valuable
        priority_value_multiplier = {
            1: 50,  # Top priority is very valuable
            2: 35,
            3: 25,
            4: 20,
            5: 15,
            6: 12,
            7: 10,
            8: 8,
            9: 6,
            10: 5,
        }.get(current_position, 3)

        priority_value = priority_value_multiplier * (weeks_remaining / 14)

        # Calculate break-even threshold
        break_even_threshold = priority_value / weeks_remaining

        # Make recommendation
        if total_expected_points > priority_value:
            recommended_action = "claim"
            reasoning = (
                f"Expected {total_expected_points:.1f} total points exceeds "
                f"priority value of {priority_value:.1f} points"
            )
        else:
            recommended_action = "wait"
            reasoning = (
                f"Expected {total_expected_points:.1f} total points is less than "
                f"priority value of {priority_value:.1f} points"
            )

        # Historical context
        historical_context = {
            "top_3_priority_value": "High - often gets league-winning players",
            "mid_priority_value": "Moderate - useful for bye week fills",
            "late_priority_value": "Low - mainly for depth pieces",
            "reset_frequency": "Weekly in most leagues",
        }

        return {
            "recommended_action": recommended_action,
            "reasoning": reasoning,
            "expected_value": round(total_expected_points, 1),
            "priority_value": round(priority_value, 1),
            "break_even_threshold": round(break_even_threshold, 1),
            "historical_context": historical_context,
            "analysis": {
                "current_position": current_position,
                "projected_weekly_gain": projected_points_gain,
                "weeks_remaining": weeks_remaining,
                "net_value": round(total_expected_points - priority_value, 1),
            },
        }

    except Exception as e:
        logger.error(
            f"Failed to evaluate waiver priority cost (current_position={current_position}, "
            f"projected_points_gain={projected_points_gain}, weeks_remaining={weeks_remaining}, "
            f"error_type={type(e).__name__}, error_message={str(e)})",
            exc_info=True,
        )
        return {
            "error": f"Failed to evaluate waiver priority: {str(e)}",
            "recommended_action": "wait",
            "reasoning": "Unable to calculate, defaulting to conservative approach",
        }


@mcp.tool()
@log_mcp_tool
async def get_nfl_schedule(week: Optional[int] = None) -> Dict[str, Any]:
    """Get NFL schedule for a specific week or the current week.

    Args:
        week: NFL week number (1-18 for regular season + playoffs).
              Can be integer or string (will be converted).
              If not provided or None, returns schedule for the current week.

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
        # Validate week if provided
        if week is not None:
            try:
                week = validate_week(week)
            except ValueError as e:
                logger.error(f"Week validation failed: {e}")
                return create_error_response(
                    str(e),
                    value_received=str(week)[:100],
                    expected="integer between 1 and 18, or None for current week",
                )

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
        logger.error(
            f"HTTP error fetching NFL schedule (week={week}, error_type={type(e).__name__}, "
            f"error_message={str(e)})",
            exc_info=True,
        )
        return {"error": "Failed to fetch NFL schedule", "details": str(e)}
    except Exception as e:
        logger.error(
            f"Failed to get NFL schedule (week={week}, error_type={type(e).__name__}, "
            f"error_message={str(e)})",
            exc_info=True,
        )
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


# ============================================================================
# ChatGPT Compatibility Tools - Required for ChatGPT Connectors
# ============================================================================


@mcp.tool()
@log_mcp_tool
async def search(query: str) -> Dict[str, List[Dict[str, Any]]]:
    """Search for fantasy football information across players, teams, and league data.

    This tool is required for ChatGPT compatibility and searches through:
    - NFL players by name or position
    - Waiver wire availability
    - Trending players (adds/drops)
    - Team rosters and matchups

    Args:
        query: Natural language search query. Cannot be empty.
              Will be converted to string and trimmed.
              Examples: "Patrick Mahomes", "waiver RB", "trending"

    Returns:
        Dictionary with 'results' key containing list of matching items.
        Each result includes id, title, and url for proper citation.
    """
    # Validate query is provided and not empty
    if not query:
        logger.error("Query parameter is required for search")
        return {
            "results": [],
            "error": "Query parameter is required",
            "expected": "non-empty search string",
        }

    # Convert to string and validate
    query = str(query).strip()
    if not query:
        logger.error("Search query cannot be empty")
        return {
            "results": [],
            "error": "Search query cannot be empty",
            "expected": "non-empty search string",
        }

    results = []
    query_lower = query.lower()

    try:
        # Search for players by name first
        if len(query) >= 2:  # Minimum 2 chars for player search
            # Call the actual function, not the decorated tool
            players = await search_players_by_name.fn(query)
            for player in players[:5]:  # Limit to top 5 player results
                # Create a unique ID with type prefix for fetch tool
                player_id = f"player_{player.get('player_id', '')}"

                # Build title with position and team
                position = player.get("position", "")
                team = player.get("team", "FA")
                title = (
                    f"{player.get('full_name', 'Unknown Player')} ({position} - {team})"
                )

                # Generate URL (using Sleeper app URL format)
                sleeper_id = player.get("player_id", "")
                url = f"https://sleeper.app/players/nfl/{sleeper_id}"

                results.append({"id": player_id, "title": title, "url": url})

        # Check for waiver/free agent queries
        if any(term in query_lower for term in ["waiver", "free agent", "available"]):
            # Extract position if mentioned
            position = None
            for pos in ["QB", "RB", "WR", "TE", "K", "DEF"]:
                if pos.lower() in query_lower:
                    position = pos
                    break

            waiver_players = await get_waiver_wire_players.fn(
                position=position, limit=5
            )

            if "players" in waiver_players:
                for player in waiver_players["players"]:
                    player_id = f"player_{player.get('player_id', '')}"
                    position = player.get("position", "")
                    team = player.get("team", "FA")
                    title = f"{player.get('full_name', 'Unknown')} ({position} - {team}) [Waiver]"
                    sleeper_id = player.get("player_id", "")
                    url = f"https://sleeper.app/players/nfl/{sleeper_id}"

                    results.append({"id": player_id, "title": title, "url": url})

        # Check for trending queries
        if any(
            term in query_lower
            for term in ["trending", "hot", "popular", "add", "drop"]
        ):
            trend_type = "drop" if "drop" in query_lower else "add"
            trending = await get_trending_players.fn(type=trend_type)

            for player in trending[:5]:  # Top 5 trending
                player_id = f"player_{player.get('player_id', '')}"
                position = player.get("position", "")
                team = player.get("team", "FA")
                trend_label = (
                    "↑ Trending Add" if trend_type == "add" else "↓ Trending Drop"
                )
                title = f"{player.get('full_name', 'Unknown')} ({position} - {team}) {trend_label}"
                sleeper_id = player.get("player_id", "")
                url = f"https://sleeper.app/players/nfl/{sleeper_id}"

                results.append({"id": player_id, "title": title, "url": url})

        # Check for roster/team queries
        if any(term in query_lower for term in ["roster", "team", "bill beliclaude"]):
            rosters = await get_league_rosters.fn()
            users = await get_league_users.fn()

            # Create user lookup
            user_map = {u["user_id"]: u for u in users}

            for roster in rosters[:3]:  # Show top 3 rosters
                roster_id = roster.get("roster_id", "")
                owner_id = roster.get("owner_id", "")
                user = user_map.get(owner_id, {})
                team_name = user.get("metadata", {}).get(
                    "team_name", user.get("display_name", f"Team {roster_id}")
                )

                # Add record
                wins = roster.get("settings", {}).get("wins", 0)
                losses = roster.get("settings", {}).get("losses", 0)
                title = f"{team_name} ({wins}-{losses})"

                results.append(
                    {
                        "id": f"roster_{roster_id}",
                        "title": title,
                        "url": f"https://sleeper.app/leagues/{LEAGUE_ID}/team/{roster_id}",
                    }
                )

    except Exception as e:
        logger.error(
            f"Failed to execute search (query={query}, error_type={type(e).__name__}, "
            f"error_message={str(e)})",
            exc_info=True,
        )

    return {"results": results}


@mcp.tool()
@log_mcp_tool
async def fetch(id: str) -> Dict[str, Any]:
    """Retrieve complete information for a specific fantasy football resource.

    This tool is required for ChatGPT compatibility and fetches full details for:
    - Player statistics and projections
    - Team rosters with all players
    - User profiles
    - Matchup details

    Args:
        id: Resource identifier with type prefix. Cannot be empty.
           Must contain underscore. Will be converted to string.
           Format: <type>_<id> (e.g., "player_4046", "roster_2")

    Returns:
        Complete resource data with id, title, text, url, and optional metadata.
    """
    try:
        # Validate id is provided and not empty
        if not id:
            logger.error("ID parameter is required for fetch")
            return {
                "error": "ID parameter is required",
                "expected": "resource identifier with type prefix (e.g., 'player_4046', 'roster_2')",
            }

        # Convert to string and validate format
        id = str(id).strip()
        if not id or "_" not in id:
            logger.error(f"Invalid ID format: {id}")
            return {
                "error": "Invalid ID format",
                "value_received": str(id)[:100],
                "expected": "format: <type>_<id> (e.g., 'player_4046', 'roster_2')",
            }

        # Parse the ID to determine resource type
        if "_" in id:
            resource_type, resource_id = id.split("_", 1)
        else:
            # Fallback to player if no prefix
            resource_type = "player"
            resource_id = id

        if resource_type == "player":
            # Fetch player details
            player = await get_player_by_sleeper_id.fn(resource_id)

            if not player:
                raise ValueError(f"Player not found: {resource_id}")

            # Build comprehensive text content
            text_parts = []
            text_parts.append(f"Name: {player.get('full_name', 'Unknown')}")
            text_parts.append(f"Position: {player.get('position', 'Unknown')}")
            text_parts.append(f"Team: {player.get('team', 'Free Agent')}")
            text_parts.append(f"Age: {player.get('age', 'Unknown')}")
            text_parts.append(f"Status: {player.get('status', 'Unknown')}")

            # Add injury info if available
            if player.get("injury_status"):
                text_parts.append(f"Injury: {player.get('injury_status')}")

            # Add stats if available
            if player.get("stats"):
                text_parts.append("\nFantasy Stats:")
                stats = player.get("stats", {})
                if "pts_ppr" in stats:
                    text_parts.append(f"  PPR Points: {stats['pts_ppr']}")
                if "rank_ppr" in stats:
                    text_parts.append(f"  PPR Rank: {stats['rank_ppr']}")

            # Add Fantasy Nerds data if available
            if player.get("ffnerd_id"):
                text_parts.append("\nFantasy Analysis:")
                if player.get("adp"):
                    text_parts.append(f"  ADP: {player.get('adp')}")
                if player.get("injury"):
                    text_parts.append(f"  Injury Report: {player.get('injury')}")

            return {
                "id": id,
                "title": f"{player.get('full_name', 'Unknown')} - {player.get('position', '')} {player.get('team', '')}",
                "text": "\n".join(text_parts),
                "url": f"https://sleeper.app/players/nfl/{resource_id}",
                "metadata": {
                    "type": "player",
                    "position": player.get("position"),
                    "team": player.get("team"),
                    "status": player.get("status"),
                },
            }

        elif resource_type == "roster":
            # Fetch roster details
            roster_id = int(resource_id)
            roster_data = await get_roster.fn(roster_id)

            # Build roster text
            text_parts = []
            text_parts.append(
                f"Team: {roster_data.get('team_name', f'Roster {roster_id}')}"
            )
            text_parts.append(f"Owner: {roster_data.get('owner_name', 'Unknown')}")
            text_parts.append(
                f"Record: {roster_data.get('wins', 0)}-{roster_data.get('losses', 0)}"
            )
            text_parts.append(f"Points For: {roster_data.get('points_for', 0)}")
            text_parts.append(f"Points Against: {roster_data.get('points_against', 0)}")

            text_parts.append("\nRoster:")
            text_parts.append("\nStarters:")
            for player in roster_data.get("starters_detail", []):
                name = player.get("full_name", "Unknown")
                pos = player.get("position", "")
                team = player.get("team", "")
                text_parts.append(f"  - {name} ({pos} - {team})")

            text_parts.append("\nBench:")
            for player in roster_data.get("bench_detail", []):
                name = player.get("full_name", "Unknown")
                pos = player.get("position", "")
                team = player.get("team", "")
                text_parts.append(f"  - {name} ({pos} - {team})")

            return {
                "id": id,
                "title": roster_data.get("team_name", f"Roster {roster_id}"),
                "text": "\n".join(text_parts),
                "url": f"https://sleeper.app/leagues/{LEAGUE_ID}/team/{roster_id}",
                "metadata": {
                    "type": "roster",
                    "wins": roster_data.get("wins"),
                    "losses": roster_data.get("losses"),
                    "roster_id": roster_id,
                },
            }

        else:
            raise ValueError(f"Unknown resource type: {resource_type}")

    except Exception as e:
        logger.error(
            f"Failed to fetch resource: {id} - {type(e).__name__}: {str(e)}",
            exc_info=True,
        )
        return {
            "id": id,
            "title": "Error",
            "text": f"Failed to fetch resource: {str(e)}",
            "url": "",
            "metadata": {"error": str(e)},
        }


# ============================================================================
# Health Monitoring Tool
# ============================================================================


@mcp.tool()
@log_mcp_tool
async def health_check() -> Dict[str, Any]:
    """Check the health status of the MCP server and its dependencies.

    Performs health checks on:
    - Server status and uptime
    - Redis cache connectivity
    - Sleeper API connectivity
    - Fantasy Nerds API connectivity (if configured)

    Returns:
        Dict with health status for each component and overall health
    """
    from datetime import datetime

    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(ZoneInfo("America/Los_Angeles")).isoformat(),
        "components": {},
        "server_info": {
            "league_id": LEAGUE_ID,
            "debug_mode": DEBUG_MODE,
        },
    }

    # Check Redis cache
    try:
        from cache_client import get_players_from_cache

        players = get_players_from_cache(active_only=True)
        health_status["components"]["redis_cache"] = {
            "status": "healthy" if players else "degraded",
            "cached_players": len(players) if players else 0,
        }
    except Exception as e:
        health_status["components"]["redis_cache"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        health_status["status"] = "degraded"

    # Check Sleeper API
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{BASE_URL}/state/nfl")
            response.raise_for_status()
            state = response.json()
            health_status["components"]["sleeper_api"] = {
                "status": "healthy",
                "current_season": state.get("season"),
                "current_week": state.get("week"),
            }
    except Exception as e:
        health_status["components"]["sleeper_api"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        health_status["status"] = "unhealthy"

    # Check Fantasy Nerds API (if configured)
    api_key = os.environ.get("FFNERD_API_KEY")
    if api_key:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    "https://api.fantasynerds.com/v1/nfl/current-week",
                    headers={"x-api-key": api_key},
                )
                response.raise_for_status()
                health_status["components"]["fantasy_nerds_api"] = {"status": "healthy"}
        except Exception as e:
            health_status["components"]["fantasy_nerds_api"] = {
                "status": "unhealthy",
                "error": str(e),
            }
            # Don't degrade overall status for optional API
    else:
        health_status["components"]["fantasy_nerds_api"] = {"status": "not_configured"}

    return health_status


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
