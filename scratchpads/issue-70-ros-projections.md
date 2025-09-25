# Issue #70: Add Support for Rest of Season (ROS) Projections

GitHub Issue: https://github.com/GregBaugues/sleeper-mcp/issues/70

## Problem Statement
The Fantasy Nerds API supports rest of season (ROS) projections that provide projected totals for the remainder of the season. This is valuable for:
- Trade evaluations
- Add/drop decisions
- Long-term roster planning

Currently, we only fetch weekly projections from Fantasy Nerds.

## API Endpoint
- URL: `https://api.fantasynerds.com/v1/nfl/ros?apikey={apikey}`
- Returns ROS projections for all skill and IDP players
- Statistical categories vary by position

## Implementation Plan

### 1. Update build_cache.py
- Add function to fetch ROS projections from Fantasy Nerds API
- Store ROS data alongside weekly projections in the player cache
- Structure: Add `ros_projections` field alongside existing `projections` (weekly)

### 2. Update Cache Structure
Current structure has weekly projections in:
```python
player["data"]["projections"] = {
    "proj_pts": float,
    "week": int,
    "season": int,
    ...stats...
}
```

Will add:
```python
player["data"]["ros_projections"] = {
    "proj_pts": float,
    "games_remaining": int,  # Estimated games left
    ...stats...
}
```

### 3. Update MCP Tools
Enhance existing tools to include ROS data:
- `get_roster()` - Include ROS projections for each player
- `search_players_by_name()` - Include ROS data in results
- `get_player_by_sleeper_id()` - Include ROS projections
- `get_waiver_wire_players()` - Show ROS projections to help with add/drop
- `get_waiver_analysis()` - Use ROS data for better recommendations

### 4. Testing
- Verify ROS data is fetched correctly
- Ensure cache builds without errors
- Test that MCP tools return ROS data properly
- Verify ROS projections format correctly (2 decimal places)

## Implementation Steps

1. ✅ Research existing code and understand current projection implementation
2. ⏳ Create feature branch `issue-70-ros-projections`
3. ⏳ Fetch sample ROS data to understand structure
4. ⏳ Update build_cache.py to fetch and store ROS data
5. ⏳ Update MCP tools to expose ROS projections
6. ⏳ Test thoroughly
7. ⏳ Create PR with documentation

## Files to Modify
- `build_cache.py` - Add ROS fetching and storage
- `sleeper_mcp.py` - Update tools to include ROS data
- `cache_client.py` - Potentially update to handle ROS data display

## Notes
- ROS projections should be clearly labeled to distinguish from weekly projections
- Consider caching strategy - ROS data changes less frequently than weekly
- Ensure backwards compatibility with existing cache structure