#!/bin/bash
# Cron script to refresh the unified player cache daily
# Add to crontab with: crontab -e
# Example cron entry for daily refresh at 3 AM:
# 0 3 * * * /path/to/sleeper-mcp/cron_refresh.sh >> /path/to/logs/cache_refresh.log 2>&1

# Change to script directory
cd "$(dirname "$0")"

# Load environment variables
source .env

# Add timestamp
echo "======================================"
echo "Cache refresh started at $(date)"
echo "======================================"

# Run the refresh script
uv run python refresh_cache.py

# Add completion timestamp
echo "Cache refresh completed at $(date)"
echo ""