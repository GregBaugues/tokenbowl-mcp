# Token Bowl MCP Server

[![CI](https://github.com/GregBaugues/tokenbowl-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/GregBaugues/tokenbowl-mcp/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

A Model Context Protocol (MCP) server for the Token Bowl fantasy football league, built with [FastMCP](https://github.com/jlowin/fastmcp) and the [Sleeper Fantasy Sports API](https://docs.sleeper.app/).

## Quick Start

### Use the Hosted Server (Recommended)

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

## Run Your Own Instance

```bash
# Clone and setup
git clone https://github.com/GregBaugues/tokenbowl-mcp.git
cd tokenbowl-mcp
uv sync

# Run for Claude Desktop
uv run python sleeper_mcp.py

# Run as web server
uv run python sleeper_mcp.py http
```

## Configuration

Create a `.env` file:

```bash
# Your Sleeper league ID (defaults to Token Bowl)
SLEEPER_LEAGUE_ID=1266471057523490816

# Optional: Redis for caching
REDIS_URL=redis://localhost:6379

# Optional: Fantasy Nerds API for enhanced analytics
FFNERD_API_KEY=your_api_key_here
```

## Available Tools

The server provides 27 MCP tools for fantasy football operations:

### League Operations
- `get_league_info` - League settings and configuration
- `get_league_rosters` - All team rosters
- `get_roster` - Detailed roster with player data
- `get_league_users` - League participants
- `get_league_matchups` - Weekly matchups
- `get_league_transactions` - Trades and waivers
- `get_league_winners_bracket` - Playoff brackets

### Player Data
- `search_players_by_name` - Find players by name
- `get_player_by_sleeper_id` - Get player details
- `get_trending_players` - Trending adds/drops
- `get_player_stats_all_weeks` - Season stats
- `get_waiver_wire_players` - Available free agents
- `get_waiver_analysis` - Waiver recommendations

### Utility
- `get_nfl_schedule` - Weekly game schedule
- `health_check` - Server status

## Development

```bash
# Run tests
uv run pytest

# Lint and format
uv run ruff check .
uv run ruff format .

# Clear cache
uv run python clear_cache.py
```

See [CLAUDE.md](CLAUDE.md) for detailed development instructions.

## Project Structure

The codebase is modular and well-organized for maintainability:

```
sleeper-mcp/
├── sleeper_mcp.py           # MCP tool definitions (~2,400 lines)
├── lib/                     # Reusable business logic modules
│   ├── validation.py        # Parameter validation utilities
│   ├── decorators.py        # MCP tool decorator (logging, error handling)
│   ├── enrichment.py        # Player data enrichment functions
│   └── league_tools.py      # League operation business logic
├── cache_client.py          # Cache interface for player data
├── build_cache.py           # Cache building and refreshing
├── scripts/                 # Utility scripts
├── tests/                   # Comprehensive test suite (166 tests)
├── data/                    # Data files and analyses
├── picks/                   # Weekly picks
├── slopups/                 # Weekly summaries
└── scratchpads/             # Development notes
```

### Architecture Highlights

**Modular Design**: Business logic is extracted into focused modules for:
- **Validation** - Reusable parameter validation across all tools
- **Enrichment** - Player data enrichment with stats, projections, trending data
- **League Operations** - Complex league business logic (rosters, matchups, transactions)
- **Decorators** - Shared logging and error handling patterns

**Separation of Concerns**: MCP tools in `sleeper_mcp.py` are thin wrappers that:
1. Define tool interfaces and documentation
2. Validate parameters using `lib.validation`
3. Call business logic from `lib/` modules
4. Return formatted responses

**Testability**: Business logic in `lib/` modules can be unit tested independently of MCP framework integration.

## License

MIT

---

Built with ❤️ for my Tokenbowl Friends