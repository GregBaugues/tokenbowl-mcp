#!/usr/bin/env python3
"""
Enhanced player cache module that uses enriched data from Fantasy Nerds.
Provides automatic refresh on cache miss/expiry.
"""

import json
import gzip
import redis
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from build_cache import cache_enriched_players
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

def get_redis_client() -> redis.Redis:
    """Get Redis client connection."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    return redis.from_url(redis_url, decode_responses=False)

def get_enriched_players_from_cache() -> Optional[Dict[str, Any]]:
    """
    Get enriched player data from Redis cache.
    Automatically refreshes if cache is missing or expired.
    """
    try:
        r = get_redis_client()
        
        # Try to get cached data
        cache_key = "nfl_players_enriched"
        cached_data = r.get(cache_key)
        
        if cached_data:
            # Check metadata to see if it's fresh enough
            metadata = r.get(f"{cache_key}_metadata")
            if metadata:
                meta = json.loads(metadata)
                last_updated = datetime.fromisoformat(meta.get("last_updated"))
                age_hours = (datetime.now() - last_updated).total_seconds() / 3600
                
                # If cache is less than 6 hours old, use it
                if age_hours < 6:
                    logger.info(f"Using cached enriched data ({age_hours:.1f} hours old)")
                    decompressed = gzip.decompress(cached_data).decode('utf-8')
                    return json.loads(decompressed)
                else:
                    logger.info(f"Cache is {age_hours:.1f} hours old, refreshing...")
            else:
                logger.warning("Cache metadata missing, refreshing...")
        else:
            logger.info("No cached data found, fetching fresh data...")
        
        # Cache is missing or too old - refresh it
        logger.info("Refreshing enriched player cache...")
        success = cache_enriched_players()
        
        if success:
            # Try to get the newly cached data
            cached_data = r.get(cache_key)
            if cached_data:
                decompressed = gzip.decompress(cached_data).decode('utf-8')
                return json.loads(decompressed)
        
        logger.error("Failed to refresh cache")
        return None
        
    except Exception as e:
        logger.error(f"Error accessing enriched player cache: {e}")
        return None

def search_enriched_players(query: str, limit: int = 10) -> list:
    """
    Search enriched players by name.
    Returns list of matching players with all enriched data.
    """
    players = get_enriched_players_from_cache()
    if not players:
        return []
    
    query_lower = query.lower()
    results = []
    
    for player_id, player in players.items():
        full_name = player.get('full_name', '').lower()
        if query_lower in full_name:
            results.append({
                'player_id': player_id,
                **player
            })
            if len(results) >= limit:
                break
    
    return results

def get_enriched_player_by_id(player_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific enriched player by Sleeper ID.
    """
    players = get_enriched_players_from_cache()
    if not players:
        return None
    
    return players.get(player_id)

def get_cache_status() -> Dict[str, Any]:
    """
    Get the status of the enriched player cache.
    """
    try:
        r = get_redis_client()
        
        # Check if cache exists
        cache_key = "nfl_players_enriched"
        exists = r.exists(cache_key)
        
        if not exists:
            return {
                "exists": False,
                "message": "Cache not found"
            }
        
        # Get metadata
        metadata = r.get(f"{cache_key}_metadata")
        if metadata:
            meta = json.loads(metadata)
            last_updated = datetime.fromisoformat(meta.get("last_updated"))
            age_hours = (datetime.now() - last_updated).total_seconds() / 3600
            
            # Get refresh history
            history_key = "nfl_players_refresh_history"
            history = []
            history_data = r.lrange(history_key, 0, 4)  # Last 5 refreshes
            for item in history_data:
                history.append(json.loads(item))
            
            return {
                "exists": True,
                "last_updated": meta.get("last_updated"),
                "age_hours": round(age_hours, 1),
                "total_players": meta.get("total_players"),
                "players_with_projections": meta.get("players_with_projections"),
                "players_with_injuries": meta.get("players_with_injuries"),
                "players_with_news": meta.get("players_with_news"),
                "compressed_size_mb": round(meta.get("compressed_size_bytes", 0) / 1024 / 1024, 2),
                "refresh_history": history
            }
        
        return {
            "exists": True,
            "message": "Cache exists but metadata missing"
        }
        
    except Exception as e:
        return {
            "error": str(e)
        }

if __name__ == "__main__":
    # Test the cache
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "status":
            status = get_cache_status()
            print(json.dumps(status, indent=2))
        elif sys.argv[1] == "search":
            if len(sys.argv) > 2:
                results = search_enriched_players(sys.argv[2])
                for player in results[:3]:
                    print(f"{player['full_name']} - {player.get('team')} {player.get('position')}")
                    if player.get('data', {}).get('projections'):
                        print(f"  Proj Points: {player['data']['projections']['proj_pts']}")
            else:
                print("Usage: python players_cache_enriched.py search <name>")
        elif sys.argv[1] == "refresh":
            print("Forcing cache refresh...")
            success = cache_enriched_players()
            print("Success!" if success else "Failed!")
    else:
        print("Usage: python players_cache_enriched.py [status|search|refresh]")