#!/usr/bin/env python
"""
Cache refresh endpoint for Render deployment.
This can be called by:
1. Render Cron Jobs (paid feature)
2. External cron services (cron-job.org, EasyCron, etc.)
3. GitHub Actions on a schedule
4. Manual trigger via curl/webhook
"""

import asyncio
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from unified_players_cache import update_unified_cache, get_unified_cache_status

# Load environment variables
load_dotenv()

# Create FastAPI app for the refresh endpoint
app = FastAPI(title="Cache Refresh API")

# Optional: Add a secret token for security
REFRESH_TOKEN = os.getenv("CACHE_REFRESH_TOKEN", "your-secret-token-here")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "cache-refresh"}


@app.get("/cache/status")
async def cache_status():
    """Get current cache status."""
    status = await get_unified_cache_status()
    return status


@app.post("/cache/refresh")
async def refresh_cache(authorization: str = Header(None)):
    """
    Refresh the unified player cache.
    
    Protected by token in Authorization header.
    Call with: curl -X POST -H "Authorization: Bearer your-secret-token-here" https://your-app.onrender.com/cache/refresh
    """
    # Check authorization token
    if authorization != f"Bearer {REFRESH_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        print(f"Cache refresh triggered at {datetime.now().isoformat()}")
        
        # Get current status
        old_status = await get_unified_cache_status()
        
        # Refresh cache
        data = await update_unified_cache()
        enriched_count = sum(1 for p in data.values() if "ffnerd_data" in p)
        
        # Get new status
        new_status = await get_unified_cache_status()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "before": {
                    "total_players": old_status.get("total_players", 0),
                    "enriched_players": old_status.get("enriched_players", 0),
                },
                "after": {
                    "total_players": len(data),
                    "enriched_players": enriched_count,
                    "enrichment_rate": f"{(enriched_count/len(data)*100):.1f}%",
                    "cache_size_mb": new_status.get("compressed_size_mb", 0),
                },
                "message": f"Cache refreshed: {len(data)} players, {enriched_count} enriched"
            }
        )
    except Exception as e:
        print(f"Cache refresh failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cache refresh failed: {str(e)}")


@app.post("/cache/refresh/webhook")
async def refresh_cache_webhook():
    """
    Simple webhook endpoint for services that don't support auth headers.
    Less secure but works with basic webhook services.
    """
    try:
        data = await update_unified_cache()
        enriched_count = sum(1 for p in data.values() if "ffnerd_data" in p)
        
        return {
            "success": True,
            "players_cached": len(data),
            "players_enriched": enriched_count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001))
    
    # Run the cache refresh API
    print(f"Starting cache refresh API on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)