#!/usr/bin/env python3
"""Debug Redis cache issues"""

import redis
import json
import httpx
import asyncio
import os

# Redis URL - using internal URL since we're testing from Render
# For local testing, you'd need the external URL with credentials
REDIS_URL = os.getenv("REDIS_URL", "redis://red-d2o755emcj7s73b8bj9g:6379")


async def test_redis_connection():
    """Test basic Redis connectivity"""
    print(f"Testing Redis URL: {REDIS_URL}")
    try:
        r = redis.from_url(REDIS_URL, decode_responses=False)
        r.ping()
        print("✅ Redis connection successful!")

        # Check memory usage
        info = r.info("memory")
        print("\n📊 Memory Stats:")
        print(f"  Used memory: {info.get('used_memory_human', 'Unknown')}")
        print(f"  Used memory RSS: {info.get('used_memory_rss_human', 'Unknown')}")
        print(
            f"  Memory fragmentation: {info.get('mem_fragmentation_ratio', 'Unknown')}"
        )

        # Check current keys
        keys = r.keys("*")
        print(f"\n🔑 Current keys in Redis: {len(keys)}")
        if keys:
            for key in keys[:5]:  # Show first 5 keys
                key_type = r.type(key).decode()
                ttl = r.ttl(key)
                size = r.memory_usage(key)
                print(
                    f"  - {key.decode()}: type={key_type}, ttl={ttl}s, size={size} bytes"
                )

        return r
    except redis.ConnectionError as e:
        print(f"❌ Redis connection failed: {e}")
        print(
            "\nTip: If running locally, you need the external Redis URL with credentials."
        )
        print("     Check Render dashboard for the connection string.")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None


async def fetch_player_data():
    """Fetch player data from Sleeper API"""
    print("\n📥 Fetching player data from Sleeper API...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get("https://api.sleeper.app/v1/players/nfl")
        response.raise_for_status()
        data = response.json()

        json_str = json.dumps(data)
        size_mb = len(json_str) / (1024 * 1024)
        print(f"  Data fetched: {len(data)} players")
        print(f"  JSON size: {size_mb:.2f} MB")

        return data, json_str


async def test_redis_storage(r, data, json_str):
    """Test storing data in Redis"""
    print("\n💾 Testing Redis storage...")

    try:
        # Clear existing cache keys
        print("  Clearing existing cache keys...")
        r.delete("nfl_players:data", "nfl_players:meta")

        # Try to store the data
        print(
            f"  Attempting to store {len(json_str) / (1024 * 1024):.2f} MB of data..."
        )
        r.setex("nfl_players:data", 86400, json_str)

        # Store metadata
        meta = {"player_count": len(data), "size_mb": len(json_str) / (1024 * 1024)}
        r.setex("nfl_players:meta", 86400, json.dumps(meta))

        print("✅ Data stored successfully!")

        # Check memory after storage
        info = r.info("memory")
        print("\n📊 Memory after storage:")
        print(f"  Used memory: {info.get('used_memory_human', 'Unknown')}")

        return True

    except redis.ResponseError as e:
        if "OOM" in str(e) or "maxmemory" in str(e):
            print(f"❌ Out of memory error: {e}")
            print("\n💡 Solution: The data is too large for the free tier.")
            print("   Options:")
            print("   1. Upgrade to a larger Redis plan")
            print(
                "   2. Store only essential player data (filter out inactive/irrelevant players)"
            )
            print("   3. Use compression before storing")
        else:
            print(f"❌ Redis error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


async def test_compressed_storage(r, data):
    """Test storing compressed data in Redis"""
    import gzip

    print("\n🗜️ Testing compressed storage...")

    # Filter to only active players to reduce size
    active_players = {
        k: v
        for k, v in data.items()
        if v and isinstance(v, dict) and v.get("active", False)
    }

    print(f"  Active players: {len(active_players)} (out of {len(data)})")

    json_str = json.dumps(active_players)
    compressed = gzip.compress(json_str.encode())

    print(f"  Original size: {len(json_str) / (1024 * 1024):.2f} MB")
    print(f"  Compressed size: {len(compressed) / (1024 * 1024):.2f} MB")
    print(f"  Compression ratio: {len(json_str) / len(compressed):.2f}x")

    try:
        r.delete("nfl_players:data:compressed", "nfl_players:meta")
        r.setex("nfl_players:data:compressed", 86400, compressed)

        meta = {
            "player_count": len(active_players),
            "compressed_size_mb": len(compressed) / (1024 * 1024),
            "compression": "gzip",
        }
        r.setex("nfl_players:meta", 86400, json.dumps(meta))

        print("✅ Compressed data stored successfully!")

        # Test retrieval
        retrieved = r.get("nfl_players:data:compressed")
        decompressed = gzip.decompress(retrieved)
        retrieved_data = json.loads(decompressed)
        print(f"  Verified: Retrieved {len(retrieved_data)} players")

        return True

    except Exception as e:
        print(f"❌ Error storing compressed data: {e}")
        return False


async def main():
    """Main diagnostic function"""
    print("🔍 Redis Cache Diagnostic Tool\n")

    # Test connection
    r = await test_redis_connection()
    if not r:
        print("\n⚠️  Cannot proceed without Redis connection")
        print("For local testing, set REDIS_URL environment variable with external URL")
        return

    # Fetch player data
    data, json_str = await fetch_player_data()

    # Test normal storage
    success = await test_redis_storage(r, data, json_str)

    if not success:
        # Try compressed storage as fallback
        await test_compressed_storage(r, data)


if __name__ == "__main__":
    asyncio.run(main())
