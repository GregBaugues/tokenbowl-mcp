# Issue #83: Season Null in get_roster

**Issue URL**: https://github.com/GregBaugues/sleeper-mcp/issues/83

## Problem
The `get_roster` function returns `season: null` and `week: null` when it should be returning the current season (2025) and week.

## Root Cause
The `get_roster` function initializes `season` and `week` as `None` with a comment saying "Will be populated from player projections", but there's no code that actually updates these fields.

## Solution Plan
1. ✅ Identify the issue: Season and week are never populated
2. ✅ Find the proper way to get season/week: Use Sleeper's `/state/nfl` endpoint
3. Add an API call to get the NFL state in `get_roster` function
4. Update the `enriched_roster` dict with the actual season and week values
5. Test the changes
6. Create PR

## Implementation Details

The fix involves:
1. Adding an async call to `{BASE_URL}/state/nfl` to get the current NFL state
2. Extracting the `season` and `week` from the response
3. Updating the `enriched_roster` dictionary with these values

Example from `get_player_stats_all_weeks` (line 1366):
```python
state_response = await client.get(f"{BASE_URL}/state/nfl")
state_response.raise_for_status()
state = state_response.json()
current_season = season or str(state.get("season", datetime.now().year))
current_week = state.get("week", 1)
```

We need to add similar logic to `get_roster` function.