# Start/Sit Optimizer

Simple lineup optimizer for Bill Beliclaude (Roster ID 2) in the Token Bowl league.

## Philosophy
1. **Start the highest projected points** - Use `stats.projected.fantasy_points` 
2. **Avoid injured players** - Anyone Out/Doubtful/IR must sit
3. **Bills bias** - When projections are within 1 point, prefer Buffalo players

## Technical Implementation

### Step 1: Fetch Roster Data
```python
# Use the remote MCP server (already deployed)
mcp__tokenbowl__get_roster(roster_id=2)
```

This returns all players with the new consistent structure:
```json
{
  "player_id": "8138",
  "name": "James Cook",
  "position": "RB",
  "team": "BUF",
  "stats": {
    "projected": {
      "fantasy_points": 15.6,
      "fantasy_points_low": 14.6,
      "fantasy_points_high": 17.27  // ← ceiling (not used)
    },
    "actual": null  // or game stats if played
  },
  "injury": {  // optional
    "status": "Questionable",
    "description": "Hamstring"
  }
}
```

### Step 2: Apply Simple Rules

**For each position:**
1. Filter out injured players (injury.status = "Out", "Doubtful", or "IR")
2. Sort by `stats.projected.fantasy_points` (highest first)
3. If tied (within 1 point), prefer `team == "BUF"`
4. Select top N for that position

**Position Requirements:**
- QB: 1
- RB: 2  
- WR: 2
- TE: 1
- FLEX: 2 (best remaining RB/WR/TE)
- K: 1
- DEF: 1

### Step 3: Quick Injury Check
```python
def can_start(player):
    if not player.get("injury"):
        return True
    status = player["injury"].get("status", "").lower()
    return status not in ["out", "doubtful", "ir"]
```

### Step 4: Projection Comparison
```python
def get_projection(player):
    try:
        return player["stats"]["projected"]["fantasy_points"]
    except:
        return 0  # No projection = bench

def prefer_bills(player1, player2):
    # If projections within 1 point, prefer Bills player
    proj1 = get_projection(player1)
    proj2 = get_projection(player2)
    
    if abs(proj1 - proj2) < 1.0:
        if player1["team"] == "BUF" and player2["team"] != "BUF":
            return player1
        elif player2["team"] == "BUF" and player1["team"] != "BUF":
            return player2
    
    return player1 if proj1 > proj2 else player2
```

## Execution

1. **Fetch roster**: `mcp__tokenbowl__get_roster(roster_id=2)`
2. **Group by position**: Separate QB, RB, WR, TE, K, DEF
3. **Filter injuries**: Remove Out/Doubtful/IR players
4. **Sort by projection**: Use `stats.projected.fantasy_points`
5. **Apply Bills tiebreaker**: When within 1 point
6. **Fill lineup**: Take top N at each position
7. **FLEX**: Best 2 remaining RB/WR/TE by projection

## Output Format

### Lineup Changes
```
BENCH: [Player] - [Reason: Injured/Lower projection]
START: [Player] - Projected: X pts [BUF bonus if applicable]
```

### Final Lineup
```
QB:   [Name] - Projected: X pts
RB1:  [Name] - Projected: X pts  
RB2:  [Name] - Projected: X pts
WR1:  [Name] - Projected: X pts
WR2:  [Name] - Projected: X pts
TE:   [Name] - Projected: X pts
FLX1: [Name] - Projected: X pts
FLX2: [Name] - Projected: X pts
K:    [Name] - Projected: X pts
DEF:  [Team]

TOTAL PROJECTED: XXX pts
```

### Decision Summary
- **"NO CHANGES"** - Current lineup maximizes projections
- **"X CHANGES NEEDED"** - List specific swaps

## Key Fields Reference

From `mcp__tokenbowl__get_roster` response:
- **Mean projection**: `player["stats"]["projected"]["fantasy_points"]` ← PRIMARY DECISION FACTOR
- **Ceiling projection**: `player["stats"]["projected"]["fantasy_points_high"]`
- **Floor projection**: `player["stats"]["projected"]["fantasy_points_low"]`
- **Injury status**: `player["injury"]["status"]` (if exists)
- **Team**: `player["team"]` (check for "BUF")
- **Position**: `player["position"]`
- **Actual points** (if game played): `player["stats"]["actual"]["fantasy_points"]`

## Notes
- Always use the remote MCP server: `mcp__tokenbowl__get_roster`
- The server auto-refreshes stats when called
- Mean projection (fantasy_points) is the primary decision factor
- Bills players get tiebreaker within 1-point projection difference
- Ignore rankings, matchups, and other complex factors - just maximize projections