#!/usr/bin/env python3
"""Main MCP Server - Composes Sleeper and Fantasy Nerds APIs"""

import sys
import os
import asyncio
from fastmcp import FastMCP
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize main MCP server
main_mcp = FastMCP("tokenbowl-mcp")

# Import the individual servers
from sleeper_mcp import mcp as sleeper_server
from ffnerds_mcp import mcp as ffnerds_server


async def setup_servers():
    """Setup and compose the servers"""
    # Mount the Sleeper server without prefix (keeping original tool names)
    await main_mcp.import_server(sleeper_server)
    
    # Mount the Fantasy Nerds server with prefix to avoid conflicts
    await main_mcp.import_server(ffnerds_server, prefix="ffnerds")
    
    logger.info("Successfully composed Sleeper and Fantasy Nerds MCP servers")


# Add health check endpoint for Render
@main_mcp.custom_route("/health", methods=["GET"])
async def health_check():
    """Health check endpoint for Render"""
    return {"status": "healthy", "service": "tokenbowl-mcp"}


if __name__ == "__main__":
    # Setup the composed servers
    asyncio.run(setup_servers())
    
    # Check for environment variable or command line argument
    if os.getenv("RENDER") or (len(sys.argv) > 1 and sys.argv[1] == "http"):
        # Use PORT env variable (required by Render) or command line arg
        port = int(os.getenv("PORT", 8000))
        if len(sys.argv) > 2:
            port = int(sys.argv[2])
        
        # Bind to 0.0.0.0 for external access (required for cloud deployment)
        main_mcp.run(transport="sse", port=port, host="0.0.0.0")
    else:
        # Default to stdio for backward compatibility (Claude Desktop)
        main_mcp.run()