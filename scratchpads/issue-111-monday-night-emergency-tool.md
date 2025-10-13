# Issue #111: Monday Night Emergency Waiver Tool

**Issue Link**: https://github.com/GregBaugues/sleeper-mcp/issues/111

## Problem Summary

The user needs a tool for Monday Night Football emergency situations where a player is injured or ruled out and they need to quickly find an available replacement at that position who hasn't played yet.

**Tool Name**: `its_monday_night_and_i_need_a(position)`
**Function**: Returns available players at a position who haven't played yet, sorted by projection descending

## Implementation Plan

### 1. Understand Requirements
- Tool specifically for Monday night emergency situations
- Must filter for players available on waivers (free agents)
- Must filter for players who haven't played yet this week
- Must sort by projections (highest first)
- Position is required parameter

### 2. Technical Analysis

#### Data Needed:
1. **Available players**: Use existing `get_waiver_wire_players` functionality
2. **Game schedule**: Use `get_nfl_schedule` to determine which teams haven't played
3. **Projections**: Already available in player cache data
4. **Current week**: Get from Sleeper state API

#### Key Challenges:
- Need to determine which teams play on Monday night or haven't played yet
- Must cross-reference player teams with game schedule
- Handle timezone correctly for game times

### 3. Implementation Steps

#### 3.1 Create the new MCP tool function
- Add new function `its_monday_night_and_i_need_a` in `sleeper_mcp.py`
- Accept position parameter (validate using existing validation)
- Get current week from Sleeper state API
- Fetch NFL schedule for current week
- Determine which teams haven't played yet (Monday night + any postponed)
- Get available players at position using waiver wire logic
- Filter to only players on teams that haven't played
- Sort by projected points descending
- Return minimal data format for context efficiency

#### 3.2 Reuse existing utilities
- Use `validate_position` from lib/validation.py
- Use `enrich_player_minimal` from lib/enrichment.py
- Leverage existing waiver wire player fetching logic
- Use existing schedule fetching logic

#### 3.3 Add appropriate error handling
- Handle case where no players available
- Handle invalid position
- Handle schedule API failures gracefully

### 4. Testing Strategy

#### Unit Tests:
- Test position validation
- Test filtering logic for teams that haven't played
- Test sorting by projections
- Test edge cases (no available players, all teams played)

#### Integration Tests:
- Test with real schedule data
- Test with actual waiver wire data
- Verify projections are included and sorted correctly

### 5. Files to Modify

1. **sleeper_mcp.py** - Add new MCP tool function (~100 lines)
2. **tests/test_sleeper_mcp.py** - Add tests for new tool
3. **README.md** - Document new tool

### 6. Implementation Details

```python
@mcp.tool()
@log_mcp_tool
async def its_monday_night_and_i_need_a(position: str) -> List[Dict[str, Any]]:
    """Get available waiver wire players at a position who haven't played yet this week.

    Perfect for Monday Night Football emergencies when you need a last-minute replacement.
    Returns players sorted by projected points (highest first).

    Args:
        position: Required position (QB, RB, WR, TE, K, DEF).
                 Case-insensitive (will be uppercased).

    Returns:
        List of available players who haven't played yet, with:
        - Player name, team, position
        - Projected points for the week
        - Game time and opponent
        - Sorted by projected points descending
    """
```

### 7. Algorithm:
1. Validate position parameter
2. Get current week and season from Sleeper state
3. Fetch NFL schedule for current week
4. Parse game times to determine teams that haven't played
   - Consider current time (use PST/PDT timezone)
   - Monday night games typically at 5:15 PM or 8:15 PM ET
   - Include teams with games at or after current time
5. Get all available players at position using waiver wire logic
6. Filter to only include players on teams that haven't played
7. Enrich with minimal data (name, team, projections)
8. Sort by projected_points descending
9. Return list of candidates

### 8. Success Criteria

- [x] Tool correctly identifies teams that haven't played yet
- [x] Only returns available (non-rostered) players
- [x] Correctly filters by position
- [x] Sorts by projections with highest first
- [x] Returns minimal data to reduce context usage
- [x] Handles edge cases gracefully
- [x] All tests pass
- [x] Documentation updated

## Notes

- This tool is specifically designed for emergency situations
- Most useful on Monday nights during the NFL season
- Could also be useful for Sunday night games
- Should return empty list if all teams have played
- Consider caching schedule data to reduce API calls