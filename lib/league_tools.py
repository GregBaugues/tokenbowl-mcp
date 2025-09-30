"""Business logic for league operations.

This module contains the business logic for all league-related MCP tools.
Functions in this module are used by the MCP tool definitions in sleeper_mcp.py.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List
from zoneinfo import ZoneInfo

import httpx

from cache_client import (
    get_player_by_id,
    get_players_from_cache,
    spot_refresh_player_stats,
)
from lib.enrichment import enrich_player_full, organize_roster_by_position

logger = logging.getLogger(__name__)


async def fetch_league_info(league_id: str, base_url: str) -> Dict[str, Any]:
    """Fetch and return league information.

    Args:
        league_id: The Sleeper league ID
        base_url: The Sleeper API base URL

    Returns:
        Dict containing all league configuration and settings
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/league/{league_id}")
        response.raise_for_status()
        return response.json()


async def fetch_league_rosters(league_id: str, base_url: str) -> List[Dict[str, Any]]:
    """Fetch all team rosters in the league.

    Args:
        league_id: The Sleeper league ID
        base_url: The Sleeper API base URL

    Returns:
        List of roster dictionaries, one for each team in the league
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/league/{league_id}/rosters")
        response.raise_for_status()
        return response.json()


async def fetch_roster_with_enrichment(
    roster_id: int, league_id: str, base_url: str
) -> Dict[str, Any]:
    """Fetch roster and enrich with full player data.

    This is the most complex league operation function. It:
    - Fetches the specific roster data
    - Enriches all players with full stats and projections
    - Organizes players into starters/bench/taxi/reserve
    - Calculates meta information (projected points, injuries, etc.)

    Args:
        roster_id: The roster ID (1-10)
        league_id: The Sleeper league ID
        base_url: The Sleeper API base URL

    Returns:
        Dict with roster info and enriched player data
    """
    try:
        # Get all rosters to find the specific one
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/league/{league_id}/rosters")
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
            response = await client.get(f"{base_url}/league/{league_id}/users")
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

        # Get current NFL season and week from state
        async with httpx.AsyncClient() as client:
            state_response = await client.get(f"{base_url}/state/nfl")
            state_response.raise_for_status()
            state = state_response.json()

        current_season = state.get("season", datetime.now().year)
        current_week = state.get("week", 1)

        # Initialize roster structure with current datetime in EDT
        edt_time = datetime.now(ZoneInfo("America/New_York"))
        formatted_datetime = edt_time.strftime("%A, %B %d, %Y at %I:%M %p EDT")

        enriched_roster = {
            "current_datetime": formatted_datetime,
            "season": current_season,
            "week": current_week,
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

        # Spot refresh stats for roster players
        player_ids_set = set(filter(None, all_player_ids))  # Filter out None values
        if player_ids_set:
            logger.info(
                f"Spot refreshing stats for roster players (count={len(player_ids_set)}, roster_id={roster_id})"
            )
            spot_refresh_player_stats(player_ids_set)

        # Track totals for meta information
        total_projected = 0.0
        starters_projected = 0.0

        # Enrich all players using utility functions
        enriched_players = []
        for player_id in all_player_ids:
            if not player_id:
                continue

            # Get player data from cache
            player_data = all_players.get(player_id, {})

            # Use enrichment utility to get fully enriched player data
            player_info = enrich_player_full(
                player_id,
                player_data,
                include_position_stats=True,
                max_news=3,
            )

            # Track projected points for meta info
            if player_info["stats"]["projected"]:
                fantasy_points = player_info["stats"]["projected"]["fantasy_points"]
                total_projected += fantasy_points
                if player_id in starters_ids:
                    starters_projected += fantasy_points

            enriched_players.append(player_info)

        # Organize players into roster categories using utility function
        categorized = organize_roster_by_position(
            enriched_players, starters_ids, taxi_ids, reserve_ids
        )
        enriched_roster.update(categorized)

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
        logger.error(
            f"Failed to get roster: {roster_id} - {type(e).__name__}: {str(e)}",
            exc_info=True,
        )
        return {"error": f"Failed to get roster: {str(e)}"}


async def fetch_league_users(league_id: str, base_url: str) -> List[Dict[str, Any]]:
    """Fetch all users in the league.

    Args:
        league_id: The Sleeper league ID
        base_url: The Sleeper API base URL

    Returns:
        List of user dictionaries for all league participants
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/league/{league_id}/users")
        response.raise_for_status()
        return response.json()


async def fetch_league_matchups(
    league_id: str, week: int, base_url: str
) -> List[Dict[str, Any]]:
    """Fetch matchups for a specific week.

    Args:
        league_id: The Sleeper league ID
        week: The NFL week number (1-18)
        base_url: The Sleeper API base URL

    Returns:
        List of matchup dictionaries for the specified week
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/league/{league_id}/matchups/{week}")
        response.raise_for_status()
        matchups = response.json()

        # Collect all player IDs from matchups for spot refresh
        all_player_ids = set()
        for matchup in matchups:
            if matchup and isinstance(matchup, dict):
                players = matchup.get("players", [])
                if players:
                    all_player_ids.update(filter(None, players))

        # Spot refresh stats for all players in matchups
        if all_player_ids:
            logger.info(
                f"Spot refreshing stats for {len(all_player_ids)} players in week {week} matchups"
            )
            spot_refresh_player_stats(all_player_ids)

        return matchups


async def fetch_league_transactions(
    league_id: str, round_num: int, base_url: str
) -> List[Dict[str, Any]]:
    """Fetch transactions with player enrichment.

    Args:
        league_id: The Sleeper league ID
        round_num: The transaction round/week number (must be positive)
        base_url: The Sleeper API base URL

    Returns:
        List of transaction dictionaries with enriched player data
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{base_url}/league/{league_id}/transactions/{round_num}"
        )
        response.raise_for_status()
        transactions = response.json()

    # Enrich transactions with player data
    for txn in transactions:
        # Enrich "adds" with full player data
        if txn.get("adds"):
            enriched_adds = {}
            for player_id, roster_id in txn["adds"].items():
                player_data = get_player_by_id(player_id)
                enriched_adds[player_id] = {
                    "roster_id": roster_id,
                    "player_name": player_data.get("full_name")
                    if player_data
                    else "Unknown",
                    "team": player_data.get("team") if player_data else None,
                    "position": player_data.get("position") if player_data else None,
                }
            txn["adds"] = enriched_adds

        # Enrich "drops" with full player data
        if txn.get("drops"):
            enriched_drops = {}
            for player_id, roster_id in txn["drops"].items():
                player_data = get_player_by_id(player_id)
                enriched_drops[player_id] = {
                    "roster_id": roster_id,
                    "player_name": player_data.get("full_name")
                    if player_data
                    else "Unknown",
                    "team": player_data.get("team") if player_data else None,
                    "position": player_data.get("position") if player_data else None,
                }
            txn["drops"] = enriched_drops

    return transactions


async def fetch_league_traded_picks(
    league_id: str, base_url: str
) -> List[Dict[str, Any]]:
    """Fetch traded draft picks.

    Args:
        league_id: The Sleeper league ID
        base_url: The Sleeper API base URL

    Returns:
        List of traded draft pick dictionaries
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/league/{league_id}/traded_picks")
        response.raise_for_status()
        return response.json()


async def fetch_league_drafts(league_id: str, base_url: str) -> List[Dict[str, Any]]:
    """Fetch draft information.

    Args:
        league_id: The Sleeper league ID
        base_url: The Sleeper API base URL

    Returns:
        List of draft dictionaries for all league drafts
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/league/{league_id}/drafts")
        response.raise_for_status()
        return response.json()


async def fetch_league_winners_bracket(
    league_id: str, base_url: str
) -> List[Dict[str, Any]]:
    """Fetch playoff winners bracket.

    Args:
        league_id: The Sleeper league ID
        base_url: The Sleeper API base URL

    Returns:
        List of playoff matchup dictionaries for the winners bracket
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/league/{league_id}/winners_bracket")
        response.raise_for_status()
        return response.json()
