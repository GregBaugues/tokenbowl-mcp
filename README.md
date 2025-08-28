# Sleeper MCP Server

A Model Context Protocol (MCP) server for the Sleeper Fantasy Sports API built with FastMCP.

## Features

This MCP server provides tools to interact with the Sleeper API, hardcoded for a specific league. Available tools include:

- League information and rosters
- User data and matchups  
- Transactions and traded picks
- NFL player data and trending players
- Draft information

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/sleeper-mcp.git
cd sleeper-mcp

# Install dependencies using uv
uv sync
```

## Configuration for Claude Desktop

Add to your Claude Desktop config file (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "sleeper": {
      "command": "sh",
      "args": [
        "-c",
        "cd /path/to/sleeper-mcp && uv run python sleeper_mcp.py"
      ]
    }
  }
}
```

Then restart Claude Desktop to load the server.

## Available Tools

### League Tools
- `get_league_info()` - Get league information
- `get_league_rosters()` - Get all rosters
- `get_league_users()` - Get all users
- `get_league_matchups(week)` - Get matchups for a week
- `get_league_transactions(round)` - Get transactions
- `get_league_traded_picks()` - Get traded picks
- `get_league_drafts()` - Get league drafts
- `get_league_winners_bracket()` - Get playoff bracket

### User Tools
- `get_user(username_or_id)` - Get user info
- `get_user_leagues(user_id, sport, season)` - Get user's leagues
- `get_user_drafts(user_id, sport, season)` - Get user's drafts

### Player Tools
- `get_nfl_players()` - Get all NFL players
- `get_trending_players(type, lookback_hours, limit)` - Get trending players

### Draft Tools
- `get_draft(draft_id)` - Get draft details
- `get_draft_picks(draft_id)` - Get draft picks
- `get_draft_traded_picks(draft_id)` - Get traded picks

## License

MIT