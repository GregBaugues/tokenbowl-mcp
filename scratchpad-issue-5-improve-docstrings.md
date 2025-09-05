# Issue #5: Improve MCP Tool Docstrings and Descriptions

## GitHub Issue
https://github.com/GregBaugues/sleeper-mcp/issues/5

## Problem Statement
- Current MCP tool docstrings are too brief and don't provide enough context for models
- Better descriptions will reduce errors when models use the tools
- Need to update default season from 2024 to 2025

## Sleeper API Reference Review
Based on https://docs.sleeper.com/:
- Read-only HTTP API, no auth required
- Rate limit: < 1000 calls/minute
- Main endpoints: User, League, Draft, Player, NFL State

## Implementation Plan

### 1. League Operations (8 tools)
- `get_league_info()` - Add details about league structure, settings
- `get_league_rosters()` - Clarify roster structure, player IDs, settings
- `get_league_users()` - Explain user-roster relationship
- `get_league_matchups()` - Detail week parameter (1-18), matchup structure
- `get_league_transactions()` - Explain round parameter, transaction types
- `get_league_traded_picks()` - Clarify draft pick trading mechanics
- `get_league_drafts()` - Describe draft information returned
- `get_league_winners_bracket()` - Detail playoff bracket structure

### 2. User Operations (3 tools)
- `get_user()` - Explain username vs user_id parameter
- `get_user_leagues()` - Update season default to 2025, explain sport options
- `get_user_drafts()` - Update season default to 2025, clarify draft types

### 3. Player Operations (5 tools)
- `get_nfl_players()` - Warn about large dataset, caching strategy
- `search_player_by_name()` - Detail search algorithm, partial matches
- `get_player_by_sleeper_id()` - Explain Sleeper player ID format
- `get_trending_players()` - Detail type options (add/drop), time windows
- Cache operations - Explain caching strategy, TTL, refresh

### 4. Draft Operations (3 tools)
- `get_draft()` - Describe draft metadata structure
- `get_draft_picks()` - Detail pick information, player selections
- `get_draft_traded_picks()` - Explain draft pick trading

### 5. Season Updates
- Change default season from "2024" to "2025" in:
  - `get_user_leagues()`
  - `get_user_drafts()`

## Key Improvements for Each Docstring
1. Add comprehensive description of what the tool does
2. Explain all parameters with valid options
3. Describe return structure
4. Note any limitations or best practices
5. Include examples where helpful
6. Specify data types clearly

## Testing Strategy
1. Run the MCP server locally
2. Verify all tools still function correctly
3. Check that docstrings display properly in MCP tool list
4. Test with a model to ensure improved understanding

## Success Criteria
- All 20 MCP tools have detailed, helpful docstrings
- Default season is 2025
- Models can understand tool purpose without external documentation
- Fewer errors when models use the tools