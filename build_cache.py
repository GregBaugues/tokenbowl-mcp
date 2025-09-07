#!/usr/bin/env python3
"""
Fetch, enrich, and cache fantasy-relevant player data in Redis.
This replaces the existing cache with enriched Sleeper + Fantasy Nerds data.
"""

import json
import gzip
import httpx
import redis
import os
from typing import Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_redis_client() -> redis.Redis:
    """Get Redis client connection."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    return redis.from_url(redis_url, decode_responses=False)


def normalize_name(name: str) -> str:
    """Normalize player name for matching."""
    return (
        name.lower().replace(".", "").replace("'", "").replace("-", "").replace(" ", "")
    )


def fetch_sleeper_players() -> Dict[str, Any]:
    """Fetch all players from Sleeper API."""
    url = "https://api.sleeper.app/v1/players/nfl"

    print("Fetching Sleeper players...")
    with httpx.Client(timeout=30.0) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.json()


def fetch_fantasy_nerds_data() -> tuple[Dict, Dict, List]:
    """Fetch all Fantasy Nerds data (rankings, injuries, news)."""
    api_key = os.getenv("FFNERD_API_KEY")

    print("Fetching Fantasy Nerds weekly rankings...")
    with httpx.Client(timeout=30.0) as client:
        rankings_resp = client.get(
            f"https://api.fantasynerds.com/v1/nfl/weekly-rankings?format=ppr&apikey={api_key}"
        )
        rankings_resp.raise_for_status()
        rankings = rankings_resp.json()

    print("Fetching Fantasy Nerds injuries...")
    with httpx.Client(timeout=30.0) as client:
        injuries_resp = client.get(
            f"https://api.fantasynerds.com/v1/nfl/injuries?apikey={api_key}"
        )
        injuries_resp.raise_for_status()
        injuries = injuries_resp.json()

    print("Fetching Fantasy Nerds news...")
    with httpx.Client(timeout=30.0) as client:
        news_resp = client.get(
            f"https://api.fantasynerds.com/v1/nfl/news?apikey={api_key}"
        )
        news_resp.raise_for_status()
        news = news_resp.json()

    return rankings, injuries, news


def fetch_fantasy_nerds_players() -> List[Dict]:
    """Fetch Fantasy Nerds player list for ID mapping."""
    api_key = os.getenv("FFNERD_API_KEY")
    url = f"https://api.fantasynerds.com/v1/nfl/players?apikey={api_key}&include_inactive="

    print("Fetching Fantasy Nerds player list for mapping...")
    with httpx.Client(timeout=30.0) as client:
        response = client.get(url)
        response.raise_for_status()
        data = response.json()
        # Ensure we return a list even if API returns an error
        if not isinstance(data, list):
            print(
                f"Warning: Fantasy Nerds API returned non-list response: {type(data)}"
            )
            return []
        return data


def create_player_mappings(
    sleeper_players: Dict, ffnerd_players: List
) -> Dict[str, int]:
    """Create mapping from Sleeper IDs to Fantasy Nerds IDs."""
    print("Creating player ID mappings...")

    # Create lookup dictionary for Fantasy Nerds players
    ffnerd_by_name = {}
    ffnerd_by_partial = {}  # For partial name matching

    for player in ffnerd_players:
        # Skip if player is not a dict (in case of bad API response)
        if not isinstance(player, dict):
            continue
        if not player.get("name"):
            continue

        full_name = normalize_name(player["name"])
        team = player.get("team", "")
        position = player.get("position", "")

        # Store with multiple keys for better matching
        ffnerd_by_name[(full_name, team, position)] = player["playerId"]
        ffnerd_by_name[(full_name, "", position)] = player["playerId"]  # Without team
        ffnerd_by_name[(full_name, team, "")] = player["playerId"]  # Without position

        # Also store without Jr/Sr/III suffixes for better matching
        name_without_suffix = (
            full_name.replace("jr", "")
            .replace("sr", "")
            .replace("iii", "")
            .replace("ii", "")
            .strip()
        )
        if name_without_suffix != full_name:
            ffnerd_by_partial[(name_without_suffix, team, position)] = player[
                "playerId"
            ]
            ffnerd_by_partial[(name_without_suffix, "", position)] = player["playerId"]

    # Create Sleeper to Fantasy Nerds mapping
    sleeper_to_ffnerd = {}
    unmatched_players = []

    for sleeper_id, sleeper_player in sleeper_players.items():
        if not sleeper_player.get("full_name"):
            continue

        full_name = normalize_name(sleeper_player["full_name"])
        team = sleeper_player.get("team", "")
        position = sleeper_player.get("position", "")

        # Try exact match first
        key = (full_name, team, position)
        if key in ffnerd_by_name:
            sleeper_to_ffnerd[sleeper_id] = ffnerd_by_name[key]
            continue

        # Try without team
        key = (full_name, "", position)
        if key in ffnerd_by_name:
            sleeper_to_ffnerd[sleeper_id] = ffnerd_by_name[key]
            continue

        # Try without position
        key = (full_name, team, "")
        if key in ffnerd_by_name:
            sleeper_to_ffnerd[sleeper_id] = ffnerd_by_name[key]
            continue

        # Try partial name matching (without suffixes)
        name_without_suffix = (
            full_name.replace("jr", "")
            .replace("sr", "")
            .replace("iii", "")
            .replace("ii", "")
            .strip()
        )
        key = (name_without_suffix, team, position)
        if key in ffnerd_by_partial:
            sleeper_to_ffnerd[sleeper_id] = ffnerd_by_partial[key]
            continue

        # Try partial without team
        key = (name_without_suffix, "", position)
        if key in ffnerd_by_partial:
            sleeper_to_ffnerd[sleeper_id] = ffnerd_by_partial[key]
            continue

        # Special case: Try adding "jr" if name doesn't have it
        # (e.g., "Marvin Harrison" -> "Marvin Harrison Jr")
        if "jr" not in full_name and "sr" not in full_name:
            name_with_jr = full_name + "jr"
            key = (name_with_jr, team, position)
            if key in ffnerd_by_name:
                sleeper_to_ffnerd[sleeper_id] = ffnerd_by_name[key]
                continue

            # Try with Jr but without team
            key = (name_with_jr, "", position)
            if key in ffnerd_by_name:
                sleeper_to_ffnerd[sleeper_id] = ffnerd_by_name[key]
                continue

        # Track unmatched fantasy-relevant players (for debugging)
        if position in ["QB", "RB", "WR", "TE", "K"] and team:
            unmatched_players.append(
                f"{sleeper_player.get('full_name')} ({position}, {team})"
            )

    print(f"Created {len(sleeper_to_ffnerd)} player ID mappings")
    if unmatched_players and len(unmatched_players) < 20:
        print(f"Notable unmatched players: {', '.join(unmatched_players[:10])}")

    return sleeper_to_ffnerd


def organize_ffnerd_data(rankings: Dict, injuries: Dict, news: List) -> Dict[str, Dict]:
    """Organize Fantasy Nerds data by player ID."""
    ffnerd_data = {}

    # Process rankings
    if "players" in rankings:
        for position, players in rankings["players"].items():
            for ranking in players:
                player_id = str(ranking.get("playerId"))
                if player_id not in ffnerd_data:
                    ffnerd_data[player_id] = {
                        "projections": None,
                        "injury": None,
                        "news": [],
                    }

                ffnerd_data[player_id]["projections"] = {
                    "week": rankings.get("week"),
                    "season": rankings.get("season"),
                    "position": ranking.get("position"),
                    "team": ranking.get("team"),
                    "proj_pts": ranking.get("proj_pts"),
                    "proj_pts_low": ranking.get("proj_pts_low"),
                    "proj_pts_high": ranking.get("proj_pts_high"),
                }

    # Process injuries
    if "teams" in injuries:
        for team, team_injuries in injuries["teams"].items():
            for injury in team_injuries:
                player_id = str(injury.get("playerId"))
                if player_id == "0":  # Skip placeholder entries
                    continue

                if player_id not in ffnerd_data:
                    ffnerd_data[player_id] = {
                        "projections": None,
                        "injury": None,
                        "news": [],
                    }

                ffnerd_data[player_id]["injury"] = {
                    "injury": injury.get("injury"),
                    "game_status": injury.get("game_status"),
                    "last_update": injury.get("last_update"),
                    "team": injury.get("team"),
                    "position": injury.get("position"),
                }

    # Process news
    for article in news:
        player_ids = article.get("playerIds", [])
        for pid in player_ids:
            player_id = str(pid)
            if player_id not in ffnerd_data:
                ffnerd_data[player_id] = {
                    "projections": None,
                    "injury": None,
                    "news": [],
                }

            ffnerd_data[player_id]["news"].append(
                {
                    "headline": article.get("article_headline"),
                    "excerpt": article.get("article_excerpt"),
                    "date": article.get("article_date"),
                    "author": article.get("article_author"),
                    "link": article.get("article_link"),
                }
            )

    return ffnerd_data


def enrich_and_filter_players(
    sleeper_players: Dict, mapping: Dict, ffnerd_data: Dict
) -> Dict:
    """Enrich Sleeper players with Fantasy Nerds data. 
    Only includes active players on NFL teams (excludes free agents and retired players)."""
    enriched = {}
    fantasy_positions = {"QB", "RB", "WR", "TE", "K", "DEF"}

    for sleeper_id, player in sleeper_players.items():
        position = player.get("position", "")

        # Include ALL fantasy-relevant players regardless of matching
        if position not in fantasy_positions:
            continue

        # Skip only truly inactive players (not IR or Out)
        status = player.get("status", "")
        if status == "Inactive" and not player.get("injury_status"):
            continue
        
        # Skip players without a team (free agents, retired players)
        if not player.get("team"):
            continue

        # Add Fantasy Nerds data if available
        if sleeper_id in mapping:
            ffnerd_id = str(mapping[sleeper_id])
            if ffnerd_id in ffnerd_data:
                player_ffnerd_data = ffnerd_data[ffnerd_id]
                # Add the data even if it's partial
                if player_ffnerd_data:
                    player["data"] = player_ffnerd_data

        # ALWAYS include the player, even without Fantasy Nerds data
        enriched[sleeper_id] = player

    return enriched


def build_name_lookup_table(players: Dict) -> Dict[str, str]:
    """Build a lookup table from normalized player names to Sleeper IDs.

    Args:
        players: Dictionary of Sleeper player data

    Returns:
        Dictionary mapping normalized names to Sleeper IDs
    """
    name_to_id = {}

    for sleeper_id, player in players.items():
        if not player.get("full_name"):
            continue

        # Add full name
        full_name = normalize_name(player["full_name"])
        name_to_id[full_name] = sleeper_id

        # Add first + last name
        if player.get("first_name") and player.get("last_name"):
            first_last = normalize_name(f"{player['first_name']} {player['last_name']}")
            if first_last != full_name:
                name_to_id[first_last] = sleeper_id

        # Add last name only (if unique or overwriting is ok)
        if player.get("last_name"):
            last_name = normalize_name(player["last_name"])
            # Only add if not already there or this is a more prominent player
            if last_name not in name_to_id:
                name_to_id[last_name] = sleeper_id

        # Add common variations without suffixes
        name_without_suffix = (
            full_name.replace("jr", "")
            .replace("sr", "")
            .replace("iii", "")
            .replace("ii", "")
            .strip()
        )
        if name_without_suffix != full_name and name_without_suffix:
            name_to_id[name_without_suffix] = sleeper_id

    return name_to_id


def cache_players():
    """Main function to fetch, enrich, and cache player data."""

    try:
        # Get Redis client
        r = get_redis_client()

        # Fetch all data
        sleeper_players = fetch_sleeper_players()
        ffnerd_players = fetch_fantasy_nerds_players()
        rankings, injuries, news = fetch_fantasy_nerds_data()

        # Create ID mappings
        mapping = create_player_mappings(sleeper_players, ffnerd_players)

        # Organize Fantasy Nerds data
        print("Organizing Fantasy Nerds data...")
        ffnerd_data = organize_ffnerd_data(rankings, injuries, news)

        # Enrich and filter to fantasy-relevant players only
        print("Enriching and filtering players...")
        players = enrich_and_filter_players(sleeper_players, mapping, ffnerd_data)

        print(f"Total fantasy-relevant players: {len(players)}")

        # Count statistics
        has_proj = sum(
            1 for p in players.values() if p.get("data", {}).get("projections")
        )
        has_injury = sum(1 for p in players.values() if p.get("data", {}).get("injury"))
        has_news = sum(1 for p in players.values() if p.get("data", {}).get("news"))

        print(f"  - With projections: {has_proj}")
        print(f"  - With injury data: {has_injury}")
        print(f"  - With news: {has_news}")

        # Build name lookup table
        print("\nBuilding player name lookup table...")
        name_lookup = build_name_lookup_table(players)
        print(f"Created {len(name_lookup)} name mappings")

        # Compress and cache
        print("\nCaching player data to Redis...")

        # Convert to JSON and compress
        json_data = json.dumps(players)
        compressed_data = gzip.compress(json_data.encode("utf-8"))

        # Store in Redis with 6-hour TTL
        cache_key = "nfl_players_cache"
        ttl = 6 * 60 * 60  # 6 hours

        # Clear old cache keys if they exist
        old_keys = ["nfl_players_enriched", "nfl_players_unified"]
        for key in old_keys:
            if r.exists(key):
                r.delete(key)
                print(f"Deleted old cache key: {key}")

        # Set new cache
        r.set(cache_key, compressed_data, ex=ttl)

        # Cache the name lookup table
        name_lookup_key = "player_name_lookup"
        name_lookup_json = json.dumps(name_lookup)
        name_lookup_compressed = gzip.compress(name_lookup_json.encode("utf-8"))
        r.set(name_lookup_key, name_lookup_compressed, ex=ttl)
        print(
            f"Cached name lookup table ({len(name_lookup_compressed) / 1024:.1f} KB compressed)"
        )

        # Store metadata
        metadata = {
            "total_players": len(players),
            "players_with_projections": has_proj,
            "players_with_injuries": has_injury,
            "players_with_news": has_news,
            "last_updated": datetime.now().isoformat(),
            "ttl_seconds": ttl,
            "compressed_size_bytes": len(compressed_data),
            "uncompressed_size_bytes": len(json_data),
        }

        r.set(f"{cache_key}_metadata", json.dumps(metadata), ex=ttl)

        print("\nCache update complete!")
        print(f"  - Cache key: {cache_key}")
        print(f"  - Compressed size: {len(compressed_data) / 1024 / 1024:.2f} MB")
        print(f"  - Uncompressed size: {len(json_data) / 1024 / 1024:.2f} MB")
        print(
            f"  - Compression ratio: {(1 - len(compressed_data) / len(json_data)) * 100:.1f}%"
        )
        print("  - TTL: 6 hours")

        # Also save to local file for backup
        with open("fantasy_relevant_players_backup.json", "w") as f:
            json.dump(players, f, indent=2)
        print("\nBackup saved to fantasy_relevant_players_backup.json")

        return True

    except Exception as e:
        print(f"Error updating cache: {e}")
        return False


if __name__ == "__main__":
    success = cache_players()
    exit(0 if success else 1)
