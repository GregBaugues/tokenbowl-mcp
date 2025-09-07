# Issue #42: Refactor Player Stats Structure in Cache

GitHub Issue: https://github.com/GregBaugues/sleeper-mcp/issues/42

## Problem Analysis

The current player stats structure has several issues:

1. **Inconsistent Structure**: `current_week_stats` only exists for players who have already played
2. **Nested Hierarchy**: Projections are nested under `data` while actual stats are at root level
3. **Field Name Inconsistency**: `proj_pts` vs `pts_ppr` 
4. **No Game Status**: No clear indication if game is not started, in progress, or final
5. **Unclear Data Priority**: When both projections and actual stats exist

## Current Structure
```json
{
  "player_id": "4046",
  "name": "Patrick Mahomes",
  "data": {
    "projections": {
      "proj_pts": "18.40",
      "proj_pts_low": "16.93", 
      "proj_pts_high": "22.00"
    }
  },
  "current_week_stats": {  // ONLY EXISTS IF PLAYER HAS PLAYED
    "pts_ppr": 26.02,
    "pass_yd": 258.0,
    "pass_td": 1.0,
    "rush_yd": 57.0,
    "rush_td": 1.0
  }
}
```

## Proposed Structure
```json
{
  "player_id": "4046", 
  "name": "Patrick Mahomes",
  "stats": {
    "projected": {
      "fantasy_points": 18.40,
      "fantasy_points_low": 16.93,
      "fantasy_points_high": 22.00
    },
    "actual": {  // NULL if player hasn't played
      "fantasy_points": 26.02,
      "game_stats": {
        "passing_yards": 258.0,
        "passing_touchdowns": 1.0,
        "rushing_yards": 57.0,
        "rushing_touchdowns": 1.0
      },
      "game_status": "final"  // "not_started", "in_progress", or "final"
    }
  }
}
```

## Implementation Plan

### 1. Files to Modify

#### A. `build_cache.py`
- **Lines 375-416**: `enrich_and_filter_players()` function
  - Change how stats and projections are structured
  - Always include both `projected` and `actual` objects
  - Set `actual` to `null` if no stats exist
  - Add game status determination logic

- **Lines 56-131**: `filter_ppr_relevant_stats()` function
  - Update field names to be more descriptive
  - Add game status tracking

#### B. `cache_client.py`
- No direct changes needed initially, as it just passes through the data
- May need updates if we add convenience methods for accessing the new structure

#### C. `sleeper_mcp.py`
- **Lines 206-254**: In `get_roster()` tool where player data is enriched
  - Update to read from new `stats.projected` structure instead of `data.projections`
  - Handle the new stats structure when displaying player info

#### D. `test_stats_integration.py`
- Update all test assertions to use new structure:
  - Change `current_week_stats` to `stats.actual`
  - Update field names (e.g., `pass_yd` to `passing_yards`)

### 2. Migration Strategy

Since the cache has a 6-hour TTL and auto-refreshes on miss:
1. Deploy the new structure
2. Old cache entries will expire naturally
3. New requests will trigger refresh with new structure
4. No explicit migration needed due to short TTL

### 3. Field Mapping

| Old Field | New Field |
|-----------|-----------|
| `data.projections.proj_pts` | `stats.projected.fantasy_points` |
| `data.projections.proj_pts_low` | `stats.projected.fantasy_points_low` |
| `data.projections.proj_pts_high` | `stats.projected.fantasy_points_high` |
| `current_week_stats.pts_ppr` | `stats.actual.fantasy_points` |
| `current_week_stats.pass_yd` | `stats.actual.game_stats.passing_yards` |
| `current_week_stats.pass_td` | `stats.actual.game_stats.passing_touchdowns` |
| `current_week_stats.rush_yd` | `stats.actual.game_stats.rushing_yards` |
| `current_week_stats.rush_td` | `stats.actual.game_stats.rushing_touchdowns` |
| `current_week_stats.rec` | `stats.actual.game_stats.receptions` |
| `current_week_stats.rec_yd` | `stats.actual.game_stats.receiving_yards` |
| `current_week_stats.rec_td` | `stats.actual.game_stats.receiving_touchdowns` |

### 4. Game Status Logic

Determine game status based on:
- If no stats exist → `"not_started"`
- If stats exist and game is complete → `"final"`
- If stats exist but game is ongoing → `"in_progress"`

Note: May need to fetch current NFL state to determine if games are in progress

### 5. Testing Plan

1. Test with player who hasn't played (should have `actual: null`)
2. Test with player who has completed game (should have full `actual` data)
3. Test that all tools still work with new structure
4. Verify backward compatibility during cache transition
5. Run existing test suite and update assertions

### 6. Benefits of New Structure

- **Consistent**: Always same structure regardless of game status
- **Clear**: Obvious separation between projected and actual
- **Extensible**: Easy to add more stat types or metadata
- **Descriptive**: Full field names are self-documenting
- **Status-aware**: Game status helps UI decisions

## Next Steps

1. Create new git branch `issue-42-stats-refactor`
2. Update `build_cache.py` to create new structure
3. Update `sleeper_mcp.py` to read from new structure
4. Update tests to expect new structure
5. Test locally with cache refresh
6. Create PR for review