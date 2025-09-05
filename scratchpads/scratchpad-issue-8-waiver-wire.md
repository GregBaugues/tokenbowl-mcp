# Implementation Plan: Waiver Wire Tool
**Issue #8**: https://github.com/GregBaugues/sleeper-mcp/issues/8

## Problem Analysis
We need to create a tool that shows players available on the waiver wire. Available players are those not currently on any team roster in the league.

## Technical Approach

### Data Sources
1. **League Rosters** (`/league/{league_id}/rosters`): Get all rosters with their player lists
2. **NFL Players Cache** (Redis): Use cached player database for player details
3. **Trending Players** (optional): Show trending adds to highlight hot waiver targets

### Implementation Steps

1. **Fetch all rosters** from the league
2. **Collect all rostered player IDs** into a set
3. **Get all NFL players** from cache
4. **Filter out rostered players** to find free agents
5. **Add metadata** (position, team, fantasy points if available)
6. **Provide filtering options**:
   - By position (QB, RB, WR, TE, DEF, K)
   - By search term (player name)
   - By trending (most added players)

### Tool Design

```python
@mcp.tool()
async def get_waiver_wire_players(
    position: Optional[str] = None,
    search_term: Optional[str] = None,
    include_trending: bool = False,
    limit: int = 50
) -> Dict[str, Any]
```

### Key Considerations

1. **Cache Staleness**: The Redis cache refreshes daily, but roster changes happen frequently. We'll fetch live roster data but use cached player details.

2. **Performance**: With ~4000 NFL players and 10-12 rosters (each with ~20-30 players), we need efficient filtering.

3. **Relevance**: Filter out retired/inactive players when possible using player status fields.

4. **Sorting**: Return most relevant players first (by projected points, recent adds, or alphabetically).

### Response Structure
```json
{
  "available_count": 3500,
  "filtered_count": 25,
  "players": [
    {
      "player_id": "xxx",
      "name": "Player Name",
      "position": "WR",
      "team": "SF",
      "status": "Active",
      "trending_add_count": 1500
    }
  ],
  "cache_info": {
    "last_updated": "2025-01-05T12:00:00Z",
    "stale_warning": false
  }
}
```

### Testing Strategy
1. Mock roster data with known player IDs
2. Verify correct filtering of rostered vs available players
3. Test position and search filters
4. Ensure proper error handling for cache misses