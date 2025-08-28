# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Model Context Protocol (MCP) server for the Sleeper Fantasy Sports API built with FastMCP. The server is hardcoded for league ID `1266471057523490816` and provides tools to interact with the Sleeper API.

## Development Commands

### Setup and Dependencies
```bash
# Install/sync dependencies using uv
uv sync

# The project uses Python 3.12+ (see .python-version)
```

### Running the Server

**HTTP/SSE Mode (for web deployment):**
```bash
uv run python sleeper_mcp.py http        # Default port 8000
uv run python sleeper_mcp.py http 3000   # Custom port
```

**STDIO Mode (for Claude Desktop):**
```bash
uv run python sleeper_mcp.py
```

### Deployment

The project is configured for Render deployment via `render.yaml`. When pushing to the main branch, it automatically deploys if autoDeploy is enabled.

## Architecture

### Core Components

1. **sleeper_mcp.py**: Single-file MCP server implementation
   - Uses FastMCP framework for tool definitions
   - All tools are async functions decorated with `@mcp.tool()`
   - Hardcoded `LEAGUE_ID = "1266471057523490816"`
   - Base API URL: `https://api.sleeper.app/v1`

2. **Transport Modes**:
   - **HTTP/SSE**: For web deployment (binds to 0.0.0.0 when `RENDER` env var is set or `http` argument provided)
   - **STDIO**: Default mode for Claude Desktop integration

3. **Deployment Configuration**:
   - **render.yaml**: Defines build and start commands for Render deployment
   - Build: `pip install uv && uv sync`
   - Start: `uv run python sleeper_mcp.py http`
   - Python version: 3.13 (specified via PYTHON_VERSION env var)

## Key Implementation Details

- The server detects deployment environment via `RENDER` env variable or command line arguments
- Port is configurable via `PORT` environment variable (required by Render) or command line
- When deployed, binds to `0.0.0.0` for external access
- All API calls use `httpx.AsyncClient` with proper error handling via `raise_for_status()`
- Large dataset endpoints (like `get_nfl_players`) use extended timeouts (30s)

## Available Tools

The server exposes these Sleeper API endpoints as MCP tools:
- League operations (info, rosters, users, matchups, transactions, traded picks, drafts, playoffs)
- User operations (profile, leagues, drafts)
- Player data (all NFL players, trending adds/drops)
- Draft operations (draft details, picks, traded picks)

## Dependencies

- **fastmcp>=2.11.3**: MCP server framework
- **httpx>=0.28.1**: Async HTTP client for API calls
- **uv**: Modern Python package manager (must be installed separately for local development)