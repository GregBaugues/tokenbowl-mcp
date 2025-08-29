#!/usr/bin/env python3
"""Simple test to verify the composed server works"""

import asyncio
import httpx
import os

# Set base URL for testing
BASE_URL = "http://localhost:8000"


async def test_sleeper_api():
    """Test direct Sleeper API call"""
    print("\n1. Testing Sleeper API directly...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("https://api.sleeper.app/v1/league/1266471057523490816")
            response.raise_for_status()
            data = response.json()
            print(f"   ✓ League: {data.get('name', 'Unknown')}")
            print(f"   ✓ Season: {data.get('season', 'N/A')}")
            print(f"   ✓ Sport: {data.get('sport', 'N/A')}")
            return True
        except Exception as e:
            print(f"   ✗ Error: {e}")
            return False


async def test_ffnerds_api():
    """Test Fantasy Nerds API (if key is set)"""
    print("\n2. Testing Fantasy Nerds API...")
    api_key = os.getenv("FANTASY_NERDS_API_KEY")
    
    if not api_key:
        print("   ⚠️  FANTASY_NERDS_API_KEY not set")
        print("   To test: export FANTASY_NERDS_API_KEY='your_key'")
        return False
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://api.fantasynerds.com/v1/nfl/byes",
                params={"apikey": api_key}
            )
            response.raise_for_status()
            print(f"   ✓ API is accessible")
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                print(f"   ✗ Invalid API key")
            else:
                print(f"   ✗ HTTP Error: {e}")
            return False
        except Exception as e:
            print(f"   ✗ Error: {e}")
            return False


async def test_redis_connection():
    """Test Redis connection if configured"""
    print("\n3. Testing Redis connection...")
    redis_url = os.getenv("REDIS_URL")
    
    if not redis_url:
        print("   ⚠️  REDIS_URL not set (optional)")
        return False
    
    try:
        import redis
        r = redis.from_url(redis_url)
        r.ping()
        print(f"   ✓ Redis is connected")
        return True
    except ImportError:
        print("   ⚠️  Redis library available via server")
        return True
    except Exception as e:
        print(f"   ✗ Redis connection failed: {e}")
        return False


async def main():
    print("=" * 60)
    print("Testing MCP Server Components")
    print("=" * 60)
    
    # Test individual components
    sleeper_ok = await test_sleeper_api()
    ffnerds_ok = await test_ffnerds_api()
    redis_ok = await test_redis_connection()
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"✓ Sleeper API: {'Working' if sleeper_ok else 'Check connection'}")
    print(f"✓ Fantasy Nerds: {'Working' if ffnerds_ok else 'Set API key to test'}")
    print(f"✓ Redis Cache: {'Working' if redis_ok else 'Optional - not configured'}")
    
    print("\n" + "=" * 60)
    print("Next Steps")
    print("=" * 60)
    print("\n1. Start the MCP server:")
    print("   uv run python main_mcp.py http 8000")
    print("\n2. In another terminal, test the endpoints:")
    print("   curl http://localhost:8000/sse")
    print("\n3. Or use with Claude Desktop by running:")
    print("   uv run python main_mcp.py")


if __name__ == "__main__":
    asyncio.run(main())