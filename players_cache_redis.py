import json
import os
from datetime import datetime, timedelta
import httpx
from typing import Optional, Dict, Any
import redis
from redis.exceptions import RedisError

# Redis connection (Render provides REDIS_URL env var)
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
PLAYERS_API_URL = "https://api.sleeper.app/v1/players/nfl"
CACHE_KEY = "nfl_players:data"
META_KEY = "nfl_players:meta"
CACHE_TTL = 86400  # 24 hours in seconds

def get_redis_client():
    """Get Redis client with connection pooling"""
    return redis.from_url(REDIS_URL, decode_responses=False)

def is_cache_valid() -> bool:
    """Check if cache exists and is still valid"""
    try:
        r = get_redis_client()
        return r.exists(CACHE_KEY) and r.exists(META_KEY)
    except RedisError:
        return False

async def fetch_players_from_api() -> Dict[str, Any]:
    """Fetch fresh player data from Sleeper API"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(PLAYERS_API_URL)
        response.raise_for_status()
        return response.json()

async def update_cache():
    """Update the cache with fresh data from API"""
    print("Fetching fresh player data from Sleeper API...")
    players_data = await fetch_players_from_api()
    
    r = get_redis_client()
    
    # Store player data with TTL
    players_json = json.dumps(players_data)
    r.setex(CACHE_KEY, CACHE_TTL, players_json)
    
    # Store metadata
    meta = {
        'last_updated': datetime.now().isoformat(),
        'player_count': len(players_data),
        'size_mb': len(players_json) / (1024 * 1024)
    }
    r.setex(META_KEY, CACHE_TTL, json.dumps(meta))
    
    print(f"Cache updated: {meta['player_count']} players, {meta['size_mb']:.2f} MB")
    return players_data

async def get_all_players() -> Dict[str, Any]:
    """Get all players, using cache if valid, otherwise fetch fresh"""
    r = get_redis_client()
    
    try:
        # Try to get from cache first
        cached_data = r.get(CACHE_KEY)
        if cached_data:
            print("Using cached player data from Redis")
            return json.loads(cached_data)
    except RedisError as e:
        print(f"Redis error, fetching fresh: {e}")
    
    # Cache miss or error - fetch fresh
    print("Cache invalid or missing, fetching fresh data")
    return await update_cache()

def search_player(players: Dict[str, Any], name: str) -> list:
    """Search for players by name"""
    results = []
    name_lower = name.lower()
    
    for player_id, player_data in players.items():
        if player_data and isinstance(player_data, dict):
            full_name = player_data.get('full_name', '').lower()
            if name_lower in full_name:
                results.append({
                    'id': player_id,
                    'name': player_data.get('full_name'),
                    'position': player_data.get('position'),
                    'team': player_data.get('team'),
                    'status': player_data.get('status'),
                    'age': player_data.get('age'),
                    'data': player_data
                })
    
    return results

async def get_player_by_name(name: str) -> list:
    """Get player data by name (uses cache)"""
    players = await get_all_players()
    return search_player(players, name)

async def get_player_by_id(player_id: str) -> Optional[Dict[str, Any]]:
    """Get player data by ID (uses cache)"""
    players = await get_all_players()
    return players.get(player_id)

async def force_refresh():
    """Force a cache refresh regardless of TTL"""
    return await update_cache()

# Health check endpoint helper
async def get_cache_status() -> Dict[str, Any]:
    """Get cache status for monitoring"""
    r = get_redis_client()
    
    try:
        meta = r.get(META_KEY)
        if meta:
            meta_data = json.loads(meta)
            ttl = r.ttl(CACHE_KEY)
            meta_data['ttl_seconds'] = ttl
            meta_data['valid'] = True
            return meta_data
    except RedisError:
        pass
    
    return {'valid': False, 'error': 'Cache not available'}

# Example usage
async def main():
    # Get Josh Allen's data
    josh_allen_results = await get_player_by_name("Josh Allen")
    
    if josh_allen_results:
        for player in josh_allen_results:
            print(f"\n{player['name']} - {player['position']} - {player['team']}")
            print(f"  ID: {player['id']}")
            print(f"  Age: {player['age']}")
            print(f"  Status: {player['status']}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())