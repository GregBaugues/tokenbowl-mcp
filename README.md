# Sleeper MCP Server

[![CI](https://github.com/GregBaugues/sleeper-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/GregBaugues/sleeper-mcp/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

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
git clone https://github.com/GregBaugues/sleeper-mcp.git
cd sleeper-mcp

# Install dependencies using uv
uv sync
```

## Usage

### Running as HTTP Server (Streamable)

Start the server on default port 8000:
```bash
uv run python sleeper_mcp.py http
```

Or specify a custom port:
```bash
uv run python sleeper_mcp.py http 3000
```

### Running with STDIO (for Claude Desktop)

```bash
uv run python sleeper_mcp.py
```

## Configuration

### For Claude Desktop (STDIO)

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

### For HTTP/SSE Transport

Configure your MCP client to connect to:
```
http://localhost:8000/sse
```

The server uses Server-Sent Events (SSE) for streaming responses, making it compatible with web-based MCP clients and other HTTP-based integrations.

### Deploying to Render

1. Fork or clone this repository to your GitHub account
2. Connect your GitHub account to Render
3. Create a new Web Service on Render
4. Connect your repository
5. Render will automatically detect the `render.yaml` configuration
6. Deploy!

Your MCP server will be available at:
```
https://your-service-name.onrender.com/sse
```

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