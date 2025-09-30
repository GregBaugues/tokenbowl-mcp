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


def fetch_current_nfl_week() -> tuple[int, str]:
    """Fetch current NFL week and season from Sleeper state API."""
    url = "https://api.sleeper.app/v1/state/nfl"

    print("Fetching current NFL week...")
    with httpx.Client(timeout=10.0) as client:
        response = client.get(url)
        response.raise_for_status()
        state = response.json()
        return state.get("week", 1), state.get("season", "2025")


def fetch_player_stats(week: int, season: str) -> Dict[str, Any]:
    """Fetch player stats for a specific week."""
    url = f"https://api.sleeper.app/v1/stats/nfl/regular/{season}/{week}"

    print(f"Fetching player stats for week {week}, season {season}...")
    with httpx.Client(timeout=30.0) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.json()


def filter_ppr_relevant_stats(stats: Dict[str, Any]) -> Dict[str, Any]:
    """Filter stats to only include PPR points and contributing stats.
    Also transforms field names to be more descriptive."""

    # Define mapping from Sleeper API fields to our descriptive names
    field_mapping = {
        # Core PPR score
        "pts_ppr": "fantasy_points",
        # Passing stats
        "pass_yd": "passing_yards",
        "pass_td": "passing_touchdowns",
        "pass_int": "passing_interceptions",
        "pass_2pt": "passing_two_point_conversions",
        # Rushing stats
        "rush_att": "carries",  # Rushing attempts
        "rush_yd": "rushing_yards",
        "rush_td": "rushing_touchdowns",
        "rush_2pt": "rushing_two_point_conversions",
        # Receiving stats (PPR)
        "rec": "receptions",
        "rec_tgt": "targets",
        "rec_yd": "receiving_yards",
        "rec_td": "receiving_touchdowns",
        "rec_2pt": "receiving_two_point_conversions",
        # Fumbles
        "fum_lost": "fumbles_lost",
        # Kicking stats
        "fgm": "field_goals_made",
        "fgm_0_19": "field_goals_made_0_19",
        "fgm_20_29": "field_goals_made_20_29",
        "fgm_30_39": "field_goals_made_30_39",
        "fgm_40_49": "field_goals_made_40_49",
        "fgm_50p": "field_goals_made_50_plus",
        "fgmiss": "field_goals_missed",
        "xpm": "extra_points_made",
        "xpmiss": "extra_points_missed",
        # Defensive stats (for IDP if used)
        "def_td": "defensive_touchdowns",
        "def_int": "defensive_interceptions",
        "def_sack": "defensive_sacks",
        "def_ff": "defensive_forced_fumbles",
        "def_fr": "defensive_fumble_recoveries",
        # Bonus stats that might affect scoring
        "bonus_pass_yd_300": "bonus_passing_300_yards",
        "bonus_pass_yd_400": "bonus_passing_400_yards",
        "bonus_rush_yd_100": "bonus_rushing_100_yards",
        "bonus_rush_yd_200": "bonus_rushing_200_yards",
        "bonus_rec_yd_100": "bonus_receiving_100_yards",
        "bonus_rec_yd_200": "bonus_receiving_200_yards",
    }

    # Filter and transform the stats
    filtered = {}
    for player_id, player_stats in stats.items():
        if isinstance(player_stats, dict):
            # Transform field names and filter to relevant stats
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
            # Handle case where stats might not be a dict
            filtered[player_id] = player_stats

    return filtered


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


def fetch_fantasy_nerds_ros() -> Dict:
    """Fetch Rest of Season (ROS) projections from Fantasy Nerds."""
    api_key = os.getenv("FFNERD_API_KEY")

    print("Fetching Fantasy Nerds ROS projections...")
    with httpx.Client(timeout=30.0) as client:
        ros_resp = client.get(
            f"https://api.fantasynerds.com/v1/nfl/ros?apikey={api_key}"
        )
        ros_resp.raise_for_status()
        return ros_resp.json()


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
        position = sleeper_player.get("position", "")
        team = sleeper_player.get("team", "")

        # Special handling for defenses which have null full_name
        if position == "DEF":
            # Construct defense name from first_name and last_name
            first_name = sleeper_player.get("first_name", "")
            last_name = sleeper_player.get("last_name", "")
            if first_name and last_name:
                full_name = normalize_name(f"{first_name} {last_name}")
            else:
                continue
        else:
            # Regular player handling
            if not sleeper_player.get("full_name"):
                continue
            full_name = normalize_name(sleeper_player["full_name"])

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
        if position in ["QB", "RB", "WR", "TE", "K", "DEF"] and team:
            player_name = sleeper_player.get("full_name")
            if position == "DEF" and not player_name:
                # For defenses, construct the name
                first_name = sleeper_player.get("first_name", "")
                last_name = sleeper_player.get("last_name", "")
                player_name = f"{first_name} {last_name}"
            if player_name:
                unmatched_players.append(f"{player_name} ({position}, {team})")

    print(f"Created {len(sleeper_to_ffnerd)} player ID mappings")
    if unmatched_players and len(unmatched_players) < 20:
        print(f"Notable unmatched players: {', '.join(unmatched_players[:10])}")

    return sleeper_to_ffnerd


def organize_ffnerd_data(
    rankings: Dict, injuries: Dict, news: List, ros: Dict
) -> Dict[str, Dict]:
    """Organize Fantasy Nerds data by player ID."""
    ffnerd_data = {}

    # Process rankings
    if "players" in rankings:
        # Handle both dict (old format) and list (new format) structures
        if isinstance(rankings["players"], list):
            # New format: just a flat list of players
            for ranking in rankings["players"]:
                player_id = str(ranking.get("playerId"))
                if player_id not in ffnerd_data:
                    ffnerd_data[player_id] = {
                        "projections": None,
                        "ros_projections": None,
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
        else:
            # Old format: dict keyed by position
            for position, players in rankings["players"].items():
                for ranking in players:
                    player_id = str(ranking.get("playerId"))
                    if player_id not in ffnerd_data:
                        ffnerd_data[player_id] = {
                            "projections": None,
                            "ros_projections": None,
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

    # Process ROS projections
    if "projections" in ros:
        # Check if ros["projections"] is actually a dict
        if not isinstance(ros["projections"], dict):
            print(f"Warning: ros['projections'] is {type(ros['projections'])}, expected dict. Skipping ROS processing.")
        else:
            for position, players in ros["projections"].items():
                if not isinstance(players, list):
                    print(f"Warning: Expected list for ROS position {position}, got {type(players)}. Skipping.")
                    continue
                for player in players:
                    player_id = str(player.get("playerId"))
                    if player_id not in ffnerd_data:
                        ffnerd_data[player_id] = {
                            "projections": None,
                            "ros_projections": None,
                            "injury": None,
                            "news": [],
                        }

                    # Build ROS projection data based on position
                    ros_data = {
                        "season": ros.get("season"),
                        "position": player.get("position"),
                        "team": player.get("team"),
                        "proj_pts": player.get("proj_pts"),
                    }

                    # Add position-specific stats
                    if position == "QB":
                        ros_data.update(
                            {
                                "passing_attempts": player.get("passing_attempts"),
                                "passing_completions": player.get("passing_completions"),
                                "passing_yards": player.get("passing_yards"),
                                "passing_touchdowns": player.get("passing_touchdowns"),
                                "passing_interceptions": player.get(
                                    "passing_interceptions"
                                ),
                                "rushing_attempts": player.get("rushing_attempts"),
                                "rushing_yards": player.get("rushing_yards"),
                                "rushing_touchdowns": player.get("rushing_touchdowns"),
                            }
                        )
                    elif position in ["RB", "WR", "TE"]:
                        ros_data.update(
                            {
                                "rushing_attempts": player.get("rushing_attempts"),
                                "rushing_yards": player.get("rushing_yards"),
                                "rushing_touchdowns": player.get("rushing_touchdowns"),
                                "receptions": player.get("receptions"),
                                "receiving_yards": player.get("receiving_yards"),
                                "receiving_touchdowns": player.get("receiving_touchdowns"),
                                "targets": player.get("targets"),
                                "fumbles": player.get("fumbles"),
                            }
                        )

                    ffnerd_data[player_id]["ros_projections"] = ros_data

    # Process injuries
    if "teams" in injuries:
        # Handle both dict (old format) and list (new format) structures
        if not isinstance(injuries["teams"], dict):
            # New API format returns a list, skip for now as we need to refactor this
            pass
        else:
            for team, team_injuries in injuries["teams"].items():
                for injury in team_injuries:
                    player_id = str(injury.get("playerId"))
                    if player_id == "0":  # Skip placeholder entries
                        continue

                    if player_id not in ffnerd_data:
                        ffnerd_data[player_id] = {
                            "projections": None,
                            "ros_projections": None,
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
    sleeper_players: Dict, mapping: Dict, ffnerd_data: Dict, stats_data: Dict
) -> Dict:
    """Enrich Sleeper players with Fantasy Nerds data and current week stats.
    Only includes active players on NFL teams (excludes free agents and retired players).
    Creates a consistent stats structure with both projected and actual data.
    Filters to only include specified fields to reduce context size."""
    enriched = {}
    fantasy_positions = {"QB", "RB", "WR", "TE", "K", "DEF"}

    # Define the fields to keep
    fields_to_keep = {
        "team",
        "practice_description",
        "search_first_name",
        "active",
        "injury_start_date",
        "first_name",
        "player_id",
        "status",
        "news_updated",
        "team_changed_at",
        "last_name",
        "search_full_name",
        "search_last_name",
        "full_name",
        "depth_chart_order",
        "injury_status",
        "depth_chart_position",
        "age",
        "injury_body_part",
        "team_abbr",
        "position",
        "injury_notes",
        "fantasy_positions",
        "hashtag",
        "count",
    }

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

        # Build filtered player object with only specified fields
        filtered_player = {}
        for field in fields_to_keep:
            if field in player:
                filtered_player[field] = player[field]

        # Synthesize full_name for defenses if it's null
        if position == "DEF" and not filtered_player.get("full_name"):
            first_name = player.get("first_name", "")
            last_name = player.get("last_name", "")
            if first_name and last_name:
                filtered_player["full_name"] = f"{first_name} {last_name}"

        # Create the new stats structure
        filtered_player["stats"] = {"projected": None, "actual": None}

        # Add Fantasy Nerds projections data
        if sleeper_id in mapping:
            ffnerd_id = str(mapping[sleeper_id])
            if ffnerd_id in ffnerd_data:
                player_ffnerd_data = ffnerd_data[ffnerd_id]

                # Add projections to the new stats structure
                if player_ffnerd_data and player_ffnerd_data.get("projections"):
                    proj = player_ffnerd_data["projections"]
                    try:
                        # Convert string values to floats
                        fantasy_points = float(proj.get("proj_pts", 0))
                        fantasy_points_low = float(
                            proj.get("proj_pts_low", fantasy_points)
                        )
                        fantasy_points_high = float(
                            proj.get("proj_pts_high", fantasy_points)
                        )

                        filtered_player["stats"]["projected"] = {
                            "fantasy_points": fantasy_points,
                            "fantasy_points_low": fantasy_points_low,
                            "fantasy_points_high": fantasy_points_high,
                        }
                    except (ValueError, TypeError):
                        pass

                # Add ROS projections to the stats structure
                if player_ffnerd_data and player_ffnerd_data.get("ros_projections"):
                    ros = player_ffnerd_data["ros_projections"]
                    try:
                        # Convert string values to floats
                        ros_fantasy_points = float(ros.get("proj_pts", 0))

                        filtered_player["stats"]["ros_projected"] = {
                            "fantasy_points": ros_fantasy_points,
                            "season": ros.get("season"),
                        }

                        # Add position-specific ROS stats
                        if position == "QB":
                            filtered_player["stats"]["ros_projected"].update(
                                {
                                    "passing_yards": float(ros.get("passing_yards", 0)),
                                    "passing_touchdowns": float(
                                        ros.get("passing_touchdowns", 0)
                                    ),
                                    "rushing_yards": float(ros.get("rushing_yards", 0)),
                                    "rushing_touchdowns": float(
                                        ros.get("rushing_touchdowns", 0)
                                    ),
                                }
                            )
                        elif position in ["RB", "WR", "TE"]:
                            filtered_player["stats"]["ros_projected"].update(
                                {
                                    "rushing_yards": float(ros.get("rushing_yards", 0)),
                                    "receiving_yards": float(
                                        ros.get("receiving_yards", 0)
                                    ),
                                    "receptions": float(ros.get("receptions", 0)),
                                    "total_touchdowns": float(
                                        ros.get("rushing_touchdowns", 0)
                                    )
                                    + float(ros.get("receiving_touchdowns", 0)),
                                }
                            )
                    except (ValueError, TypeError):
                        pass

                # Keep other FFNerd data (injury, news) in the old location for now
                # This maintains backward compatibility
                if player_ffnerd_data:
                    filtered_player["data"] = {
                        "injury": player_ffnerd_data.get("injury"),
                        "news": player_ffnerd_data.get("news"),
                    }

        # Add current week actual stats if available
        if sleeper_id in stats_data:
            player_stats = stats_data[sleeper_id]

            # Extract fantasy points from the transformed stats
            fantasy_points = player_stats.get("fantasy_points")

            # Separate game stats from fantasy points
            game_stats = {
                k: v for k, v in player_stats.items() if k != "fantasy_points"
            }

            # Determine game status (for now, assume "final" if stats exist)
            # TODO: Could enhance this by checking game schedule
            game_status = "final" if fantasy_points else "not_started"

            filtered_player["stats"]["actual"] = {
                "fantasy_points": fantasy_points,
                "game_stats": game_stats if game_stats else None,
                "game_status": game_status,
            }

        # ALWAYS include the player, even without Fantasy Nerds data
        enriched[sleeper_id] = filtered_player

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
        position = player.get("position", "")

        # Handle defenses specially (they have null full_name)
        if position == "DEF":
            first_name = player.get("first_name", "")
            last_name = player.get("last_name", "")
            team = player.get("team", "")

            if first_name and last_name:
                # Add full defense name
                full_name = normalize_name(f"{first_name} {last_name}")
                name_to_id[full_name] = sleeper_id

                # Also add just the team nickname for easier searching
                name_to_id[normalize_name(last_name)] = sleeper_id

                # Add team abbreviation as well
                if team:
                    name_to_id[normalize_name(team)] = sleeper_id
        else:
            # Regular player handling
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
        ros = fetch_fantasy_nerds_ros()  # Fetch ROS projections

        # Get current NFL week and fetch stats
        current_week, season = fetch_current_nfl_week()
        raw_stats = fetch_player_stats(current_week, season)

        # Filter to only PPR-relevant stats
        stats_data = filter_ppr_relevant_stats(raw_stats)
        print(f"Filtered to {len(stats_data)} players with PPR-relevant stats")

        # Create ID mappings
        mapping = create_player_mappings(sleeper_players, ffnerd_players)

        # Organize Fantasy Nerds data (now including ROS)
        print("Organizing Fantasy Nerds data...")
        ffnerd_data = organize_ffnerd_data(rankings, injuries, news, ros)

        # Enrich and filter to fantasy-relevant players only
        print("Enriching and filtering players...")
        players = enrich_and_filter_players(
            sleeper_players, mapping, ffnerd_data, stats_data
        )

        print(f"Total fantasy-relevant players: {len(players)}")

        # Count statistics with new structure
        has_proj = sum(
            1 for p in players.values() if p.get("stats", {}).get("projected")
        )
        has_ros = sum(
            1 for p in players.values() if p.get("stats", {}).get("ros_projected")
        )
        has_injury = sum(1 for p in players.values() if p.get("data", {}).get("injury"))
        has_news = sum(1 for p in players.values() if p.get("data", {}).get("news"))
        has_stats = sum(1 for p in players.values() if p.get("stats", {}).get("actual"))

        print(f"  - With weekly projections: {has_proj}")
        print(f"  - With ROS projections: {has_ros}")
        print(f"  - With injury data: {has_injury}")
        print(f"  - With news: {has_news}")
        print(f"  - With current week stats: {has_stats}")

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
            "players_with_ros_projections": has_ros,
            "players_with_injuries": has_injury,
            "players_with_news": has_news,
            "players_with_stats": has_stats,
            "current_week": current_week,
            "season": season,
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
