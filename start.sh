#!/bin/bash
# Start script for Render deployment
# Refreshes cache on startup, then starts the MCP server

echo "🚀 Starting Token Bowl MCP Server"
echo "================================="

# Refresh the cache on startup
echo "📊 Refreshing player cache..."
uv run python -c "
import asyncio
from unified_players_cache import update_unified_cache

async def refresh():
    try:
        data = await update_unified_cache()
        enriched = sum(1 for p in data.values() if 'ffnerd_data' in p)
        print(f'✅ Cache refreshed: {len(data)} players, {enriched} enriched')
        return True
    except Exception as e:
        print(f'⚠️ Cache refresh failed: {e}')
        print('Continuing with existing cache...')
        return False

asyncio.run(refresh())
"

# Start the MCP server
echo "🌐 Starting MCP server..."
exec uv run python sleeper_mcp.py http