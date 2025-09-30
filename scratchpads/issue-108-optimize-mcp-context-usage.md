# Issue #108: Optimize MCP tool data returns to reduce context usage

**Issue URL**: https://github.com/GregBaugues/sleeper-mcp/issues/108

## Overview

Reduce token usage by 20-30% through selective data reduction and optional enrichment parameters. This issue identifies 6 specific optimizations based on comprehensive testing of all 27 MCP tools.

## Implementation Plan

### Phase 1: Player Enrichment Cleanup (High Priority)

**Goal**: Remove ~30% tokens per player object by eliminating unused fields

**Files to modify**:
- `lib/enrichment.py` - `enrich_player_basic()`, `enrich_player_full()`, `enrich_player_minimal()`

**Fields to remove** (from Sleeper API data that we cache):
1. `search_full_name` - Search internal, not user-facing
2. `search_first_name` - Search internal, not user-facing
3. `search_last_name` - Search internal, not user-facing
4. `hashtag` - Unique identifier but unused in our context
5. `team_abbr` - Always null, redundant with `team`
6. `depth_chart_position` - Too granular ("LWR" vs just "WR")
7. `team_changed_at` - Rarely relevant

**Impact**: Affects all tools that return player data (get_roster, get_waiver_wire_players, get_trending_players, search_players_by_name, etc.)

**Testing**:
- Ensure tests still pass after field removal
- Verify no tools depend on removed fields

### Phase 2: News Deduplication (High Priority)

**Goal**: Reduce 200-400 tokens per roster call

**Problem**: News arrays contain duplicates (e.g., Ricky Pearsall had 3 identical items)

**Files to modify**:
- `lib/enrichment.py` - `enrich_player_injury_news()`

**Solution**: Deduplicate news items by headline or limit to 1 most recent per player

**Implementation**:
```python
def enrich_player_injury_news(player_data: Dict[str, Any], max_news: int = 3) -> Dict[str, Any]:
    # ... existing code ...

    if enriched_data.get("news") and len(enriched_data["news"]) > 0:
        # Deduplicate by headline
        seen_headlines = set()
        unique_news = []
        for item in enriched_data["news"]:
            headline = item.get("headline", "")
            if headline and headline not in seen_headlines:
                seen_headlines.add(headline)
                unique_news.append(item)

        # Include latest N unique news items
        enrichment["news"] = unique_news[:max_news]
```

**Testing**:
- Test with players that have duplicate news
- Verify only unique headlines are returned
- Ensure max_news limit is respected

### Phase 3: get_trending_players Parameters (High Priority)

**Goal**: Reduce 1200+ tokens for typical usage via filtering

**Files to modify**:
- `sleeper_mcp.py` - `get_trending_players()`

**Add parameters**:
1. `limit: int = 10` (default: 10, max: 25) - Currently always returns 25
2. `position: Optional[str] = None` - Filter by QB/RB/WR/TE/DEF/K

**Implementation**:
```python
@mcp.tool()
@log_mcp_tool
async def get_trending_players(
    type: str = "add",
    limit: int = 10,
    position: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get trending NFL players based on recent add/drop activity.

    Args:
        type: Transaction type to track (default: "add")
        limit: Maximum number of players to return (default: 10, max: 25)
        position: Filter by position (QB, RB, WR, TE, DEF, K). None returns all.

    ...
    """
    # Validate parameters
    if type not in ["add", "drop"]:
        return create_error_response(...)

    try:
        limit = validate_limit(limit, default=10, max=25)
    except ValueError as e:
        return create_error_response(...)

    if position:
        try:
            position = validate_position(position)
        except ValueError as e:
            return create_error_response(...)

    # Fetch trending players from API
    # ... existing API call ...

    # Filter by position if requested
    if position:
        trending_items = [
            item for item in trending_items
            if player_data.get(item["player_id"], {}).get("position") == position
        ]

    # Apply limit
    trending_items = trending_items[:limit]

    # Enrich and return
    # ... existing enrichment logic ...
```

**Testing**:
- Test default limit (10)
- Test custom limit
- Test max limit enforcement (25)
- Test position filtering for each position
- Test position filtering with limit
- Test invalid position handling

### Phase 4: get_league_info Restructuring (High Priority)

**Goal**: Better UX with clearer data structure

**Files to modify**:
- `lib/league_tools.py` - `fetch_league_info()`

**Current**: Returns 50+ raw Sleeper fields directly

**New structure**:
```python
{
    "name": "Token Bowl - the first LLM powered fantasy league",
    "season": "2025",
    "status": "in_season",
    "current_week": 4,
    "num_teams": 10,
    "scoring_type": "ppr",
    "roster_requirements": {
        "starters": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX", "K", "DEF"],
        "bench_slots": 5,
        "total_roster": 15
    },
    "playoffs": {
        "teams": 6,
        "start_week": 15
    },
    "waivers": {
        "type": "rolling",
        "clear_days": 2,
        "day_of_week": 2
    },
    "trade_deadline": 11,
    "settings": { /* move detailed settings here */ }
}
```

**Testing**:
- Verify all essential info is surfaced
- Ensure backward compatibility if needed
- Test with actual league data

### Phase 5: get_league_rosters Optimization (High Priority)

**Goal**: Reduce 600 tokens for summary use cases

**Files to modify**:
- `sleeper_mcp.py` - `get_league_rosters()`

**Add parameter**:
- `include_details: bool = False`

**Implementation**:
```python
@mcp.tool()
@log_mcp_tool
async def get_league_rosters(include_details: bool = False) -> List[Dict[str, Any]]:
    """Get all team rosters in the Token Bowl league.

    Args:
        include_details: If True, include full player ID arrays.
                        If False, return only summary info (default).

    Returns roster information for each team including:
    - Roster ID and owner user ID (always)
    - Wins, losses, ties, points for/against (always)
    - Waiver position (always)
    - Player ID arrays (only if include_details=True)
    ...
    """
    # Fetch rosters
    # ... existing API call ...

    if not include_details:
        # Return minimal roster info
        return [
            {
                "roster_id": r.get("roster_id"),
                "owner_id": r.get("owner_id"),
                "wins": r.get("settings", {}).get("wins", 0),
                "losses": r.get("settings", {}).get("losses", 0),
                "ties": r.get("settings", {}).get("ties", 0),
                "points_for": r.get("settings", {}).get("fpts", 0),
                "points_against": r.get("settings", {}).get("fpts_against", 0),
                "waiver_position": r.get("settings", {}).get("waiver_position"),
            }
            for r in rosters
        ]

    # Return full roster data
    return rosters
```

**Testing**:
- Test with include_details=False (default)
- Test with include_details=True
- Verify token reduction in minimal mode

### Phase 6: get_league_matchups Enrichment (Medium Priority)

**Goal**: Eliminate need for 30+ follow-up player lookups

**Files to modify**:
- `lib/league_tools.py` - `fetch_league_matchups()`
- `sleeper_mcp.py` - `get_league_matchups()`

**Add parameter**:
- `enrich_players: bool = False`

**Implementation**:
```python
@mcp.tool()
@log_mcp_tool
async def get_league_matchups(week: int, enrich_players: bool = False) -> List[Dict[str, Any]]:
    """Get head-to-head matchups for a specific week.

    Args:
        week: The NFL week number (1-18)
        enrich_players: If True, include player names/positions inline.
                       If False, return only player IDs (default).
    ...
    """
    from lib.league_tools import fetch_league_matchups

    # Validate week
    try:
        week = validate_week(week)
    except ValueError as e:
        return create_error_response(...)

    return await fetch_league_matchups(
        LEAGUE_ID,
        BASE_URL,
        week,
        enrich_players=enrich_players
    )
```

In `lib/league_tools.py`:
```python
async def fetch_league_matchups(
    league_id: str,
    base_url: str,
    week: int,
    enrich_players: bool = False
) -> List[Dict[str, Any]]:
    # Fetch matchups
    # ... existing API call ...

    if enrich_players:
        # Get player cache
        player_data = await get_players_from_cache()

        # Enrich starters and players_points
        for matchup in matchups:
            if matchup.get("starters"):
                matchup["starters"] = [
                    {
                        "player_id": pid,
                        "name": player_data.get(pid, {}).get("full_name", "Unknown"),
                        "position": player_data.get(pid, {}).get("position"),
                    }
                    for pid in matchup["starters"]
                ]
            # Similar for players_points

    return matchups
```

**Testing**:
- Test with enrich_players=False (default)
- Test with enrich_players=True
- Verify player enrichment is correct
- Test with missing player data

## Testing Strategy

### Unit Tests
1. Test each modified function individually
2. Test parameter validation for new parameters
3. Test edge cases (empty data, missing fields, etc.)

### Integration Tests
1. Test full MCP tool calls with new parameters
2. Verify backward compatibility where applicable
3. Test token usage reduction (measure before/after)

### Regression Tests
1. Run full test suite after each phase
2. Verify no existing functionality is broken
3. Check that all 166 existing tests still pass

## Implementation Order

1. **Phase 1** (Player Enrichment Cleanup) - Foundation for all other work
2. **Phase 2** (News Deduplication) - High impact, low risk
3. **Phase 3** (get_trending_players) - High impact, moderate complexity
4. **Phase 4** (get_league_info) - Moderate impact, low risk
5. **Phase 5** (get_league_rosters) - High impact for summary use cases
6. **Phase 6** (get_league_matchups) - Optional, lower priority

## Estimated Impact

- **Token Reduction**: 20-30% across common operations
- **Improved UX**: Clearer data structures, better filtering options
- **Breaking Changes**: Minimal (most changes are additive with defaults maintaining backward compatibility)

## Notes

- All parameter additions should maintain backward compatibility by using sensible defaults
- Document all new parameters in tool docstrings
- Update tests to cover new functionality
- Consider adding integration tests that measure token usage before/after
