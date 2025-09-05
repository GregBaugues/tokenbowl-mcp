"""Manual testing script for Fantasy Nerds Redis cache."""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ffnerd.cache import FantasyNerdsCache
from ffnerd.client import FantasyNerdsClient


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f" {title}")
    print("=" * 60)


def print_status(success: bool, message: str):
    """Print a status message with emoji."""
    emoji = "✅" if success else "❌"
    print(f"{emoji} {message}")


async def test_basic_cache_operations():
    """Test basic cache storage and retrieval."""
    print_section("Testing Basic Cache Operations")

    cache = FantasyNerdsCache()

    # Test mapping storage
    test_mapping = {
        "12345": 6789,
        "67890": 1234,
        "11111": 2222,
    }

    print("\n1. Testing player ID mapping cache:")
    success = cache.store_mapping(test_mapping)
    print_status(success, f"Stored mapping with {len(test_mapping)} entries")

    retrieved = cache.get_mapping()
    if retrieved:
        print_status(retrieved == test_mapping, "Retrieved mapping matches original")
    else:
        print_status(False, "Failed to retrieve mapping")

    # Test projections
    print("\n2. Testing projections cache:")
    test_projections = [
        {"player_id": 1, "name": "Player 1", "points": 20.5, "yards": 300},
        {"player_id": 2, "name": "Player 2", "points": 15.3, "yards": 250},
    ]

    success = cache.store_projections(week=1, data=test_projections, scoring="PPR")
    print_status(
        success, f"Stored week 1 PPR projections ({len(test_projections)} players)"
    )

    retrieved = cache.get_projections(week=1, scoring="PPR")
    if retrieved:
        print_status(len(retrieved) == 2, f"Retrieved {len(retrieved)} projections")
    else:
        print_status(False, "Failed to retrieve projections")

    # Test injuries
    print("\n3. Testing injuries cache:")
    test_injuries = [
        {
            "player": "Player A",
            "team": "Team 1",
            "status": "Questionable",
            "injury": "Hamstring",
        },
        {"player": "Player B", "team": "Team 2", "status": "Out", "injury": "Ankle"},
    ]

    success = cache.store_injuries(test_injuries)
    print_status(success, f"Stored {len(test_injuries)} injury reports")

    retrieved = cache.get_injuries()
    if retrieved:
        print_status(len(retrieved) == 2, f"Retrieved {len(retrieved)} injuries")
    else:
        print_status(False, "Failed to retrieve injuries")

    # Test news
    print("\n4. Testing news cache:")
    test_news = [
        {
            "title": "Breaking News",
            "content": "Important update about Player X",
            "date": "2024-01-01",
        },
        {
            "title": "Trade Alert",
            "content": "Player Y traded to new team",
            "date": "2024-01-02",
        },
    ]

    success = cache.store_news(test_news)
    print_status(success, f"Stored {len(test_news)} news articles")

    retrieved = cache.get_news()
    if retrieved:
        print_status(len(retrieved) == 2, f"Retrieved {len(retrieved)} news articles")
    else:
        print_status(False, "Failed to retrieve news")

    # Test player enrichment
    print("\n5. Testing player enrichment cache:")
    test_enrichment = {
        "projections": {"week_1": 20.5, "week_2": 22.3},
        "injury": {"status": "Healthy"},
        "news": [{"title": "Player performing well in practice"}],
        "rankings": {"overall": 10, "position": 3},
    }

    sleeper_id = "test_player_123"
    success = cache.store_player_enrichment(sleeper_id, test_enrichment)
    print_status(success, f"Stored enrichment data for player {sleeper_id}")

    retrieved = cache.get_player_enrichment(sleeper_id)
    if retrieved:
        print_status("cached_at" in retrieved, "Enrichment includes timestamp")
        print_status("projections" in retrieved, "Enrichment includes projections")
    else:
        print_status(False, "Failed to retrieve enrichment")


async def test_compression_effectiveness():
    """Test data compression effectiveness."""
    print_section("Testing Compression Effectiveness")

    cache = FantasyNerdsCache()

    # Create a large dataset
    large_data = {str(i): i * 100 for i in range(1000)}

    # Test compression
    original_json = json.dumps(large_data)
    original_size = len(original_json)
    compressed = cache._compress_data(large_data)
    compressed_size = len(compressed)

    compression_ratio = (1 - compressed_size / original_size) * 100

    print(f"\nOriginal size: {original_size:,} bytes")
    print(f"Compressed size: {compressed_size:,} bytes")
    print(f"Compression ratio: {compression_ratio:.1f}%")
    print_status(compression_ratio > 50, "Achieved >50% compression")

    # Test decompression
    decompressed = cache._decompress_data(compressed)
    print_status(
        decompressed == large_data, "Data integrity maintained after compression"
    )


async def test_cache_management():
    """Test cache management features."""
    print_section("Testing Cache Management")

    cache = FantasyNerdsCache()

    # Get cache status
    print("\n1. Cache Status:")
    status = cache.get_cache_status()

    if status.get("healthy"):
        print_status(True, "Cache is healthy")
        print(f"   Total keys: {status.get('total_keys', 0)}")
        print(f"   Memory used: {status.get('redis_memory_used_mb', 0):.2f} MB")
        print(f"   Hit rate: {status.get('stats', {}).get('hit_rate_pct', 0):.1f}%")

        print("\n   Key breakdown:")
        for category, count in status.get("key_categories", {}).items():
            if count > 0:
                print(f"     - {category}: {count}")
    else:
        print_status(False, f"Cache unhealthy: {status.get('error', 'Unknown error')}")

    # Test TTL
    print("\n2. Testing TTL (Time To Live):")

    # Store some test data
    cache.store_projections(week=99, data={"test": "ttl"}, scoring="TEST")

    ttl = cache.get_ttl("projections", week=99, scoring="TEST")
    if ttl:
        hours = ttl / 3600
        print_status(True, f"Projections TTL: {ttl} seconds ({hours:.1f} hours)")
    else:
        print_status(False, "Could not get TTL")

    # Test cache invalidation
    print("\n3. Testing cache invalidation:")

    # Add some test keys
    cache.store_projections(week=98, data={"test": 1}, scoring="TEST1")
    cache.store_projections(week=97, data={"test": 2}, scoring="TEST2")

    # Invalidate projections
    deleted = cache.invalidate_cache("projections:*")
    print_status(deleted >= 0, f"Invalidated {deleted} projection keys")


async def test_with_real_api():
    """Test cache with real Fantasy Nerds API (requires API key)."""
    print_section("Testing with Real API (if available)")

    api_key = os.getenv("FFNERD_API_KEY")
    if not api_key:
        print_status(False, "FFNERD_API_KEY not set - skipping API tests")
        return

    try:
        client = FantasyNerdsClient(api_key)
        cache = FantasyNerdsCache()

        # Test connection
        print("\n1. Testing API connection:")
        connected = await client.test_connection()
        print_status(connected, "Successfully connected to Fantasy Nerds API")

        if not connected:
            return

        # Fetch and cache real data
        print("\n2. Fetching and caching real data:")

        # Get players
        print("   Fetching players...")
        players = await client.get_players(include_inactive=False)
        if players:
            # Create a simple mapping (just for testing)
            test_mapping = {
                str(i): p.get("playerId") for i, p in enumerate(players[:10])
            }
            success = cache.store_mapping(test_mapping)
            print_status(success, f"Cached mapping for {len(test_mapping)} players")

        # Get and cache projections
        print("   Fetching projections...")
        projections = await client.get_weekly_projections(week=1)
        if projections:
            success = cache.store_projections(week=1, data=projections)
            print_status(success, "Cached week 1 projections")

        # Get and cache injuries
        print("   Fetching injuries...")
        injuries = await client.get_injuries()
        if injuries:
            success = cache.store_injuries(injuries)
            print_status(success, f"Cached {len(injuries)} injury reports")

        # Get and cache news
        print("   Fetching news...")
        news = await client.get_news(days=1)
        if news:
            success = cache.store_news(news)
            print_status(success, f"Cached {len(news)} news articles")

        # Display final cache status
        print("\n3. Final cache status:")
        status = cache.get_cache_status()
        print(f"   Total cached keys: {status.get('total_keys', 0)}")
        print(f"   Total size: {status.get('total_size_mb', 0):.2f} MB")

    except Exception as e:
        print_status(False, f"Error testing with API: {e}")


async def main():
    """Run all cache tests."""
    print("\n" + "=" * 60)
    print(" Fantasy Nerds Redis Cache Test Suite")
    print("=" * 60)
    print(f"\nStarted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Run test suites
        await test_basic_cache_operations()
        await test_compression_effectiveness()
        await test_cache_management()
        await test_with_real_api()

        print_section("Test Complete")
        print("\n✨ All tests completed!")

    except Exception as e:
        print_section("Test Failed")
        print(f"\n❌ Error during testing: {e}")
        raise

    print(f"\nFinished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
