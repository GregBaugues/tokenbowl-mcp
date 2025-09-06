#!/usr/bin/env python3
"""
Background task to refresh the enriched player cache.
Runs continuously and refreshes the cache every 6 hours.
Can be deployed as a Render background worker.
"""

import time
import logging
import os
from datetime import datetime, timedelta
from build_cache import cache_enriched_players
import redis
import json
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_redis_client() -> redis.Redis:
    """Get Redis client connection."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    return redis.from_url(redis_url, decode_responses=False)

def should_refresh_cache() -> bool:
    """Check if cache needs refreshing based on age or missing."""
    try:
        r = get_redis_client()
        
        # Check if cache exists
        if not r.exists("nfl_players_enriched"):
            logger.info("Cache does not exist, refresh needed")
            return True
        
        # Check metadata for last update time
        metadata = r.get("nfl_players_enriched_metadata")
        if not metadata:
            logger.info("Cache metadata missing, refresh needed")
            return True
        
        meta = json.loads(metadata)
        last_updated = datetime.fromisoformat(meta.get("last_updated"))
        age_hours = (datetime.now() - last_updated).total_seconds() / 3600
        
        # Refresh if older than 6 hours
        if age_hours >= 6:
            logger.info(f"Cache is {age_hours:.1f} hours old, refresh needed")
            return True
        
        logger.info(f"Cache is {age_hours:.1f} hours old, no refresh needed yet")
        return False
        
    except Exception as e:
        logger.error(f"Error checking cache status: {e}")
        return True  # Refresh on error

def run_background_refresh():
    """Run the background refresh loop."""
    logger.info("Starting background refresh service...")
    
    # Initial delay to let the main service start
    initial_delay = int(os.getenv("INITIAL_DELAY_SECONDS", "60"))
    if initial_delay > 0:
        logger.info(f"Waiting {initial_delay} seconds before first refresh check...")
        time.sleep(initial_delay)
    
    # Refresh interval (default 6 hours)
    refresh_interval_hours = float(os.getenv("REFRESH_INTERVAL_HOURS", "6"))
    refresh_interval_seconds = refresh_interval_hours * 3600
    
    logger.info(f"Refresh interval set to {refresh_interval_hours} hours")
    
    while True:
        try:
            if should_refresh_cache():
                logger.info("Starting cache refresh...")
                start_time = time.time()
                
                success = cache_enriched_players()
                
                elapsed = time.time() - start_time
                
                if success:
                    logger.info(f"Cache refresh completed successfully in {elapsed:.1f} seconds")
                    
                    # Store refresh history
                    try:
                        r = get_redis_client()
                        history_key = "nfl_players_refresh_history"
                        history = {
                            "timestamp": datetime.now().isoformat(),
                            "duration_seconds": elapsed,
                            "success": True
                        }
                        
                        # Keep last 10 refresh records
                        r.lpush(history_key, json.dumps(history))
                        r.ltrim(history_key, 0, 9)
                        r.expire(history_key, 7 * 24 * 3600)  # Keep history for 7 days
                    except Exception as e:
                        logger.warning(f"Failed to store refresh history: {e}")
                else:
                    logger.error("Cache refresh failed")
            
            # Sleep until next check (check every hour, but only refresh if needed)
            check_interval = min(3600, refresh_interval_seconds)  # Check at least hourly
            logger.info(f"Sleeping for {check_interval/3600:.1f} hours until next check...")
            time.sleep(check_interval)
            
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
            break
        except Exception as e:
            logger.error(f"Unexpected error in refresh loop: {e}")
            logger.info("Waiting 5 minutes before retry...")
            time.sleep(300)  # Wait 5 minutes before retrying

if __name__ == "__main__":
    run_background_refresh()