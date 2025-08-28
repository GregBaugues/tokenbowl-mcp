#!/usr/bin/env python3
"""Clear Redis cache to fix memory issues"""

import os
import redis
import sys

REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')

def clear_cache():
    """Clear the player cache from Redis"""
    try:
        r = redis.from_url(REDIS_URL, decode_responses=False)
        
        # Delete cache keys
        deleted = 0
        for key in ['nfl_players:data', 'nfl_players:meta']:
            if r.delete(key):
                deleted += 1
                print(f"Deleted {key}")
        
        # Get memory info
        info = r.info('memory')
        used_mb = info.get('used_memory', 0) / (1024 * 1024)
        print(f"\nRedis memory usage: {used_mb:.2f} MB")
        print(f"Deleted {deleted} keys")
        
        return True
    except Exception as e:
        print(f"Error clearing cache: {e}")
        return False

if __name__ == "__main__":
    if clear_cache():
        print("Cache cleared successfully")
        sys.exit(0)
    else:
        print("Failed to clear cache")
        sys.exit(1)