#!/usr/bin/env python3
"""Test script to verify ChatGPT compatibility tools."""

import asyncio
import json
import sys

sys.path.insert(0, ".")

# Import the actual function implementations
import sleeper_mcp


async def test_search():
    """Test the search tool."""
    print("Testing search tool...")

    # Get the actual function from the decorated tool
    search_func = sleeper_mcp.search.fn

    # Test player search
    result = await search_func("Patrick Mahomes")
    print(f"Search for 'Patrick Mahomes': {json.dumps(result, indent=2)}")
    assert "results" in result
    assert len(result["results"]) > 0

    # Test waiver search
    result = await search_func("waiver RB")
    print(f"\nSearch for 'waiver RB': Found {len(result.get('results', []))} results")

    # Test trending search
    result = await search_func("trending")
    print(f"\nSearch for 'trending': Found {len(result.get('results', []))} results")

    print("\n✅ Search tool tests passed!")


async def test_fetch():
    """Test the fetch tool."""
    print("\nTesting fetch tool...")

    # Get the actual functions from the decorated tools
    search_func = sleeper_mcp.search.fn
    fetch_func = sleeper_mcp.fetch.fn

    # First get a player ID from search
    search_result = await search_func("Patrick Mahomes")
    if search_result["results"]:
        player_id = search_result["results"][0]["id"]
        print(f"Fetching player with ID: {player_id}")

        fetch_result = await fetch_func(player_id)
        print(f"\nFetch result keys: {list(fetch_result.keys())}")
        print(f"Title: {fetch_result.get('title')}")
        print(f"URL: {fetch_result.get('url')}")

        assert "id" in fetch_result
        assert "title" in fetch_result
        assert "text" in fetch_result
        assert "url" in fetch_result

        print("\n✅ Fetch tool tests passed!")
    else:
        print("⚠️  No search results to test fetch with")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("ChatGPT Compatibility Tools Test")
    print("=" * 60)

    try:
        await test_search()
        await test_fetch()

        print("\n" + "=" * 60)
        print("✅ All tests passed successfully!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
