#!/usr/bin/env python3
"""
Manually trigger cache refresh on production server
"""

import sys


def trigger_refresh():
    """Trigger cache refresh via MCP tool call"""
    # base_url = "https://tokenbowl-mcp.onrender.com"

    # This would need proper MCP protocol implementation
    # For now, just call the build_cache script locally
    import subprocess

    result = subprocess.run(
        ["uv", "run", "python", "build_cache.py"], capture_output=True, text=True
    )

    if result.returncode == 0:
        print("Cache refresh successful!")
        print(result.stdout)
    else:
        print("Cache refresh failed!")
        print(result.stderr)
        sys.exit(1)


if __name__ == "__main__":
    trigger_refresh()
