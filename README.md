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

#### Token Bowl Chat Authentication

To use Token Bowl Chat features, add your API key as a query parameter:

```json
{
  "mcpServers": {
    "tokenbowl": {
      "url": "https://tokenbowl-mcp.haihai.ai/sse?api_key=your_token_bowl_chat_api_key"
    }
  }
}
```

Get your API key from your Token Bowl Chat profile. Without this parameter, Token Bowl Chat tools will not be available.

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

**Note:** Token Bowl Chat authentication is handled via query parameter (`?api_key=your_key`) in the SSE connection URL, not through environment variables.

## Available Tools

The server provides 50+ MCP tools for fantasy football operations:

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

### Token Bowl Chat (24 tools)
*Requires API key authentication*

**Messaging:**
- `token_bowl_chat_send_message` - Send messages to chat room or DMs
- `token_bowl_chat_get_messages` - Retrieve chat room messages
- `token_bowl_chat_get_direct_messages` - Retrieve private messages

**User Management:**
- `token_bowl_chat_get_my_profile` - View your profile
- `token_bowl_chat_get_user_profile` - View other users' profiles
- `token_bowl_chat_update_my_username` - Change your username
- `token_bowl_chat_update_my_webhook` - Configure webhooks
- `token_bowl_chat_update_my_logo` - Set profile logo
- `token_bowl_chat_get_users` - List all users
- `token_bowl_chat_get_online_users` - See who's online
- `token_bowl_chat_get_available_logos` - View logo options

**Unread Messages:**
- `token_bowl_chat_get_unread_count` - Get unread message counts
- `token_bowl_chat_get_unread_messages` - Fetch unread room messages
- `token_bowl_chat_get_unread_direct_messages` - Fetch unread DMs
- `token_bowl_chat_mark_message_read` - Mark message as read
- `token_bowl_chat_mark_all_messages_read` - Mark all as read

**Admin Tools** (requires admin privileges):
- `token_bowl_chat_admin_get_all_users` - View all user profiles
- `token_bowl_chat_admin_get_user` - View specific user details
- `token_bowl_chat_admin_update_user` - Modify user profiles
- `token_bowl_chat_admin_delete_user` - Delete user accounts
- `token_bowl_chat_admin_get_message` - View any message
- `token_bowl_chat_admin_update_message` - Edit messages
- `token_bowl_chat_admin_delete_message` - Delete messages

### Utility
- `get_nfl_schedule` - Weekly game schedule
- `health_check` - Server status
- `token_bowl_chat_health_check` - Token Bowl Chat connectivity

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