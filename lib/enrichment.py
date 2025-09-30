"""Player data enrichment utilities for MCP tools.

This module provides reusable functions for enriching player data with stats,
projections, trending information, and other contextual data. These utilities
help reduce code duplication across tools like get_roster, get_waiver_wire_players,
and get_player_stats_all_weeks.

All enrichment functions are designed to:
- Work with the cache data structure
- Handle missing/incomplete data gracefully
- Support both new and old stat locations for backward compatibility
- Return consistently structured dictionaries
"""

import logging
from typing import Any, Dict, List, Set

logger = logging.getLogger(__name__)


def enrich_player_basic(player_id: str, player_data: Dict[str, Any]) -> Dict[str, Any]:
    """Build basic player information from cache data.

    Args:
        player_id: Sleeper player ID
        player_data: Player data from cache

    Returns:
        Dict with basic player info (player_id, name, position, team, status, bye_week)
    """
    # Build basic player info
    player_info = {
        "player_id": player_id,
        "name": player_data.get("full_name", f"{player_id} (Unknown)"),
        "position": player_data.get("position"),
        "team": player_data.get("team"),
        "status": player_data.get("status"),
    }

    # Handle team defenses (player_id is 2-3 letter team code)
    if len(player_id) <= 3 and player_id.isalpha():
        player_info["name"] = f"{player_id} Defense"
        player_info["position"] = "DEF"
        player_info["team"] = player_id

    # Add bye week if available
    if "bye_week" in player_data:
        player_info["bye_week"] = player_data["bye_week"]

    return player_info


def enrich_player_stats(
    player_data: Dict[str, Any], include_position_stats: bool = True
) -> Dict[str, Any]:
    """Extract and structure stats from player data.

    Args:
        player_data: Player data from cache
        include_position_stats: Whether to include position-specific ROS stats

    Returns:
        Dict with stats structure (projected, ros_projected, actual)
    """
    player_stats: Dict[str, Any] = {
        "projected": None,
        "actual": None,
        "ros_projected": None,
    }

    if "stats" not in player_data:
        return player_stats

    cached_stats = player_data["stats"]

    # Add projected stats
    if cached_stats.get("projected"):
        proj = cached_stats["projected"]
        fantasy_points = proj.get("fantasy_points", 0)

        player_stats["projected"] = {
            "fantasy_points": round(fantasy_points, 2),
            "fantasy_points_low": round(
                proj.get("fantasy_points_low", fantasy_points), 2
            ),
            "fantasy_points_high": round(
                proj.get("fantasy_points_high", fantasy_points), 2
            ),
        }

    # Add ROS projected stats
    if cached_stats.get("ros_projected"):
        ros = cached_stats["ros_projected"]
        player_stats["ros_projected"] = {
            "fantasy_points": round(ros.get("fantasy_points", 0), 2),
            "season": ros.get("season"),
        }

        # Add position-specific ROS stats if requested
        if include_position_stats:
            position = player_data.get("position")

            if position == "QB":
                if "passing_yards" in ros:
                    player_stats["ros_projected"].update(
                        {
                            "passing_yards": round(ros.get("passing_yards", 0), 0),
                            "passing_touchdowns": round(
                                ros.get("passing_touchdowns", 0), 1
                            ),
                            "rushing_yards": round(ros.get("rushing_yards", 0), 0),
                            "rushing_touchdowns": round(
                                ros.get("rushing_touchdowns", 0), 1
                            ),
                        }
                    )
            elif position in ["RB", "WR", "TE"]:
                if any(
                    k in ros for k in ["rushing_yards", "receiving_yards", "receptions"]
                ):
                    player_stats["ros_projected"].update(
                        {
                            "rushing_yards": round(ros.get("rushing_yards", 0), 0),
                            "receiving_yards": round(ros.get("receiving_yards", 0), 0),
                            "receptions": round(ros.get("receptions", 0), 1),
                            "total_touchdowns": round(
                                ros.get("total_touchdowns", 0), 1
                            ),
                        }
                    )

    # Add actual stats if game has been played
    if cached_stats.get("actual"):
        actual = cached_stats["actual"]
        player_stats["actual"] = {
            "fantasy_points": round(actual.get("fantasy_points", 0), 2),
            "game_status": actual.get("game_status", "unknown"),
            "game_stats": actual.get("game_stats"),
        }

    return player_stats


def enrich_player_injury_news(
    player_data: Dict[str, Any], max_news: int = 3
) -> Dict[str, Any]:
    """Extract injury and news information from player data.

    Args:
        player_data: Player data from cache
        max_news: Maximum number of news items to include (default: 3)

    Returns:
        Dict with optional 'injury' and 'news' keys
    """
    enrichment: Dict[str, Any] = {}

    if "data" not in player_data:
        return enrichment

    enriched_data = player_data["data"]

    # Add injury info
    if enriched_data.get("injury"):
        injury = enriched_data["injury"]
        enrichment["injury"] = {
            "status": injury.get("game_status"),
            "description": injury.get("injury"),
            "last_update": injury.get("last_update"),
        }

    # Add news if available
    if enriched_data.get("news") and len(enriched_data["news"]) > 0:
        # Deduplicate news items by headline (issue #108)
        seen_headlines = set()
        unique_news = []
        for item in enriched_data["news"]:
            headline = item.get("headline", "")
            if headline and headline not in seen_headlines:
                seen_headlines.add(headline)
                unique_news.append(item)

        # Include latest N unique news items
        enrichment["news"] = unique_news[:max_news]

    return enrichment


def enrich_player_full(
    player_id: str,
    player_data: Dict[str, Any],
    include_position_stats: bool = True,
    max_news: int = 3,
) -> Dict[str, Any]:
    """Fully enrich a player with all available data.

    Combines basic info, stats, injury, and news into one player dictionary.

    Args:
        player_id: Sleeper player ID
        player_data: Player data from cache
        include_position_stats: Whether to include position-specific ROS stats
        max_news: Maximum number of news items to include

    Returns:
        Dict with fully enriched player data
    """
    # Start with basic info
    player_info = enrich_player_basic(player_id, player_data)

    # Add stats
    player_info["stats"] = enrich_player_stats(player_data, include_position_stats)

    # Add injury and news
    injury_news = enrich_player_injury_news(player_data, max_news)
    player_info.update(injury_news)

    return player_info


def enrich_player_minimal(
    player_id: str, player_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Create minimal player data with only essential fields.

    Used for waiver wire listings and other contexts where full data is not needed.

    Args:
        player_id: Sleeper player ID
        player_data: Player data from cache

    Returns:
        Dict with minimal player data (name, position, team, status, projected_points, bye_week)
    """
    minimal_data = {
        "player_id": player_id,
        "full_name": player_data.get("full_name"),
        "position": player_data.get("position"),
        "team": player_data.get("team"),
        "status": player_data.get("status"),
        "injury_status": player_data.get("injury_status"),
    }

    # Add bye week if available
    if "bye_week" in player_data:
        minimal_data["bye_week"] = player_data["bye_week"]

    # Add projected points if available
    # Check new location first (stats.projected.fantasy_points)
    if "stats" in player_data and player_data["stats"].get("projected"):
        try:
            fantasy_points = player_data["stats"]["projected"].get("fantasy_points")
            if fantasy_points is not None:
                minimal_data["projected_points"] = float(fantasy_points)
        except (ValueError, TypeError):
            pass
    # Fall back to old location for backward compatibility
    elif "data" in player_data and player_data["data"].get("projections"):
        try:
            proj_pts = player_data["data"]["projections"].get("proj_pts")
            if proj_pts:
                minimal_data["projected_points"] = float(proj_pts)
        except (ValueError, TypeError):
            pass

    # Add ROS projected points if available
    if "stats" in player_data and player_data["stats"].get("ros_projected"):
        try:
            ros_points = player_data["stats"]["ros_projected"].get("fantasy_points")
            if ros_points is not None:
                minimal_data["ros_projected_points"] = float(ros_points)
        except (ValueError, TypeError):
            pass

    return minimal_data


async def get_trending_data_map(
    get_trending_fn, txn_type: str = "add"
) -> Dict[str, int]:
    """Fetch trending players and return as a player_id -> count map.

    Args:
        get_trending_fn: The get_trending_players function to call
        txn_type: Transaction type ("add" or "drop")

    Returns:
        Dict mapping player_id to trending count
    """
    trending_map: Dict[str, int] = {}
    try:
        trending_response = await get_trending_fn(type=txn_type)
        trending_map = {item["player_id"]: item["count"] for item in trending_response}
    except Exception as e:
        logger.warning(
            f"Could not fetch trending data (type={txn_type}, error_type={type(e).__name__}, error_message={str(e)})"
        )

    return trending_map


async def get_recent_drops_set(
    get_recent_transactions_fn, days_back: int = 7, limit: int = 50
) -> Set[str]:
    """Fetch recently dropped players and return as a set of player_ids.

    Args:
        get_recent_transactions_fn: The get_recent_transactions function to call
        days_back: Number of days to look back
        limit: Maximum number of transactions to fetch

    Returns:
        Set of player IDs that were recently dropped
    """
    recent_drops: Set[str] = set()
    try:
        recent_txns = await get_recent_transactions_fn(
            drops_only=True,
            max_days_ago=days_back,
            include_player_details=False,
            limit=limit,
        )
        # Extract player IDs from drops
        for txn in recent_txns:
            if txn.get("drops"):
                recent_drops.update(txn["drops"].keys())
    except Exception as e:
        logger.warning(
            f"Could not fetch recent drops (days_back={days_back}, error_type={type(e).__name__}, error_message={str(e)})"
        )

    return recent_drops


def add_trending_data(
    players: List[Dict[str, Any]], trending_map: Dict[str, int]
) -> List[Dict[str, Any]]:
    """Add trending add/drop counts to player list.

    Modifies players in place by adding 'trending_add_count' field.

    Args:
        players: List of player dictionaries
        trending_map: Dict mapping player_id to trending count

    Returns:
        The same player list (modified in place)
    """
    for player in players:
        player_id = player.get("player_id")
        if player_id and player_id in trending_map:
            player["trending_add_count"] = trending_map[player_id]

    return players


def mark_recent_drops(
    players: List[Dict[str, Any]], recent_drops_set: Set[str]
) -> List[Dict[str, Any]]:
    """Mark players that were recently dropped.

    Modifies players in place by adding 'recently_dropped' field.

    Args:
        players: List of player dictionaries
        recent_drops_set: Set of player IDs that were recently dropped

    Returns:
        The same player list (modified in place)
    """
    for player in players:
        player_id = player.get("player_id")
        if player_id and player_id in recent_drops_set:
            player["recently_dropped"] = True

    return players


def organize_roster_by_position(
    players: List[Dict[str, Any]],
    starters_ids: List[str],
    taxi_ids: List[str],
    reserve_ids: List[str],
) -> Dict[str, List[Dict[str, Any]]]:
    """Organize players into roster categories (starters, bench, taxi, reserve).

    Args:
        players: List of enriched player dictionaries (must have player_id)
        starters_ids: List of player IDs in starting lineup
        taxi_ids: List of player IDs on taxi squad
        reserve_ids: List of player IDs on reserve/IR

    Returns:
        Dict with keys: starters, bench, taxi, reserve (each a list of players)
    """
    categorized: Dict[str, List[Dict[str, Any]]] = {
        "starters": [],
        "bench": [],
        "taxi": [],
        "reserve": [],
    }

    for player in players:
        player_id = player.get("player_id")
        if not player_id:
            continue

        # Categorize by roster position
        if player_id in reserve_ids:
            categorized["reserve"].append(player)
        elif player_id in taxi_ids:
            categorized["taxi"].append(player)
        elif player_id in starters_ids:
            categorized["starters"].append(player)
        else:
            categorized["bench"].append(player)

    return categorized
