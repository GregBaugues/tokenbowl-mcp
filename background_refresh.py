"""
Background cache refresh task for Render deployment.
This runs as part of the main MCP server process.
"""

import asyncio
import os
from datetime import datetime, timedelta
from unified_players_cache import update_unified_cache, get_unified_cache_status
import logging

logger = logging.getLogger(__name__)

# Refresh interval (in seconds)
REFRESH_INTERVAL = int(os.getenv("CACHE_REFRESH_INTERVAL", 86400))  # Default 24 hours


async def background_cache_refresh():
    """
    Background task that refreshes the cache periodically.
    Runs as part of the main application process.
    """
    while True:
        try:
            # Wait for the refresh interval
            await asyncio.sleep(REFRESH_INTERVAL)
            
            logger.info(f"Starting scheduled cache refresh at {datetime.now().isoformat()}")
            
            # Check if cache needs refresh (optional - could just refresh anyway)
            status = await get_unified_cache_status()
            if status.get("ttl_seconds", 0) < 3600:  # Less than 1 hour left
                logger.info("Cache TTL low, refreshing...")
                
                # Refresh the cache
                data = await update_unified_cache()
                enriched_count = sum(1 for p in data.values() if "ffnerd_data" in p)
                
                logger.info(f"Cache refreshed: {len(data)} players, {enriched_count} enriched")
            else:
                logger.info(f"Cache still fresh (TTL: {status.get('ttl_seconds')} seconds)")
                
        except Exception as e:
            logger.error(f"Background cache refresh failed: {e}")
            # Continue running even if refresh fails
            await asyncio.sleep(300)  # Wait 5 minutes before retrying


def start_background_refresh():
    """
    Start the background refresh task.
    Call this when starting the MCP server.
    """
    asyncio.create_task(background_cache_refresh())
    logger.info(f"Background cache refresh started (interval: {REFRESH_INTERVAL} seconds)")