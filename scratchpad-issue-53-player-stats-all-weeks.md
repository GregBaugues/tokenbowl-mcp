# Issue #53: Add Tool to Get All Weeks of Real Stats for a Player

GitHub Issue: https://github.com/GregBaugues/sleeper-mcp/issues/53

## Problem Description
The issue requests adding a new tool to get real stats for all weeks for a given player. Currently, the player cache only returns stats for the current week (via the spot_refresh_player_stats mechanism), and this should remain unchanged. The new tool will provide a way to get historical stats for any player across all weeks of the season.

## Implementation Plan

### 1. New Tool Function: `get_player_stats_all_weeks`

#### Function Signature
```python
@mcp.tool()
async def get_player_stats_all_weeks(
    player_id: str,
    season: Optional[str] = None
) -> Dict[str, Any]
```

#### Parameters
- `player_id`: The Sleeper player ID (required)
- `season`: The season year (optional, defaults to current year)

#### Returns
Dictionary containing:
- Player information (name, position, team)
- Stats by week (week 1-18) with actual game stats
- Total stats across all weeks
- Games played count

### 2. Implementation Details

#### API Endpoints Used
- Player info: Get from cache using `get_player_by_id()`
- Stats per week: `https://api.sleeper.app/v1/stats/nfl/regular/{season}/{week}`
- Current season info: `https://api.sleeper.app/v1/state/nfl`

#### Logic Flow
1. Validate player_id exists in cache
2. Get current season from NFL state endpoint (or use provided season)
3. Determine the current week to avoid fetching future weeks
4. Make concurrent requests for all weeks (1 to current_week)
5. Filter stats using the same PPR-relevant logic from `filter_ppr_relevant_stats`
6. Aggregate stats for the player across all weeks
7. Return comprehensive stats data

### 3. Key Considerations

#### Performance
- Use `httpx.AsyncClient` with concurrent requests for all weeks
- Implement proper error handling for individual week failures
- Set reasonable timeouts (10s per request)

#### Data Structure
```python
{
    "player_id": "4046",
    "player_info": {
        "name": "Patrick Mahomes",
        "position": "QB",
        "team": "KC",
        "status": "Active"
    },
    "season": 2025,
    "weeks_fetched": 10,
    "weekly_stats": {
        "1": {
            "fantasy_points": 25.4,
            "passing_yards": 291,
            "passing_touchdowns": 3,
            ...
        },
        "2": {
            "fantasy_points": 19.8,
            ...
        },
        ...
    },
    "totals": {
        "fantasy_points": 245.6,
        "passing_yards": 2915,
        "passing_touchdowns": 30,
        "games_played": 10,
        ...
    }
}
```

#### Error Handling
- Handle player not found in cache
- Handle API failures gracefully
- Return partial data if some weeks fail
- Include error information in response

### 4. Testing Approach
- Test with valid player ID
- Test with invalid player ID
- Test with different seasons
- Test concurrent request handling
- Verify stats aggregation is correct

### 5. Integration Notes
- Tool will be added to sleeper_mcp.py
- No changes to cache_client.py (cache remains current week only)
- Use existing filter_ppr_relevant_stats function from cache_client
- Tool will be accessible as `mcp__tokenbowl__get_player_stats_all_weeks` when deployed

## Next Steps
1. Create branch `issue-53-player-stats-all-weeks`
2. Implement the new tool in sleeper_mcp.py
3. Test locally with various player IDs
4. Run linting and formatting checks
5. Create PR with comprehensive description