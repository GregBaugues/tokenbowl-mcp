# Issue #59: More Stats for Offensive Players

GitHub Issue: https://github.com/GregBaugues/sleeper-mcp/issues/59

## Problem Description
Include yards, receptions, carries, passing tds, rushing tds, for offensive players.
These will be pulled from the sleeper api and included in player cache.

## Current State Analysis

### Stats Already Being Tracked
After analyzing the codebase, ALL requested stats are ALREADY mapped in `filter_ppr_relevant_stats()`:

1. ✅ **Yards** - Already tracked:
   - `pass_yd` → `passing_yards`
   - `rush_yd` → `rushing_yards`
   - `rec_yd` → `receiving_yards`

2. ✅ **Receptions** - Already tracked:
   - `rec` → `receptions`

3. ✅ **Carries** - Already tracked (added in PR #56):
   - `rush_att` → `carries`

4. ✅ **Passing TDs** - Already tracked:
   - `pass_td` → `passing_touchdowns`

5. ✅ **Rushing TDs** - Already tracked:
   - `rush_td` → `rushing_touchdowns`

### Evidence from Cache Testing
Running test_find_players_with_stats.py showed players DO have these stats:
- James Cook: carries: 19, rushing_yards: 108, rushing_touchdowns: 1
- Tua Tagovailoa: passing_yards: 146, passing_touchdowns: 2, carries: 2
- Khalil Shakir: receptions: 4, receiving_yards: 45

### The Real Issue
The actual problem is that when fetching players through MCP tools, the stats field returns None for most players. This is because:

1. Stats are only available for players who have played in the current week
2. The spot refresh mechanism tries to fetch current week stats but may not find them
3. Only 22 out of 872 players have stats in the cache (as shown by get_cache_status())

## Resolution
Since all the requested stats are already being tracked, the issue is actually RESOLVED. The stats are:
1. Being fetched from the Sleeper API ✅
2. Being filtered and mapped correctly ✅
3. Being stored in the player cache ✅
4. Available for players who have played ✅

## Possible Enhancement
If the user wants stats to be MORE WIDELY available (not just current week), we could:
1. Store season totals in addition to current week stats
2. Keep historical weekly stats in the cache
3. Fetch projections in addition to actual stats

But as written, the issue requirements are already met.

## Recommendation
Close the issue as already completed via PR #56 (which added carries) and the existing stats mapping that already included all other requested stats.