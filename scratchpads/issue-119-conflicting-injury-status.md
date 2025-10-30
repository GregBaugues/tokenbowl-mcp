# Issue #119: Conflicting Injury Status in get_player_by_sleeper_id

**GitHub Issue**: https://github.com/GregBaugues/sleeper-mcp/issues/119
**Date**: 2025-10-30
**Reporter**: @brentschooley

## Problem Description

The `get_player_by_sleeper_id` function returns conflicting injury information for a player. Specifically, for Terry McLaurin (player ID 5927), the response contains:

1. `injury_status: "Out"` - From Sleeper API
2. `data.injury.game_status: "Questionable For Week 9 Vs. Seattle"` - From Fantasy Nerds API

These two values conflict with each other, which could mislead users about the player's actual status for Week 9.

## Investigation

### Current Data Flow

1. **`get_player_by_sleeper_id`** (sleeper_mcp.py:~1820):
   - Calls `spot_refresh_player_stats({player_id})` to update stats
   - Calls `get_player_by_id(player_id)` to fetch from cache
   - Returns the full player data

2. **`get_player_by_id`** (cache_client.py):
   - Simply fetches player from cached data
   - Returns the entire cached player object

3. **Player Data Structure** (from cache):
   The cached player data includes:
   - Base Sleeper fields: `injury_status`, `injury_body_part`, `injury_notes`, etc.
   - Enriched FFNerd data in `data` field: `data.injury.game_status`, `data.injury.injury`, etc.

### Root Cause

The issue is that we have two sources of injury information:
1. **Sleeper API**: Provides `injury_status` field (e.g., "Out", "Questionable", "Doubtful")
2. **Fantasy Nerds API**: Provides more detailed injury info in `data.injury` including `game_status`

These two sources can have different/conflicting information because:
- They may update at different times
- They may use different sources/criteria
- They may have different interpretations of injury severity

### Current Cache Building

Looking at `build_cache.py`:
- Line ~225: We're including the Fantasy Nerds injury data in the enrichment
- Line ~275: We're also keeping the original Sleeper `injury_status` field

## Solution Plan

We need to reconcile the conflicting injury information. Options:

### Option 1: Use Only One Source (Recommended)
**Prefer Fantasy Nerds data when available**, as it's more detailed and specific:
- If `data.injury` exists, use it as the single source of truth
- Map Fantasy Nerds `game_status` to the standard `injury_status` field
- Remove the original Sleeper `injury_status` to avoid confusion

### Option 2: Merge and Prioritize
Create a unified injury status that prioritizes the most recent/detailed info:
- Check timestamps to see which is more recent
- If FFNerd has data, use it; otherwise fall back to Sleeper

### Option 3: Keep Both but Clarify
Keep both sources but rename/structure them clearly:
- `sleeper_injury_status` for Sleeper data
- `ffnerd_injury_status` for FFNerd data
- Add a `resolved_injury_status` that picks the best one

## Implementation Steps

Going with **Option 1** (Use FFNerd as primary source):

1. **Modify `build_cache.py`**:
   - When building the cache, if FFNerd injury data exists, don't include Sleeper's `injury_status`
   - Map FFNerd's `game_status` to a standardized format

2. **Update the enrichment logic** in `lib/enrichment.py`:
   - Ensure injury data is consistently structured
   - Add logic to extract status from FFNerd data

3. **Test the changes**:
   - Create test cases with conflicting injury data
   - Verify the resolution works correctly

4. **Update documentation**:
   - Document that injury information comes primarily from Fantasy Nerds when available

## Files to Modify

1. `build_cache.py` - Modify cache building to resolve injury conflicts
2. `lib/enrichment.py` - Potentially update enrichment logic
3. `tests/test_enrichment.py` - Add tests for injury conflict resolution

## Test Cases

1. Player with FFNerd injury data - should use FFNerd status
2. Player with only Sleeper injury data - should use Sleeper status
3. Player with conflicting data - should prefer FFNerd
4. Player with no injury data - should have null/none status

## Notes

- This is a data consistency issue, not a bug in the code logic
- The fix should be backward compatible with existing cached data
- We should monitor if this happens with other fields too