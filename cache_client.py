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
from typing import Dict, Any, Optional
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
                logger.warning("Cache metadata missing, refreshing...")
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

        logger.error("Failed to refresh cache")
        return None

    except Exception as e:
        logger.error(f"Error accessing player cache: {e}")
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
        logger.error(f"Error getting name lookup from cache: {e}")
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
