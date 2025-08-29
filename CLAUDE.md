# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a composed Model Context Protocol (MCP) server that combines:
1. **Sleeper Fantasy Sports API** - Hardcoded for league ID `1266471057523490816`
2. **Fantasy Nerds API** - Comprehensive NFL fantasy data and projections

The server uses FastMCP's composition features to modularly combine multiple API servers while keeping them separate for future flexibility.

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
uv run python main_mcp.py http        # Default port 8000
uv run python main_mcp.py http 3000   # Custom port
```

**STDIO Mode (for Claude Desktop):**
```bash
uv run python main_mcp.py
```

### Deployment

The project is configured for Render deployment via `render.yaml`. When pushing to the main branch, it automatically deploys if autoDeploy is enabled.

## Architecture

### Core Components

1. **main_mcp.py**: Main composition server that combines all APIs
   - Uses FastMCP's `import_server()` for composition
   - Entry point for all deployments
   - Composes Sleeper and Fantasy Nerds servers

2. **sleeper_mcp.py**: Sleeper Fantasy Sports API server
   - Hardcoded `LEAGUE_ID = "1266471057523490816"`
   - Base API URL: `https://api.sleeper.app/v1`
   - 20 tools for league, user, player, and draft operations
   - Redis caching for player data

3. **ffnerds_mcp.py**: Fantasy Nerds API server
   - Base API URL: `https://api.fantasynerds.com/v1/nfl`
   - 25 tools for comprehensive fantasy football data
   - All tools prefixed with `ffnerds_` when composed
   - Requires `FANTASY_NERDS_API_KEY` environment variable

4. **Transport Modes**:
   - **HTTP/SSE**: For web deployment (binds to 0.0.0.0 when `RENDER` env var is set or `http` argument provided)
   - **STDIO**: Default mode for Claude Desktop integration

5. **Deployment Configuration**:
   - **render.yaml**: Defines build and start commands for Render deployment
   - Build: `pip install uv && uv sync`
   - Start: `uv run python main_mcp.py http`
   - Python version: 3.13 (specified via PYTHON_VERSION env var)
   - Environment variables: `RENDER`, `PYTHON_VERSION`, `FANTASY_NERDS_API_KEY`

## Key Implementation Details

- The server detects deployment environment via `RENDER` env variable or command line arguments
- Port is configurable via `PORT` environment variable (required by Render) or command line
- When deployed, binds to `0.0.0.0` for external access
- All API calls use `httpx.AsyncClient` with proper error handling via `raise_for_status()`
- Large dataset endpoints (like `get_nfl_players`) use extended timeouts (30s)

## Available Tools

### Sleeper API Tools (20 tools, no prefix):
- **League operations**: info, rosters, users, matchups, transactions, traded picks, drafts, playoffs
- **User operations**: profile, leagues, drafts
- **Player data**: all NFL players, trending adds/drops, search by name/ID, cache management
- **Draft operations**: draft details, picks, traded picks

### Fantasy Nerds API Tools (25 tools, `ffnerds_` prefix):
- **Draft tools**: auction values, ADP, draft projections, draft rankings, best ball rankings
- **Rankings**: weekly rankings, dynasty rankings, defense rankings, IDP rankings, player tiers
- **Projections**: weekly projections, rest of season projections, playoff projections
- **Player data**: player list, player details, fantasy leaders, adds/drops
- **League info**: bye weeks, depth charts, injuries, NFL schedule, teams
- **DFS**: DFS projections, DFS slates
- **News**: NFL news updates

## Dependencies

- **fastmcp>=2.11.3**: MCP server framework
- **httpx>=0.28.1**: Async HTTP client for API calls
- **uv**: Modern Python package manager (must be installed separately for local development)