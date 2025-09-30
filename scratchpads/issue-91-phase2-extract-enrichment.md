# Issue #91: Phase 2 - Extract Player Enrichment Utilities

**GitHub Issue**: [#91](https://github.com/GregBaugues/sleeper-mcp/issues/91)
**Parent Issue**: [#88](https://github.com/GregBaugues/sleeper-mcp/issues/88)
**Depends On**: #90 (Phase 1) - ✅ COMPLETED
**Author**: GregBaugues
**Phase**: 2 of 4 in refactoring plan
**Risk Level**: MEDIUM - Affects multiple complex tools with enrichment logic

## Objective

Extract common player data enrichment logic from multiple tools into reusable utility functions. This is the second step in reducing `sleeper_mcp.py` from 2,747 lines to ~800 lines.

## Current State Analysis

### File Size After Phase 1
- **sleeper_mcp.py**: 2,747 lines (down from 2,935)
- **lib/validation.py**: 191 lines ✅
- **lib/decorators.py**: ~120 lines ✅

### Enrichment Patterns Identified

After analyzing the code, I've identified these common enrichment patterns:

#### 1. **Player Data Enrichment** (Used in: get_roster, get_waiver_wire_players, get_player_stats_all_weeks)

**Current Pattern in get_roster (lines 227-361)**:
```python
for player_id in all_player_ids:
    player_data = all_players.get(player_id, {})

    # Build basic player info
    player_info = {
        "player_id": player_id,
        "name": player_data.get("full_name", f"{player_id} (Unknown)"),
        "position": player_data.get("position"),
        "team": player_data.get("team"),
        "status": player_data.get("status"),
    }

    # Handle team defenses
    if len(player_id) <= 3 and player_id.isalpha():
        player_info["name"] = f"{player_id} Defense"
        player_info["position"] = "DEF"
        player_info["team"] = player_id

    # Add stats from cache (projected, ros_projected, actual)
    player_stats = {"projected": None, "actual": None, "ros_projected": None}

    if "stats" in player_data:
        cached_stats = player_data["stats"]

        # Projected stats
        if cached_stats.get("projected"):
            proj = cached_stats["projected"]
            fantasy_points = proj.get("fantasy_points", 0)
            player_stats["projected"] = {
                "fantasy_points": round(fantasy_points, 2),
                "fantasy_points_low": round(proj.get("fantasy_points_low", fantasy_points), 2),
                "fantasy_points_high": round(proj.get("fantasy_points_high", fantasy_points), 2),
            }

        # ROS projected stats with position-specific stats
        if cached_stats.get("ros_projected"):
            ros = cached_stats["ros_projected"]
            player_stats["ros_projected"] = {
                "fantasy_points": round(ros.get("fantasy_points", 0), 2),
                "season": ros.get("season"),
            }

            # Add position-specific ROS stats (QB, RB/WR/TE)
            if player_data.get("position") == "QB":
                # passing yards, touchdowns, rushing yards, etc.
            elif player_data.get("position") in ["RB", "WR", "TE"]:
                # rushing yards, receiving yards, receptions, etc.

        # Actual stats
        if cached_stats.get("actual"):
            actual = cached_stats["actual"]
            player_stats["actual"] = {
                "fantasy_points": round(actual.get("fantasy_points", 0), 2),
                "game_status": actual.get("game_status", "unknown"),
                "game_stats": actual.get("game_stats"),
            }

    player_info["stats"] = player_stats

    # Add injury and news data
    if "data" in player_data:
        enriched = player_data["data"]
        if enriched.get("injury"):
            # injury status, description, last_update
        if enriched.get("news"):
            # latest 3 news items
```

**Similar Pattern in get_waiver_wire_players (lines 1531-1586)**:
- Minimal mode: only basic fields + projected_points
- Full mode: all player data with trending_add_count
- Checks both new and old stat locations for backward compatibility

#### 2. **Trending Data Enrichment** (Used in: get_waiver_wire_players, get_waiver_analysis)

**Current Pattern in get_waiver_wire_players (lines 1498-1508)**:
```python
trending_data = {}
try:
    trending_response = await get_trending_players.fn(type="add")
    trending_data = {item["player_id"]: item["count"] for item in trending_response}
except Exception as e:
    logger.warning(f"Could not fetch trending data...")

# Later: Add to each player
if player_id in trending_data:
    player_entry["trending_add_count"] = trending_data[player_id]
```

#### 3. **Recent Drops Detection** (Used in: get_waiver_wire_players, get_waiver_analysis)

**Current Pattern in get_waiver_wire_players (lines 1476-1493)**:
```python
recent_drops = set()
if highlight_recent_drops:
    try:
        recent_txns = await get_recent_transactions.fn(
            drops_only=True,
            max_days_ago=7,
            include_player_details=False,
            limit=50,
        )
        for txn in recent_txns:
            if txn.get("drops"):
                recent_drops.update(txn["drops"].keys())
    except Exception as e:
        logger.warning(f"Could not fetch recent drops...")

# Later: Mark player
if player_id in recent_drops:
    player_entry["recently_dropped"] = True
```

#### 4. **Roster Organization** (Used in: get_roster)

**Current Pattern in get_roster (lines 353-361)**:
```python
# Categorize player by roster position
if player_id in reserve_ids:
    enriched_roster["reserve"].append(player_info)
elif player_id in taxi_ids:
    enriched_roster["taxi"].append(player_info)
elif player_id in starters_ids:
    enriched_roster["starters"].append(player_info)
else:
    enriched_roster["bench"].append(player_info)
```

## Implementation Plan

### Functions to Create in lib/enrichment.py

#### 1. `enrich_player_basic(player_id: str, player_data: Dict) -> Dict`
Extract basic player info with defense handling.

#### 2. `enrich_player_stats(player_data: Dict, include_position_stats: bool = True) -> Dict`
Extract stats enrichment (projected, ros_projected, actual).

#### 3. `enrich_player_injury_news(player_data: Dict, max_news: int = 3) -> Dict`
Extract injury and news data.

#### 4. `enrich_player_full(player_id: str, player_data: Dict, include_position_stats: bool = True) -> Dict`
Combine all enrichment functions for full player enrichment.

#### 5. `enrich_player_minimal(player_id: str, player_data: Dict) -> Dict`
Minimal data mode (name, position, team, status, projected_points only).

#### 6. `async get_trending_data_map(type: str = "add") -> Dict[str, int]`
Fetch trending players and return as player_id -> count map.

#### 7. `async get_recent_drops_set(days_back: int = 7, limit: int = 50) -> Set[str]`
Fetch recent drops and return as set of player_ids.

#### 8. `add_trending_data(players: List[Dict], trending_map: Dict[str, int]) -> List[Dict]`
Add trending counts to player list.

#### 9. `mark_recent_drops(players: List[Dict], recent_drops_set: Set[str]) -> List[Dict]`
Mark players as recently dropped.

#### 10. `organize_roster_by_position(players: List[Dict], starters_ids: List, taxi_ids: List, reserve_ids: List) -> Dict`
Organize players into starters/bench/taxi/reserve categories.

## Detailed Task Breakdown

### Task 1: Create lib/enrichment.py

Create the enrichment module with all utility functions.

Key design decisions:
- Functions should work with the cache data structure
- Handle both new and old stat locations for backward compatibility
- Defensive error handling (don't fail if data is missing)
- Clear function names and comprehensive docstrings
- Type hints for all parameters and returns

### Task 2: Add Unit Tests

Create `tests/test_enrichment.py` with comprehensive coverage:
- Test each enrichment function independently
- Test with minimal player data
- Test with full player data
- Test with missing/None data
- Test defense handling
- Test stat calculations
- Test injury/news extraction
- Mock async functions (trending, recent drops)

### Task 3: Refactor get_roster

Replace enrichment logic (lines 227-361) with utility functions:
```python
# Before: ~135 lines of enrichment logic
# After: ~20 lines using utility functions

for player_id in all_player_ids:
    if not player_id:
        continue

    player_data = all_players.get(player_id, {})
    player_info = enrich_player_full(
        player_id,
        player_data,
        include_position_stats=True
    )

    # Track totals
    if player_info["stats"]["projected"]:
        fantasy_points = player_info["stats"]["projected"]["fantasy_points"]
        total_projected += fantasy_points
        if player_id in starters_ids:
            starters_projected += fantasy_points

# Organize into categories
categorized = organize_roster_by_position(
    all_enriched_players,
    starters_ids,
    taxi_ids,
    reserve_ids
)
enriched_roster.update(categorized)
```

### Task 4: Refactor get_waiver_wire_players

Replace enrichment logic (lines 1498-1586) with utility functions:
```python
# Fetch trending and drops data
trending_map = await get_trending_data_map(type="add")
recent_drops_set = await get_recent_drops_set(days_back=7) if highlight_recent_drops else set()

# Enrich players
for player_id, player_data in all_players.items():
    # Filtering logic stays the same

    # Enrichment becomes simpler
    if not include_stats:
        player_entry = enrich_player_minimal(player_id, player_data)
    else:
        player_entry = player_data  # Full mode

    available_players.append(player_entry)

# Add trending and drops
available_players = add_trending_data(available_players, trending_map)
available_players = mark_recent_drops(available_players, recent_drops_set)
```

### Task 5: Refactor get_waiver_analysis

Similar pattern to get_waiver_wire_players.

### Task 6: Refactor get_player_stats_all_weeks

Update to use enrichment utilities for player data.

## Files to Create

1. `lib/enrichment.py` (~400 lines)
2. `tests/test_enrichment.py` (~500 lines)

## Files to Modify

1. `sleeper_mcp.py` - Replace enrichment logic in 4 tools
2. `lib/__init__.py` - Add enrichment exports

## Expected Impact

### Lines of Code Changes

- **sleeper_mcp.py**: -300 to -400 lines (removing duplicate enrichment)
- **New lib/enrichment.py**: +400 lines (reusable code)
- **New tests**: +500 lines (comprehensive coverage)
- **Net change**: +600 lines total, but main file reduced by 300-400 lines

### After This Phase
- **sleeper_mcp.py**: ~2,350 lines (down from 2,747)

## Success Criteria

- ✓ `sleeper_mcp.py` reduced by 300-400 lines
- ✓ All enrichment logic is reusable across tools
- ✓ No duplicate enrichment code remains
- ✓ All existing tests pass
- ✓ New unit tests provide >90% coverage of enrichment functions
- ✓ Performance is maintained or improved
- ✓ Type hints are complete
- ✓ No breaking changes to MCP tool behavior

## Risk Mitigation

- MEDIUM RISK: Affects 4 complex tools with critical enrichment logic
- Test thoroughly before and after refactoring
- Ensure enrichment results match original behavior exactly
- Use async functions where needed (trending, recent drops)
- Handle backward compatibility for old stat locations
- Defensive error handling for missing data

## Testing Strategy

### Unit Tests (New)
- Test each enrichment function independently
- Mock cache data structures
- Test with various player data scenarios
- Test async functions with mocked responses

### Integration Tests (Existing)
- All existing tests must pass
- Verify enriched data matches original format
- Check that all tools still work correctly

### Manual Testing
- `get_roster(2)` - Verify full enrichment with stats
- `get_waiver_wire_players(limit=10)` - Check minimal mode
- `get_waiver_wire_players(limit=10, include_stats=True)` - Check full mode
- `get_waiver_analysis()` - Verify analysis with enrichment

## Commit Strategy

1. "Create lib/enrichment.py with basic enrichment utilities"
2. "Add unit tests for enrichment utilities"
3. "Refactor get_roster to use enrichment utilities"
4. "Refactor get_waiver_wire_players to use enrichment utilities"
5. "Refactor get_waiver_analysis to use enrichment utilities"
6. "Refactor get_player_stats_all_weeks to use enrichment utilities"
7. "Update lib/__init__.py exports"
8. "Run full test suite and verify"
9. "Run linting and formatting"

## Notes

- Keep backward compatibility with old stat locations
- Ensure defensive error handling throughout
- Maintain performance (avoid extra API calls)
- Keep enrichment functions pure where possible
- Document all data structure expectations

## Related Issues

- #88 - Parent issue: Cleanup codebase and plan for refactor
- #90 - Phase 1: Extract validation and decorator utilities (✅ COMPLETED)
- #92 - Phase 3: Extract business logic to lib/ modules
- #93 - Phase 4: Final cleanup and optimization