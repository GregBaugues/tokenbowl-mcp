# Token Bowl MCP Tools Quick Reference

Essential MCP tools for fantasy football analysis. All tools prefixed with `mcp__tokenbowl__` when used in Claude.

## Core Roster & League Tools

### `get_roster(roster_id)`
Get complete roster with all players, projections, and current week number.
```python
get_roster(roster_id=2)  # Bill Beliclaude's roster
# Returns: starters, bench, week number, player details with projections
```

### `get_league_rosters(include_details=False)`
Get all team rosters with records and standings.
```python
get_league_rosters(include_details=False)  # Summary only (default)
# Returns: roster_id, wins/losses, points_for, points_against, waiver_position
```

### `get_league_users()`
Map roster IDs to team owners and names.
```python
get_league_users()
# Returns: user_id, username, display_name, team_name
```

### `get_league_matchups(week)`
Get head-to-head matchups for a specific week.
```python
get_league_matchups(week=7)
# Returns: roster_ids, points, player_points breakdown
```

## Player Search & Analysis Tools

### `search_players_by_name(name)`
Search for players by name (unified Sleeper + Fantasy Nerds data).
```python
search_players_by_name(name="Jefferson")
# Returns: Top 10 matches with projections, ADP, injury status
```

### `get_player_by_sleeper_id(player_id)`
Get complete player data by Sleeper ID.
```python
get_player_by_sleeper_id(player_id="4046")  # Patrick Mahomes
# Returns: All Sleeper data + Fantasy Nerds enrichment
```

### `get_player_stats_all_weeks(player_id, season=None)`
Get real game stats for all weeks of a season.
```python
get_player_stats_all_weeks(player_id="4046", season="2024")
# Returns: Week-by-week stats, season totals, games played
```

## Waiver Wire Tools

### `get_waiver_analysis(position=None, days_back=7, limit=20)` ⭐
**USE THIS FIRST** - Consolidated waiver analysis with minimal context.
```python
get_waiver_analysis(position="RB", days_back=7, limit=20)
# Returns: Recently dropped players, trending available, priority position
```

### `get_waiver_wire_players(position=None, limit=50, include_stats=False)`
Get all available free agents not on any roster.
```python
get_waiver_wire_players(position="DEF", limit=10, include_stats=True)
# Returns: Available players with optional full stats/projections
```

### `get_trending_players(type="add", limit=10, position=None)`
Get players trending across all Sleeper leagues.
```python
get_trending_players(type="add", limit=25, position="RB")
# Returns: Players with add/drop counts from last 24 hours
```

### `get_recent_transactions(limit=20, drops_only=False)`
Get most recent league transactions.
```python
get_recent_transactions(limit=20, drops_only=True, max_days_ago=14)
# Returns: Recent adds/drops sorted by recency
```

## Decision Support Tools

### `evaluate_waiver_priority_cost(current_position, projected_points_gain, weeks_remaining)`
Calculate if using waiver priority is worth it.
```python
evaluate_waiver_priority_cost(current_position=3, projected_points_gain=5, weeks_remaining=10)
# Returns: recommended_action, expected_value, break_even_threshold
```

### `its_monday_night_and_i_need_a(position)`
Emergency waiver tool for Monday night replacements.
```python
its_monday_night_and_i_need_a(position="RB")
# Returns: Top 3 available players at position who haven't played yet
```

## Context & Schedule Tools

### `get_league_info()`
Get league settings and current status.
```python
get_league_info()
# Returns: League name, season, week, scoring settings, playoff config
```

### `get_nfl_schedule(week=None)`
Get NFL game schedule for a specific week.
```python
get_nfl_schedule(week=7)  # Or None for current week
# Returns: Games, times, teams, scores (if complete)
```

### `get_league_transactions(round)`
Get waiver and trade transactions for a specific round.
```python
get_league_transactions(round=5)
# Returns: Transaction details with enriched player data
```

## Research Tools (Use via Web)

### `WebSearch(query)`
Search web for player news, injuries, analysis.
```python
WebSearch(query="Josh Allen injury status week 7 2024")
# Use for: injury updates, usage trends, expert analysis
```

### `WebFetch(url, prompt)`
Fetch and analyze specific articles.
```python
WebFetch(url="https://...", prompt="Summarize injury impact on player value")
# Use for: Deep dive on specific articles from search results
```

## Efficiency Tips

1. **Start with consolidated tools**: Use `get_waiver_analysis()` instead of multiple separate calls
2. **Minimize context**: Use `include_details=False` and `include_stats=False` when possible
3. **Delegate to subagents**: Let subagents handle data-heavy operations
4. **Cache player data**: Player info updates daily, avoid repeated searches
5. **Batch operations**: Get all rosters once, then filter locally
