# Token Bowl MCP Server

[![CI](https://github.com/GregBaugues/tokenbowl-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/GregBaugues/tokenbowl-mcp/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A high-performance Model Context Protocol (MCP) server for the Token Bowl fantasy football league. Built with [FastMCP](https://github.com/jlowin/fastmcp) and the [Sleeper Fantasy Sports API](https://docs.sleeper.app/), this server provides seamless access to league data, player statistics, and real-time updates through a standardized MCP interface.

## 🎯 Key Features

- **🏈 Comprehensive League Management**: Access league info, rosters, matchups, transactions, and playoff brackets
- **👤 User Analytics**: Track user profiles, leagues, and draft history across seasons
- **📊 Player Intelligence**: Real-time NFL player data with Redis caching for instant searches
- **📈 Trending Analysis**: Monitor trending adds/drops with customizable lookback periods
- **🎲 Draft Tools**: Complete draft history, picks, and traded picks tracking
- **⚡ High Performance**: Redis-cached player data with 24-hour TTL and automatic refresh
- **🔄 Dual Transport**: Supports both STDIO (Claude Desktop) and HTTP/SSE (web deployment)
- **☁️ Production Ready**: Auto-deploys to Render with built-in health checks

## 📋 Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Redis (for caching - optional for local development)
- Sleeper Fantasy Football league access

## 🚀 Quick Start

### Option 1: Use the Hosted Server (Recommended)

The easiest way to use Token Bowl MCP is through the hosted server. No installation required!

#### For Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "tokenbowl": {
      "url": "https://tokenbowl-mcp.haihai.ai/sse"
    }
  }
}
```

That's it! The server is already running and ready to use.

#### For Other MCP Clients

Connect your MCP client to:
```
https://tokenbowl-mcp.haihai.ai/sse
```

### Option 2: Run Your Own Instance

#### Installation

```bash
# Clone the repository
git clone https://github.com/GregBaugues/tokenbowl-mcp.git
cd tokenbowl-mcp

# Install dependencies using uv
uv sync

# For development with tests
uv sync --extra test

# For development with linting
uv sync --extra dev
```

#### Running the Server

##### For Claude Desktop (STDIO mode)
```bash
uv run python sleeper_mcp.py
```

##### For Web Deployment (HTTP/SSE mode)
```bash
# Default port 8000
uv run python sleeper_mcp.py http

# Custom port
uv run python sleeper_mcp.py http 3000
```

## 🔧 Configuration

### Environment Setup

For local development, create a `.env` file in the project root to configure environment variables:

```bash
# Copy the example template
cp .env.example .env

# Edit with your values
nano .env
```

Example `.env` file:
```bash
# Fantasy Nerds API Key (required for extended analytics)
FFNERD_API_KEY=your_api_key_here

# Sleeper League ID (optional, defaults to Token Bowl)
SLEEPER_LEAGUE_ID=1266471057523490816

# Redis URL (for production/caching)
REDIS_URL=redis://localhost:6379
```

**Note**: The `.env` file is automatically ignored by git and should never be committed to version control.

### Claude Desktop Integration

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "tokenbowl-local": {
      "command": "sh",
      "args": [
        "-c",
        "cd /path/to/tokenbowl-mcp && uv run python sleeper_mcp.py"
      ]
    }
  }
}
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FFNERD_API_KEY` | Fantasy Nerds API key for extended analytics | None (required for fantasy data) |
| `SLEEPER_LEAGUE_ID` | Sleeper league ID to use | `1266471057523490816` (Token Bowl) |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` |
| `PORT` | HTTP server port (Render) | `8000` |
| `RENDER` | Deployment flag | `false` |

### Redis Cache Configuration

The server uses Redis to cache NFL player data (5MB+ dataset) with intelligent filtering:
- **Cache TTL**: 24 hours with automatic refresh
- **Compression**: Gzip compression (level 9) for memory efficiency
- **Smart Filtering**: Only caches active players with search rank < 5000
- **Memory Optimized**: Designed for free-tier Redis instances

## 📚 API Documentation

### League Operations (8 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_league_info()` | Get league settings and configuration | None |
| `get_league_rosters()` | Get all team rosters with players | None |
| `get_league_users()` | Get all league members | None |
| `get_league_matchups(week)` | Get matchups for specific week | `week: int` |
| `get_league_transactions(round)` | Get waiver/trade transactions | `round: int` (default: 1) |
| `get_league_traded_picks()` | Get all traded draft picks | None |
| `get_league_drafts()` | Get league draft history | None |
| `get_league_winners_bracket()` | Get playoff bracket | None |

### User Operations (3 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_user(username_or_id)` | Get user profile | `username_or_id: str` |
| `get_user_leagues(user_id, sport, season)` | Get user's leagues | `user_id: str`, `sport: str`, `season: str` |
| `get_user_drafts(user_id, sport, season)` | Get user's draft history | `user_id: str`, `sport: str`, `season: str` |

### Player Operations (5 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_nfl_players()` | Get all NFL players (cached) | None |
| `search_player_by_name(name)` | Search players by name | `name: str` |
| `get_player_by_sleeper_id(player_id)` | Get specific player | `player_id: str` |
| `get_trending_players(type, lookback_hours, limit)` | Get trending adds/drops | `type: str`, `lookback_hours: int`, `limit: int` |
| `get_players_cache_status()` | Check cache health | None |
| `refresh_players_cache()` | Force cache refresh | None |

### Draft Operations (3 tools)
#### (Now commented out, to reduce tool pollution)

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_draft(draft_id)` | Get draft details | `draft_id: str` |
| `get_draft_picks(draft_id)` | Get all draft picks | `draft_id: str` |
| `get_draft_traded_picks(draft_id)` | Get traded draft picks | `draft_id: str` |

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=. --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_sleeper_mcp.py

# Run linting
uv run ruff check .
uv run ruff format .
```

## 🚢 Deployment

### Deploy to Render

1. Fork this repository
2. Connect GitHub to Render
3. Create a new Web Service
4. Select your forked repository
5. Render auto-detects `render.yaml` configuration
6. Add Redis instance (optional but recommended)
7. Deploy!

The service will be available at:
```
https://your-service-name.onrender.com/sse
```



### Project Structure

```
tokenbowl-mcp/
├── sleeper_mcp.py           # Main MCP server
├── players_cache_redis.py   # Redis caching layer
├── tests/
│   ├── test_sleeper_mcp.py  # Server tests
│   ├── test_players_cache.py # Cache tests
│   └── test_integration.py  # Integration tests
├── render.yaml              # Render deployment config
├── pyproject.toml           # Python dependencies
└── .github/
    └── workflows/
        └── ci.yml           # GitHub Actions CI/CD
```

### Utility Scripts

```bash
# Clear Redis cache
uv run python clear_cache.py

# Debug Redis connection
uv run python debug_redis.py
```


### Development Guidelines

- Write tests for new features
- Follow Python best practices and PEP 8
- Use type hints where appropriate
- Update documentation for API changes
- Ensure CI passes before submitting PR


## 🙏 References

- [Sleeper](https://sleeper.app/) for their comprehensive fantasy sports API
- [FastMCP](https://github.com/jlowin/fastmcp) for the excellent MCP framework



## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/GregBaugues/tokenbowl-mcp/issues)

- **API Docs**: [Sleeper API Documentation](https://docs.sleeper.app/)



**Note**: By default, this server uses the Token Bowl league (ID: `1266471057523490816`). To use with your own league, set the `SLEEPER_LEAGUE_ID` environment variable to your league's ID.

Built with ❤️ for the fantasy football community