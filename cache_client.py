#!/usr/bin/env python3
"""
Enhanced player cache module that uses enriched data from Fantasy Nerds.
Provides automatic refresh on cache miss/expiry.
"""

import json
import gzip
import redis
import os
import logging
from typing import Dict, Any, Optional, Set
from datetime import datetime
from build_cache import cache_players
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


def get_redis_client() -> redis.Redis:
    """Get Redis client connection."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    return redis.from_url(redis_url, decode_responses=False)


def get_players_from_cache(active_only: bool = True) -> Optional[Dict[str, Any]]:
    """
    Get player data from Redis cache.
    Automatically refreshes if cache is missing or expired.

    Args:
        active_only: If True, only return active players (default: True)
    """
    try:
        r = get_redis_client()

        # Try to get cached data
        cache_key = "nfl_players_cache"
        cached_data = r.get(cache_key)

        if cached_data:
            # Check metadata to see if it's fresh enough
            metadata = r.get(f"{cache_key}_metadata")
            if metadata:
                meta = json.loads(metadata)
                last_updated = datetime.fromisoformat(meta.get("last_updated"))
                age_hours = (datetime.now() - last_updated).total_seconds() / 3600

                # If cache is less than 6 hours old, use it
                if age_hours < 6:
                    logger.info(f"Using cached player data ({age_hours:.1f} hours old)")
                    decompressed = gzip.decompress(cached_data).decode("utf-8")
                    players = json.loads(decompressed)

                    # Filter for active players if requested
                    if active_only:
                        active_players = {
                            pid: pdata
                            for pid, pdata in players.items()
                            if pdata.get("active", False) is True
                            and pdata.get("team") is not None
                        }
                        logger.info(
                            f"Filtered to {len(active_players)} active players with teams from {len(players)} total"
                        )
                        return active_players

                    return players
                else:
                    logger.info(f"Cache is {age_hours:.1f} hours old, refreshing...")
            else:
                logger.warning("Cache metadata missing, refreshing")
        else:
            logger.info("No cached data found, fetching fresh data...")

        # Cache is missing or too old - refresh it
        logger.info("Refreshing player cache...")
        success = cache_players()

        if success:
            # Try to get the newly cached data
            cached_data = r.get(cache_key)
            if cached_data:
                decompressed = gzip.decompress(cached_data).decode("utf-8")
                players = json.loads(decompressed)

                # Filter for active players if requested
                if active_only:
                    active_players = {
                        pid: pdata
                        for pid, pdata in players.items()
                        if pdata.get("active", False) is True
                        and pdata.get("team") is not None
                    }
                    logger.info(
                        f"Filtered to {len(active_players)} active players with teams from {len(players)} total"
                    )
                    return active_players

                return players

        logger.error("Failed to refresh cache", exc_info=True)
        return None

    except Exception as e:
        logger.error(
            f"Error accessing player cache (error_type={type(e).__name__}, error_message={str(e)}, active_only={active_only})",
            exc_info=True,
        )
        return None


def normalize_name(name: str) -> str:
    """Normalize player name for matching."""
    return (
        name.lower().replace(".", "").replace("'", "").replace("-", "").replace(" ", "")
    )


def get_name_lookup_from_cache() -> Optional[Dict[str, str]]:
    """Get the player name to Sleeper ID lookup table from cache."""
    try:
        r = get_redis_client()
        cache_key = "player_name_lookup"
        cached_data = r.get(cache_key)

        if cached_data:
            decompressed = gzip.decompress(cached_data).decode("utf-8")
            return json.loads(decompressed)

        logger.warning("Name lookup table not found in cache")
        return None
    except Exception as e:
        logger.error(
            f"Error getting name lookup from cache (error_type={type(e).__name__}, error_message={str(e)})",
            exc_info=True,
        )
        return None


def search_players(query: str, limit: int = 10, active_only: bool = True) -> list:
    """
    Search players by name using cached lookup table for fast access.
    Returns list of matching players with all data.

    Args:
        query: Player name to search for
        limit: Maximum number of results to return (default: 10)
        active_only: If True, only return active players (default: True)
    """
    # Get both the players data and name lookup table
    players = get_players_from_cache(active_only=active_only)
    if not players:
        return []

    name_lookup = get_name_lookup_from_cache()
    normalized_query = normalize_name(query)
    results = []
    matched_ids = set()

    # First, try exact match using the lookup table
    if name_lookup and normalized_query in name_lookup:
        player_id = name_lookup[normalized_query]
        if player_id in players:
            results.append({"player_id": player_id, **players[player_id]})
            matched_ids.add(player_id)

    # Then do partial matching on the lookup table keys
    if name_lookup and len(results) < limit:
        for name_key, player_id in name_lookup.items():
            if player_id not in matched_ids and normalized_query in name_key:
                if player_id in players:
                    results.append({"player_id": player_id, **players[player_id]})
                    matched_ids.add(player_id)
                    if len(results) >= limit:
                        break

    # Fall back to searching full names in player data if needed
    if len(results) < limit:
        query_lower = query.lower()
        for player_id, player in players.items():
            if player_id not in matched_ids:
                full_name = player.get("full_name", "").lower()
                if query_lower in full_name:
                    results.append({"player_id": player_id, **player})
                    matched_ids.add(player_id)
                    if len(results) >= limit:
                        break

    return results


def get_player_by_id(player_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific player by Sleeper ID.
    """
    players = get_players_from_cache()
    if not players:
        return None

    return players.get(player_id)


def spot_refresh_player_stats(player_ids: Optional[Set[str]] = None) -> bool:
    """
    Spot refresh stats for specific players or all players with recent stats.
    This fetches current week stats and updates only those players in cache.

    Args:
        player_ids: Optional set of player IDs to specifically update.
                   If None, updates all players with stats in current week.

    Returns:
        True if update successful, False otherwise
    """
    try:
        # Get current week from NFL schedule
        import httpx

        # Get current week/season info
        current_year = datetime.now().year
        season = str(current_year)

        # Fetch current week from schedule endpoint
        with httpx.Client(timeout=10.0) as client:
            schedule_resp = client.get("https://api.sleeper.app/v1/state/nfl")
            schedule_resp.raise_for_status()
            state = schedule_resp.json()
            current_week = state.get("week", 1)

            logger.info(f"Fetching live stats for week {current_week}, season {season}")

            # Fetch stats for current week
            stats_url = (
                f"https://api.sleeper.app/v1/stats/nfl/regular/{season}/{current_week}"
            )
            stats_resp = client.get(stats_url)
            stats_resp.raise_for_status()
            raw_stats = stats_resp.json()

        # Filter to PPR-relevant stats using the same logic as build_cache
        filtered_stats = filter_ppr_relevant_stats(raw_stats)

        # If specific player_ids provided, filter to just those
        if player_ids:
            filtered_stats = {
                pid: stats for pid, stats in filtered_stats.items() if pid in player_ids
            }

        if not filtered_stats:
            logger.info("No stats to update")
            return True

        # Get Redis client and current cache
        r = get_redis_client()
        cache_key = "nfl_players_cache"

        # Get current cache
        cached_data = r.get(cache_key)
        if not cached_data:
            logger.warning("No cache exists to spot update")
            return False

        # Decompress and load current cache
        decompressed = gzip.decompress(cached_data).decode("utf-8")
        players = json.loads(decompressed)

        # Update stats for matching players
        updated_count = 0
        for player_id, stats in filtered_stats.items():
            if player_id in players:
                # Update the stats.actual structure
                if "stats" not in players[player_id]:
                    players[player_id]["stats"] = {"projected": None, "actual": None}

                # Extract fantasy points
                fantasy_points = stats.get("fantasy_points")

                # Separate game stats from fantasy points
                game_stats = {k: v for k, v in stats.items() if k != "fantasy_points"}

                players[player_id]["stats"]["actual"] = {
                    "fantasy_points": fantasy_points,
                    "game_stats": game_stats if game_stats else None,
                    "game_status": "live",  # Could be enhanced with actual game status
                }
                updated_count += 1

        logger.info(f"Updated stats for {updated_count} players")

        # Re-compress and save back to cache
        compressed = gzip.compress(json.dumps(players).encode("utf-8"))
        r.set(cache_key, compressed)

        # Update metadata with spot refresh time
        metadata = r.get(f"{cache_key}_metadata")
        if metadata:
            meta = json.loads(metadata)
            meta["last_spot_refresh"] = datetime.now().isoformat()
            meta["last_spot_refresh_count"] = updated_count
            r.set(f"{cache_key}_metadata", json.dumps(meta))

        return True

    except Exception as e:
        logger.error(
            f"Error spot refreshing player stats (error_type={type(e).__name__}, error_message={str(e)})",
            exc_info=True,
        )
        return False


def filter_ppr_relevant_stats(stats: Dict[str, Any]) -> Dict[str, Any]:
    """Filter stats to only include PPR points and contributing stats.
    Duplicated from build_cache.py for efficiency."""

    # Define mapping from Sleeper API fields to our descriptive names
    field_mapping = {
        "pts_ppr": "fantasy_points",
        "pass_yd": "passing_yards",
        "pass_td": "passing_touchdowns",
        "pass_int": "passing_interceptions",
        "pass_2pt": "passing_two_point_conversions",
        "rush_att": "carries",  # Rushing attempts
        "rush_yd": "rushing_yards",
        "rush_td": "rushing_touchdowns",
        "rush_2pt": "rushing_two_point_conversions",
        "rec": "receptions",
        "rec_tgt": "targets",
        "rec_yd": "receiving_yards",
        "rec_td": "receiving_touchdowns",
        "rec_2pt": "receiving_two_point_conversions",
        "fum_lost": "fumbles_lost",
        "fgm": "field_goals_made",
        "fgm_0_19": "field_goals_made_0_19",
        "fgm_20_29": "field_goals_made_20_29",
        "fgm_30_39": "field_goals_made_30_39",
        "fgm_40_49": "field_goals_made_40_49",
        "fgm_50p": "field_goals_made_50_plus",
        "fgmiss": "field_goals_missed",
        "xpm": "extra_points_made",
        "xpmiss": "extra_points_missed",
        "def_td": "defensive_touchdowns",
        "def_int": "defensive_interceptions",
        "def_sack": "defensive_sacks",
        "def_ff": "defensive_forced_fumbles",
        "def_fr": "defensive_fumble_recoveries",
        "bonus_pass_yd_300": "bonus_passing_300_yards",
        "bonus_pass_yd_400": "bonus_passing_400_yards",
        "bonus_rush_yd_100": "bonus_rushing_100_yards",
        "bonus_rush_yd_200": "bonus_rushing_200_yards",
        "bonus_rec_yd_100": "bonus_receiving_100_yards",
        "bonus_rec_yd_200": "bonus_receiving_200_yards",
    }

    filtered = {}
    for player_id, player_stats in stats.items():
        if isinstance(player_stats, dict):
            transformed_stats = {}
            fantasy_points = None

            for old_field, new_field in field_mapping.items():
                if old_field in player_stats:
                    value = player_stats[old_field]
                    if value is not None and value != 0:
                        transformed_stats[new_field] = value
                        if old_field == "pts_ppr":
                            fantasy_points = value

            # Only add player if they have fantasy points
            if fantasy_points is not None:
                filtered[player_id] = transformed_stats
        else:
            filtered[player_id] = player_stats

    return filtered


def get_cache_status() -> Dict[str, Any]:
    """
    Get the status of the player cache.
    """
    try:
        r = get_redis_client()

        # Check if cache exists
        cache_key = "nfl_players_cache"
        exists = r.exists(cache_key)

        if not exists:
            return {"exists": False, "message": "Cache not found"}

        # Get metadata
        metadata = r.get(f"{cache_key}_metadata")
        if metadata:
            meta = json.loads(metadata)
            last_updated = datetime.fromisoformat(meta.get("last_updated"))
            age_hours = (datetime.now() - last_updated).total_seconds() / 3600

            # Get refresh history
            history_key = "nfl_players_refresh_history"
            history = []
            history_data = r.lrange(history_key, 0, 4)  # Last 5 refreshes
            for item in history_data:
                history.append(json.loads(item))

            return {
                "exists": True,
                "last_updated": meta.get("last_updated"),
                "age_hours": round(age_hours, 1),
                "total_players": meta.get("total_players"),
                "players_with_projections": meta.get("players_with_projections"),
                "players_with_injuries": meta.get("players_with_injuries"),
                "players_with_news": meta.get("players_with_news"),
                "players_with_stats": meta.get("players_with_stats", 0),
                "current_week": meta.get("current_week"),
                "season": meta.get("season"),
                "compressed_size_mb": round(
                    meta.get("compressed_size_bytes", 0) / 1024 / 1024, 2
                ),
                "refresh_history": history,
            }

        return {"exists": True, "message": "Cache exists but metadata missing"}

    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    # Test the cache
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "status":
            status = get_cache_status()
            print(json.dumps(status, indent=2))
        elif sys.argv[1] == "search":
            if len(sys.argv) > 2:
                results = search_players(sys.argv[2])
                for player in results[:3]:
                    print(
                        f"{player['full_name']} - {player.get('team')} {player.get('position')}"
                    )
                    if player.get("data", {}).get("projections"):
                        print(
                            f"  Proj Points: {player['data']['projections']['proj_pts']}"
                        )
            else:
                print("Usage: python cache_client.py search <name>")
        elif sys.argv[1] == "refresh":
            print("Forcing cache refresh...")
            success = cache_players()
            print("Success!" if success else "Failed!")
    else:
        print("Usage: python cache_client.py [status|search|refresh]")
