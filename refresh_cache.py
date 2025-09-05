#!/usr/bin/env python
"""
Manual cache refresh script for unified player data.
Run this to force refresh the cache with latest Sleeper + Fantasy Nerds data.
"""

import asyncio
import os
from dotenv import load_dotenv
from unified_players_cache import update_unified_cache, get_unified_cache_status

# Load environment variables
load_dotenv()


async def main():
    print("🔄 Starting unified cache refresh...")
    print("-" * 50)
    
    # Check current cache status
    print("\n📊 Current cache status:")
    status = await get_unified_cache_status()
    if status.get("valid"):
        print(f"  • Total players: {status.get('total_players', 0)}")
        print(f"  • Enriched players: {status.get('enriched_players', 0)}")
        print(f"  • Last updated: {status.get('last_updated', 'Unknown')}")
        print(f"  • TTL remaining: {status.get('ttl_seconds', 0)} seconds")
    else:
        print(f"  • Cache invalid or missing: {status.get('error', 'Unknown error')}")
    
    # Refresh the cache
    print("\n🚀 Fetching fresh data from APIs...")
    print("  • Fetching from Sleeper API...")
    print("  • Fetching from Fantasy Nerds API...")
    print("  • Mapping player IDs...")
    print("  • Building unified dataset...")
    
    try:
        data = await update_unified_cache()
        
        # Count enriched players
        enriched_count = sum(1 for p in data.values() if "ffnerd_data" in p)
        
        print("\n✅ Cache refresh complete!")
        print("-" * 50)
        print(f"  • Total players cached: {len(data)}")
        print(f"  • Players enriched with FFNerd data: {enriched_count}")
        print(f"  • Enrichment rate: {(enriched_count/len(data)*100):.1f}%")
        
        # Check new cache status
        new_status = await get_unified_cache_status()
        if new_status.get("valid"):
            print(f"  • Cache size: {new_status.get('compressed_size_mb', 0):.2f} MB (compressed)")
            print(f"  • Redis memory used: {new_status.get('redis_memory_used_mb', 0):.2f} MB")
        
        print("\n🎉 Unified player data is now up to date!")
        
    except Exception as e:
        print(f"\n❌ Error refreshing cache: {e}")
        print("\nTroubleshooting:")
        print("  1. Check REDIS_URL is set correctly")
        print("  2. Check FFNERD_API_KEY is set correctly")
        print("  3. Ensure Redis service is running")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)