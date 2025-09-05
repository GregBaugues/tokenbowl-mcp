"""
Unified player cache combining Sleeper and Fantasy Nerds data.
Stores enriched player data in Redis with automatic refresh.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
import gzip
import asyncio

import redis
from redis.exceptions import RedisError
import httpx

from ffnerd.client import FantasyNerdsClient
from ffnerd.mapper import PlayerMapper

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CACHE_TTL = 86400  # 24 hours in seconds

# Cache keys for unified data
UNIFIED_CACHE_KEY = "unified_players:data"
UNIFIED_META_KEY = "unified_players:meta"
FFNERD_CACHE_KEY = "ffnerd_players:data"
SLEEPER_API_URL = "https://api.sleeper.app/v1/players/nfl"


def get_redis_client():
    """Get Redis client with connection pooling"""
    return redis.from_url(
        REDIS_URL,
        decode_responses=False,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
        max_connections=10,
    )


async def fetch_sleeper_players() -> Dict[str, Any]:
    """Fetch player data from Sleeper API"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(SLEEPER_API_URL)
        response.raise_for_status()
        return response.json()


async def fetch_ffnerd_enrichment_data() -> Dict[str, Any]:
    """Fetch enrichment data from Fantasy Nerds API"""
    client = FantasyNerdsClient()  # Will raise if API key not configured

    try:
        # Fetch multiple data points in parallel
        players_task = asyncio.create_task(client.get_players())
        injuries_task = asyncio.create_task(client.get_injuries())
        adp_task = asyncio.create_task(client.get_adp())
        projections_task = asyncio.create_task(client.get_weekly_projections(1))

        players = await players_task
        injuries = await injuries_task
        adp = await adp_task
        projections = await projections_task

        # Organize by player ID for easy lookup
        ffnerd_data = {}

        # Add player base data
        if not isinstance(players, list):
            players = []
        for player in players:
            ffnerd_data[player["playerId"]] = {
                "player_id": player["playerId"],
                "name": player.get("name", ""),
                "team": player.get("team", ""),
                "position": player.get("position", ""),
                "jersey": player.get("jersey"),
                "height": player.get("height"),
                "weight": player.get("weight"),
                "dob": player.get("dob"),
                "college": player.get("college"),
            }

        # Add injury data
        if not isinstance(injuries, list):
            injuries = []
        injury_map = {
            inj["playerId"]: inj
            for inj in injuries
            if isinstance(inj, dict) and "playerId" in inj
        }
        for player_id, injury in injury_map.items():
            if player_id in ffnerd_data:
                ffnerd_data[player_id]["injury"] = {
                    "status": injury.get("injuryCode"),
                    "desc": injury.get("injuryDesc"),
                    "practice_status": injury.get("practiceStatus"),
                    "game_status": injury.get("gameStatus"),
                }

        # Add ADP data
        if not isinstance(adp, list):
            adp = []
        adp_map = {
            item["playerId"]: item
            for item in adp
            if isinstance(item, dict) and "playerId" in item
        }
        for player_id, adp_info in adp_map.items():
            if player_id in ffnerd_data:
                ffnerd_data[player_id]["adp"] = {
                    "avg": adp_info.get("adp"),
                    "min": adp_info.get("adpMin"),
                    "max": adp_info.get("adpMax"),
                    "std_dev": adp_info.get("adpStdev"),
                }

        # Add weekly projections
        # Handle projections - could be dict or list
        if isinstance(projections, dict):
            # If it's a dict, might have a data key or be the data itself
            proj_list = projections.get("data", []) if "data" in projections else []
        elif isinstance(projections, list):
            proj_list = projections
        else:
            proj_list = []

        proj_map = {
            proj["playerId"]: proj
            for proj in proj_list
            if isinstance(proj, dict) and "playerId" in proj
        }
        for player_id, proj in proj_map.items():
            if player_id in ffnerd_data:
                ffnerd_data[player_id]["projection_week1"] = {
                    "projected_points": proj.get("projectedPoints"),
                    "passing_yards": proj.get("passingYards"),
                    "passing_tds": proj.get("passingTDs"),
                    "rushing_yards": proj.get("rushingYards"),
                    "rushing_tds": proj.get("rushingTDs"),
                    "receiving_yards": proj.get("receivingYards"),
                    "receiving_tds": proj.get("receivingTDs"),
                    "receptions": proj.get("receptions"),
                }

        return ffnerd_data

    except Exception as e:
        print(f"Error fetching FFNerd data: {e}")
        return {}


async def build_unified_player_data() -> Dict[str, Any]:
    """
    Build unified player dataset combining Sleeper and Fantasy Nerds data.
    Returns dict with Sleeper player IDs as keys.
    """
    print("Building unified player dataset...")

    # Fetch data from both sources
    sleeper_players = await fetch_sleeper_players()
    ffnerd_data = await fetch_ffnerd_enrichment_data()

    # Initialize mapper for ID translation with the mapping file
    from pathlib import Path

    mapping_file = Path(__file__).parent / "data" / "player_mapping.json"
    mapper = PlayerMapper(mapping_file=str(mapping_file))

    # Build unified dataset
    unified_players = {}
    enriched_count = 0

    for sleeper_id, player in sleeper_players.items():
        if player and isinstance(player, dict):
            # Filter to relevant players only
            search_rank = player.get("search_rank")
            is_active = player.get("active", False)
            status = player.get("status", "")

            is_relevant = search_rank is not None and search_rank < 5000
            is_nfl_active = status in [
                "Active",
                "Injured Reserve",
                "PUP",
            ] and player.get("team")

            if is_relevant or (is_active and is_nfl_active):
                # Start with Sleeper data
                unified = {
                    "sleeper_id": sleeper_id,
                    "full_name": player.get("full_name"),
                    "first_name": player.get("first_name"),
                    "last_name": player.get("last_name"),
                    "position": player.get("position"),
                    "team": player.get("team"),
                    "status": player.get("status"),
                    "age": player.get("age"),
                    "search_rank": player.get("search_rank"),
                    "active": player.get("active"),
                    "height": player.get("height"),
                    "weight": player.get("weight"),
                    "college": player.get("college"),
                    "years_exp": player.get("years_exp"),
                    "depth_chart_order": player.get("depth_chart_order"),
                    "depth_chart_position": player.get("depth_chart_position"),
                }

                # Try to enrich with FFNerd data
                ffnerd_id = mapper.get_ffnerd_id(sleeper_id)
                if ffnerd_id and ffnerd_id in ffnerd_data:
                    enriched_count += 1
                    ffnerd_player = ffnerd_data[ffnerd_id]

                    # Add FFNerd specific fields
                    unified["ffnerd_id"] = ffnerd_id
                    unified["ffnerd_data"] = {
                        "jersey": ffnerd_player.get("jersey"),
                        "dob": ffnerd_player.get("dob"),
                        "injury": ffnerd_player.get("injury"),
                        "adp": ffnerd_player.get("adp"),
                        "projection_week1": ffnerd_player.get("projection_week1"),
                    }

                unified_players[sleeper_id] = unified

    print(
        f"Unified {len(unified_players)} players, enriched {enriched_count} with FFNerd data"
    )
    return unified_players


async def update_unified_cache():
    """Update the unified cache with fresh data from both APIs"""
    unified_data = await build_unified_player_data()

    try:
        r = get_redis_client()

        # Compress the unified data
        unified_json = json.dumps(unified_data)
        compressed_data = gzip.compress(unified_json.encode(), compresslevel=9)

        print(
            f"Unified cache compression: {len(unified_json) / (1024 * 1024):.2f}MB -> {len(compressed_data) / (1024 * 1024):.2f}MB"
        )

        # Store with TTL
        r.setex(UNIFIED_CACHE_KEY, CACHE_TTL, compressed_data)

        # Store metadata
        meta = {
            "last_updated": datetime.now().isoformat(),
            "total_players": len(unified_data),
            "enriched_players": sum(
                1 for p in unified_data.values() if "ffnerd_data" in p
            ),
            "compressed_size_mb": len(compressed_data) / (1024 * 1024),
            "compression": "gzip",
        }
        r.setex(UNIFIED_META_KEY, CACHE_TTL, json.dumps(meta))

        print(
            f"Unified cache updated: {meta['total_players']} players, {meta['enriched_players']} enriched, {meta['compressed_size_mb']:.2f} MB"
        )

    except RedisError as e:
        print(f"Failed to update unified cache: {e}")

    return unified_data


async def get_unified_players() -> Dict[str, Any]:
    """Get unified player data from cache or fetch fresh"""
    try:
        r = get_redis_client()

        # Try cache first
        cached_data = r.get(UNIFIED_CACHE_KEY)
        if cached_data:
            print("Using cached unified player data")
            try:
                decompressed = gzip.decompress(cached_data)
                return json.loads(decompressed)
            except gzip.BadGzipFile:
                return json.loads(cached_data)
    except (RedisError, ConnectionError) as e:
        print(f"Redis error, will fetch fresh: {e}")

    # Cache miss - fetch fresh
    print("Unified cache miss, building fresh data")
    return await update_unified_cache()


async def search_unified_players(name: str) -> List[Dict[str, Any]]:
    """
    Search unified player data by name.
    Returns enriched player data including FFNerd info when available.
    """
    players = await get_unified_players()
    results = []
    name_lower = name.lower()

    for player_id, player_data in players.items():
        full_name = player_data.get("full_name", "").lower()
        if name_lower in full_name:
            result = {
                "id": player_id,
                "name": player_data.get("full_name"),
                "position": player_data.get("position"),
                "team": player_data.get("team"),
                "status": player_data.get("status"),
                "age": player_data.get("age"),
                "search_rank": player_data.get("search_rank"),
            }

            # Include FFNerd data when available
            if "ffnerd_data" in player_data:
                result["ffnerd"] = player_data["ffnerd_data"]

            results.append(result)

    # Sort by search rank
    results.sort(key=lambda x: x.get("search_rank", 99999))
    return results[:10]


async def get_unified_player_by_id(sleeper_id: str) -> Optional[Dict[str, Any]]:
    """Get unified player data by Sleeper ID"""
    players = await get_unified_players()
    return players.get(sleeper_id)


async def get_unified_cache_status() -> Dict[str, Any]:
    """Get status of the unified cache"""
    try:
        r = get_redis_client()

        meta = r.get(UNIFIED_META_KEY)
        if meta:
            meta_data = json.loads(meta)
            ttl = r.ttl(UNIFIED_CACHE_KEY)
            meta_data["ttl_seconds"] = ttl
            meta_data["valid"] = True

            # Add Redis memory info
            try:
                info = r.info("memory")
                meta_data["redis_memory_used_mb"] = info.get("used_memory", 0) / (
                    1024 * 1024
                )
                meta_data["redis_memory_peak_mb"] = info.get("used_memory_peak", 0) / (
                    1024 * 1024
                )
            except Exception:
                pass

            return meta_data
    except (RedisError, ConnectionError) as e:
        return {"valid": False, "error": f"Redis connection error: {str(e)}"}

    return {"valid": False, "error": "Unified cache not available"}


# Example usage
async def main():
    # Test unified player search
    results = await search_unified_players("Patrick Mahomes")

    for player in results:
        print(f"\n{player['name']} - {player['position']} - {player['team']}")
        print(f"  Sleeper ID: {player['id']}")
        if "ffnerd" in player:
            print("  FFNerd Data Available: Yes")
            if player["ffnerd"].get("adp"):
                print(f"  ADP: {player['ffnerd']['adp']['avg']}")
            if player["ffnerd"].get("injury"):
                print(f"  Injury: {player['ffnerd']['injury']['status']}")


if __name__ == "__main__":
    asyncio.run(main())
