#!/usr/bin/env python3
"""Test that stats are properly integrated into player data."""

from cache_client import search_players, get_player_by_id, get_cache_status


def test_cache_status():
    """Test that cache status shows stats info."""
    status = get_cache_status()
    print("Cache Status:")
    print(f"  - Total players: {status.get('total_players')}")
    print(f"  - With projections: {status.get('players_with_projections')}")
    print(f"  - With stats: {status.get('players_with_stats')}")
    print(f"  - Current week: {status.get('current_week')}")
    print(f"  - Season: {status.get('season')}")
    print()


def test_player_search():
    """Test that player search includes stats."""
    print("Testing player search for 'mahomes':")
    results = search_players("mahomes", limit=1)
    if results:
        player = results[0]
        print(f"  - Player: {player.get('full_name')}")
        print(f"  - Team: {player.get('team')}")
        print(f"  - Position: {player.get('position')}")

        if player.get("stats", {}).get("actual"):
            actual = player["stats"]["actual"]
            print("  - Has actual stats: YES")
            print(f"    - Game status: {actual.get('game_status')}")
            print(f"    - Fantasy points: {actual.get('fantasy_points')}")
            if actual.get("game_stats"):
                game_stats = actual["game_stats"]
                print(f"    - Passing yards: {game_stats.get('passing_yards')}")
                print(f"    - Passing TDs: {game_stats.get('passing_touchdowns')}")
        else:
            print("  - Has actual stats: NO")

        if player.get("stats", {}).get("projected"):
            proj = player["stats"]["projected"]
            print("  - Has projections: YES")
            print(f"    - Projected points: {proj.get('fantasy_points')}")
    print()


def test_player_by_id():
    """Test that get_player_by_id includes stats."""
    print("Testing get_player_by_id for '4046' (Patrick Mahomes):")
    player = get_player_by_id("4046")
    if player:
        print(f"  - Player: {player.get('full_name')}")

        if player.get("stats", {}).get("actual"):
            actual = player["stats"]["actual"]
            print("  - Has actual stats: YES")
            print(f"    - Game status: {actual.get('game_status')}")
            print(f"    - Fantasy points: {actual.get('fantasy_points')}")
        else:
            print("  - Has actual stats: NO")

        if player.get("stats", {}).get("projected"):
            proj = player["stats"]["projected"]
            print("  - Has projections: YES")
            print(f"    - Projected points: {proj.get('fantasy_points')}")
    print()


def test_player_without_stats():
    """Test a player who hasn't played yet."""
    print("Testing player without stats (search for a backup QB):")
    results = search_players("trubisky", limit=1)
    if results:
        player = results[0]
        print(f"  - Player: {player.get('full_name')}")
        print(f"  - Team: {player.get('team')}")
        print(
            f"  - Has actual stats: {'YES' if player.get('stats', {}).get('actual') else 'NO'}"
        )
        print(
            f"  - Has projections: {'YES' if player.get('stats', {}).get('projected') else 'NO'}"
        )
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Stats Integration in Cached Player Data")
    print("=" * 60)
    print()

    test_cache_status()
    test_player_search()
    test_player_by_id()
    test_player_without_stats()

    print("=" * 60)
    print("Test Complete!")
    print("=" * 60)
