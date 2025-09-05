#!/usr/bin/env python3
"""Manual test script for Fantasy Nerds player enrichment."""

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ffnerd.enricher import PlayerEnricher
from ffnerd.mapper import PlayerMapper
from ffnerd.cache import FantasyNerdsCache
from players_cache_redis import get_all_players


async def test_single_player_enrichment():
    """Test enriching a single player."""
    print("\n" + "=" * 60)
    print("Testing Single Player Enrichment")
    print("=" * 60)

    # Sample Sleeper player data
    sample_player = {
        "player_id": "4046",
        "full_name": "Patrick Mahomes",
        "first_name": "Patrick",
        "last_name": "Mahomes",
        "team": "KC",
        "position": "QB",
        "age": 28,
        "status": "Active",
        "injury_status": None,
        "years_exp": 7,
        "college": "Texas Tech",
    }

    # Initialize components
    mapper = PlayerMapper()
    cache = FantasyNerdsCache()
    enricher = PlayerEnricher(mapper=mapper, cache=cache)

    print("\nOriginal player data:")
    print(json.dumps(sample_player, indent=2))

    # Enrich the player
    enriched = await enricher.enrich_player(sample_player)

    if "ffnerd_data" in enriched:
        print("\n✅ Player successfully enriched!")
        print(f"Confidence score: {enriched['ffnerd_data'].get('confidence', 0):.3f}")
        print("\nEnriched data:")
        print(json.dumps(enriched["ffnerd_data"], indent=2, default=str))
    else:
        print("\n❌ Player could not be enriched (no mapping or cache data)")

    return enriched


async def test_bulk_enrichment(limit: int = 10):
    """Test enriching multiple players from the cache."""
    print("\n" + "=" * 60)
    print(f"Testing Bulk Enrichment (First {limit} Players)")
    print("=" * 60)

    # Get players from Sleeper cache
    print("\nFetching players from Sleeper cache...")
    try:
        all_players = await get_all_players()

        # Take first N players for testing
        test_players = dict(list(all_players.items())[:limit])
        print(f"✅ Fetched {len(test_players)} players for testing")

    except Exception as e:
        print(f"❌ Error fetching players from cache: {e}")
        print("Using sample players instead...")

        # Fallback sample data
        test_players = {
            "4046": {
                "player_id": "4046",
                "full_name": "Patrick Mahomes",
                "position": "QB",
                "team": "KC",
            },
            "6786": {
                "player_id": "6786",
                "full_name": "Jonathan Taylor",
                "position": "RB",
                "team": "IND",
            },
            "4984": {
                "player_id": "4984",
                "full_name": "Calvin Ridley",
                "position": "WR",
                "team": "TEN",
            },
            "6744": {
                "player_id": "6744",
                "full_name": "Travis Kelce",
                "position": "TE",
                "team": "KC",
            },
            "5859": {
                "player_id": "5859",
                "full_name": "Lamar Jackson",
                "position": "QB",
                "team": "BAL",
            },
        }

    # Initialize enricher
    mapper = PlayerMapper()
    cache = FantasyNerdsCache()
    enricher = PlayerEnricher(mapper=mapper, cache=cache)

    # Enrich players
    print("\nEnriching players...")
    enriched_players = await enricher.enrich_players(test_players)

    # Analyze results
    enriched_count = sum(1 for p in enriched_players.values() if "ffnerd_data" in p)

    print("\n📊 Enrichment Results:")
    print(f"  Total players: {len(test_players)}")
    print(f"  Successfully enriched: {enriched_count}")
    print(f"  Not enriched: {len(test_players) - enriched_count}")

    # Show metrics
    metrics = enricher.get_metrics()
    print("\n📈 Performance Metrics:")
    print(f"  Success rate: {metrics['success_rate']}%")
    print(f"  Average confidence: {metrics['average_confidence']:.3f}")
    print(f"  Average time: {metrics['average_time_ms']:.2f}ms")
    print(f"  Cache hit rate: {metrics['cache_hit_rate']}%")
    print(f"  Total elapsed: {metrics.get('elapsed_time_seconds', 0):.3f}s")

    # Show sample enriched player
    for player_id, player in enriched_players.items():
        if "ffnerd_data" in player:
            print(f"\n📋 Sample Enriched Player: {player['full_name']}")
            ffnerd = player["ffnerd_data"]

            if "projections" in ffnerd and ffnerd["projections"]:
                print(
                    f"  Projections: {ffnerd['projections'].get('points', 'N/A')} pts"
                )

            if "injury" in ffnerd and ffnerd["injury"]:
                print(f"  Injury Status: {ffnerd['injury'].get('status', 'N/A')}")

            if "rankings" in ffnerd and ffnerd["rankings"]:
                print(
                    f"  Rankings: Overall #{ffnerd['rankings'].get('overall', 'N/A')}"
                )

            if "news" in ffnerd and ffnerd["news"]:
                print(f"  News Items: {len(ffnerd['news'])}")

            print(f"  Confidence: {ffnerd.get('confidence', 0):.3f}")
            break

    return enriched_players


async def test_performance(player_count: int = 1000):
    """Test enrichment performance with many players."""
    print("\n" + "=" * 60)
    print(f"Testing Performance ({player_count} Players)")
    print("=" * 60)

    # Create test players
    test_players = {
        str(i): {
            "player_id": str(i),
            "full_name": f"Test Player {i}",
            "position": ["QB", "RB", "WR", "TE"][i % 4],
            "team": ["KC", "BUF", "MIA", "CIN"][i % 4],
        }
        for i in range(player_count)
    }

    # Initialize enricher
    mapper = PlayerMapper()
    cache = FantasyNerdsCache()
    enricher = PlayerEnricher(mapper=mapper, cache=cache)

    print(f"\nEnriching {player_count} players...")

    # Time the enrichment
    import time

    start_time = time.time()
    enriched_players = await enricher.enrich_players(test_players, max_concurrent=50)
    elapsed = time.time() - start_time

    # Check performance requirement
    print("\n⏱️  Performance Results:")
    print(f"  Players processed: {len(enriched_players)}")
    print(f"  Time elapsed: {elapsed:.3f}s")
    print(f"  Players per second: {len(enriched_players) / elapsed:.0f}")

    if elapsed < 1.0:
        print(f"  ✅ PASSED: Processed {player_count} players in under 1 second!")
    else:
        print(f"  ⚠️  WARNING: Took {elapsed:.3f}s (target: < 1 second)")

    return elapsed


async def test_confidence_scoring():
    """Test confidence scoring with different data scenarios."""
    print("\n" + "=" * 60)
    print("Testing Confidence Scoring")
    print("=" * 60)

    enricher = PlayerEnricher()

    test_cases = [
        ("No data", {}, None),
        (
            "Full data",
            {"position": "QB"},
            {
                "projections": {"points": 25},
                "injury": {"status": "Healthy"},
                "news": [{"headline": "News"}],
                "rankings": {"overall": 1},
                "ffnerd_id": 123,
            },
        ),
        (
            "Partial data",
            {"position": "RB"},
            {"projections": {"points": 15}, "rankings": {"overall": 10}},
        ),
        ("Only projections", {"position": "WR"}, {"projections": {"points": 12}}),
        ("Kicker with limited data", {"position": "K"}, {"projections": {"points": 8}}),
    ]

    print("\nConfidence scores for different scenarios:")
    for name, player_data, ffnerd_data in test_cases:
        confidence = enricher.calculate_confidence(player_data, ffnerd_data)
        status = "✅" if confidence > 0.5 else "⚠️" if confidence > 0 else "❌"
        print(f"  {status} {name:20s}: {confidence:.3f}")


async def test_cache_integration():
    """Test integration with Redis cache."""
    print("\n" + "=" * 60)
    print("Testing Cache Integration")
    print("=" * 60)

    cache = FantasyNerdsCache()

    print("\nChecking Redis connection...")
    try:
        client = cache.get_redis_client()
        client.ping()
        print("✅ Redis connection successful")

        # Check cache status
        status = await cache.get_cache_status()
        print("\n📊 Cache Status:")
        print(f"  Hits: {status['hits']}")
        print(f"  Misses: {status['misses']}")
        print(f"  Hit rate: {status['hit_rate']:.1f}%")
        print(f"  Keys cached: {status['total_keys']}")
        print(f"  Memory used: {status['memory_used_mb']:.2f} MB")

    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("Make sure Redis is running (redis-server or Docker)")
        return False

    return True


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print(" Fantasy Nerds Enrichment Test Suite")
    print("=" * 60)
    print(f" Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Check environment
    api_key = os.getenv("FFNERD_API_KEY")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

    print("\n🔧 Configuration:")
    print(f"  FFNERD_API_KEY: {'✅ Set' if api_key else '❌ Not set'}")
    print(f"  REDIS_URL: {redis_url}")

    if not api_key:
        print("\n⚠️  Warning: FFNERD_API_KEY not set in environment")
        print("  Enrichment will only work with cached data")

    # Run tests
    tests = [
        ("Cache Integration", test_cache_integration),
        ("Single Player", test_single_player_enrichment),
        ("Bulk Enrichment", lambda: test_bulk_enrichment(25)),
        ("Confidence Scoring", test_confidence_scoring),
        ("Performance Test", lambda: test_performance(1000)),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            print(f"\n🔄 Running: {test_name}")
            result = await test_func()
            results[test_name] = "✅ Passed"
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            results[test_name] = f"❌ Failed: {str(e)[:50]}"

    # Summary
    print("\n" + "=" * 60)
    print(" Test Summary")
    print("=" * 60)
    for test_name, result in results.items():
        print(f"  {result} {test_name}")

    passed = sum(1 for r in results.values() if "✅" in r)
    total = len(results)

    print(f"\n  Total: {passed}/{total} tests passed")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
