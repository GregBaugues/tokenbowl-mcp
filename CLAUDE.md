# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the Token Bowl MCP server - a Model Context Protocol server for fantasy football leagues using the Sleeper Fantasy Sports API. Built with FastMCP, it defaults to the Token Bowl league (ID: `1266471057523490816`) but can be configured for any league via the `SLEEPER_LEAGUE_ID` environment variable. Provides 21 tools to interact with fantasy football data.

**Context**: This is part of the larger `tokenbowl` system - an LLM-powered fantasy football league management system.

## Directory Structure

```
sleeper-mcp/
├── sleeper_mcp.py           # Main MCP server
├── players_cache_redis.py   # Redis caching layer
├── build_cache.py           # Cache building functions
├── cache_client.py          # Cache client interface
├── scripts/                 # Utility scripts
│   ├── manual_cache_refresh.py
│   ├── parse_trade_proposal.py
│   └── extract_trade_proposal.py
├── data/                    # Data files and analyses
├── picks/                   # Weekly picks (week1, week2, etc.)
├── slopups/                 # Weekly summaries
├── scratchpads/             # Development notes and issues
├── tests/                   # Test suite
└── .github/workflows/       # CI/CD configuration
``` 

## Development Commands

### Setup and Dependencies
```bash
# Install/sync dependencies using uv
uv sync

# The project uses Python 3.12+ (see .python-version)

# Create .env file for local development
cp .env.example .env
# Edit .env with your actual API keys and configuration
```

### Environment Variables
These are located in .env
- `FFNERD_API_KEY`: Fantasy Nerds API key for extended analytics
- `SLEEPER_LEAGUE_ID`: Sleeper league ID (defaults to Token Bowl: 1266471057523490816)
- `REDIS_URL`: Redis connection URL (defaults to redis://localhost:6379)
wy
### GitHub
use `gh` for all interaction with github

### IMPORTANT: Pre-PR Checklist
Before creating any Pull Request, you MUST:
1. Run linting: `uv run ruff check .`
2. Run formatting check: `uv run ruff format . --check`
3. Fix any issues found (use `uv run ruff format .` to auto-format)
4. Run tests: `uv run pytest`

PRs will automatically fail CI if linting doesn't pass!


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

### Utility Commands
```bash
# Clear Redis cache
uv run python clear_cache.py

# Debug Redis connection and view cache status
uv run python debug_redis.py
```

### Testing
```bash
# Install test dependencies
uv sync --extra test

# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=. --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_sleeper_mcp.py

# Run tests with VCR cassette recording (first time)
uv run pytest --vcr-record=once

# Run tests without hitting external APIs (replay mode)
uv run pytest --vcr-record=none

# Run linting (ALWAYS run before creating a PR)
uv run ruff check .
uv run ruff format . --check
```

### Pre-commit Hooks (Recommended)

To automatically check linting before committing:

```bash
# Install dev dependencies including pre-commit
uv sync --extra dev

# Install the pre-commit hooks
uv run pre-commit install

# Run hooks manually on all files
uv run pre-commit run --all-files
```

This will automatically run `ruff` linting and formatting checks before each commit, preventing linting issues from reaching PRs.

### CI/CD

**IMPORTANT: Before creating any PR, you MUST run:**
```bash
uv run ruff check .
uv run ruff format . --check
```

GitHub Actions CI runs on every push and PR:
- Tests on Python 3.11, 3.12, and 3.13
- Runs linting with ruff (PRs will fail if linting doesn't pass)
- Provides test reports and artifacts
- Uses Redis service container for integration tests

CI workflow is defined in `.github/workflows/ci.yml`

### Deployment

The project is configured for Render deployment via `render.yaml`. When pushing to the main branch, it automatically deploys if autoDeploy is enabled.

**Production Details:**
- **Repository**: https://github.com/GregBaugues/sleeper-mcp
- **Render Service ID**: `srv-d2o5vv95pdvs739hqde0`
- **Redis Cache ID**: `red-d2o755emcj7s73b8bj9g`
- **Deployment**: Auto-deploys on push to `main` branch
- **MCP Tool Prefix**: When deployed, tools are prefixed with `mcp__tokenbowl__`

## Architecture

### Core Components

1. **sleeper_mcp.py**: Single-file MCP server implementation (21 tools)
   - Uses FastMCP framework for tool definitions
   - All tools are async functions decorated with `@mcp.tool()`
   - `LEAGUE_ID` from environment variable `SLEEPER_LEAGUE_ID` (default: `1266471057523490816`)
   - Base API URL: `https://api.sleeper.app/v1`
   - Environment-aware transport detection

2. **players_cache_redis.py**: Redis caching layer for NFL player data
   - Caches 5MB+ player dataset to avoid API rate limits
   - 24-hour TTL with automatic refresh
   - Gzip compression to reduce memory usage
   - Aggressive filtering for free Redis tier constraints
   - Connection pooling and robust error handling

3. **Transport Modes**:
   - **HTTP/SSE**: For web deployment (binds to 0.0.0.0 when `RENDER` env var is set or `http` argument provided)
   - **STDIO**: Default mode for Claude Desktop integration

4. **Deployment Configuration**:
   - **render.yaml**: Defines build and start commands for Render deployment
   - Build: `pip install uv && uv sync`
   - Start: `uv run python sleeper_mcp.py http`
   - Python version: 3.13 (specified via PYTHON_VERSION env var)
   - Health check endpoint: `/health`

## Key Implementation Details

- Environment variables are loaded from `.env` file using python-dotenv for local development
- The server detects deployment environment via `RENDER` env variable or command line arguments
- Port is configurable via `PORT` environment variable (required by Render) or command line
- When deployed, binds to `0.0.0.0` for external access, localhost for local development
- All API calls use `httpx.AsyncClient` with proper error handling via `raise_for_status()`
- Large dataset endpoints (like `get_nfl_players`) use extended timeouts (30s)
- Redis connection via `REDIS_URL` environment variable
- Player search functions utilize cached data for instant responses

## Available Tools

The server exposes 21 Sleeper API endpoints as MCP tools:
- **League operations**: info, rosters, users, matchups, transactions, traded picks, drafts, playoffs
- **User operations**: profile, leagues, drafts
- **Player data**: all NFL players (cached), trending adds/drops, search by name/ID
- **Draft operations**: draft details, picks, traded picks
- **Cache operations**: status, refresh, search functionality

## Dependencies

- **fastmcp>=2.11.3**: MCP server framework
- **httpx>=0.28.1**: Async HTTP client for API calls
- **redis>=5.0.0**: Redis client for caching layer
- **python-dotenv**: Environment variable loading from .env files
- **uv**: Modern Python package manager (must be installed separately for local development)

## Production Management

When deployed, you can manage the production service using Render MCP tools in Claude:
- `mcp__render__list_services` - View deployed services
- `mcp__render__get_service` - Get service details
- `mcp__render__list_logs` - View production logs
- `mcp__render__get_metrics` - Monitor performance
- `mcp__render__update_environment_variables` - Update env vars (triggers redeploy)

## Debugging Notes

- Use FastMCP docs at https://gofastmcp.com/llms.txt when debugging FastMCP issues
- Redis cache prevents hitting Sleeper API rate limits for player data
- Player search functions use cached data for instant responses
- Redis uses LRU eviction policy for optimal cache management within free tier limits