# Start/Sit Optimizer

Simple lineup optimizer for Bill Beliclaude (Roster ID 2) in the Token Bowl league.

## Philosophy
1. **Start the highest ceiling** - Use `stats.projected.fantasy_points_high` 
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
      "fantasy_points_high": 17.27  // ← USE THIS FOR CEILING
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
2. Sort by `stats.projected.fantasy_points_high` (highest first)
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

### Step 4: Ceiling Comparison
```python
def get_ceiling(player):
    try:
        return player["stats"]["projected"]["fantasy_points_high"]
    except:
        return 0  # No projection = bench

def prefer_bills(player1, player2):
    # If ceilings within 1 point, prefer Bills player
    ceiling1 = get_ceiling(player1)
    ceiling2 = get_ceiling(player2)
    
    if abs(ceiling1 - ceiling2) < 1.0:
        if player1["team"] == "BUF" and player2["team"] != "BUF":
            return player1
        elif player2["team"] == "BUF" and player1["team"] != "BUF":
            return player2
    
    return player1 if ceiling1 > ceiling2 else player2
```

## Execution

1. **Fetch roster**: `mcp__tokenbowl__get_roster(roster_id=2)`
2. **Group by position**: Separate QB, RB, WR, TE, K, DEF
3. **Filter injuries**: Remove Out/Doubtful/IR players
4. **Sort by ceiling**: Use `stats.projected.fantasy_points_high`
5. **Apply Bills tiebreaker**: When within 1 point
6. **Fill lineup**: Take top N at each position
7. **FLEX**: Best 2 remaining RB/WR/TE by ceiling

## Output Format

### Lineup Changes
```
BENCH: [Player] - [Reason: Injured/Lower ceiling]
START: [Player] - Ceiling: X pts [BUF bonus if applicable]
```

### Final Lineup
```
QB:   [Name] - Ceiling: X pts
RB1:  [Name] - Ceiling: X pts  
RB2:  [Name] - Ceiling: X pts
WR1:  [Name] - Ceiling: X pts
WR2:  [Name] - Ceiling: X pts
WR3:  [Name] - Ceiling: X pts
TE:   [Name] - Ceiling: X pts
FLX1: [Name] - Ceiling: X pts
FLX2: [Name] - Ceiling: X pts
K:    [Name] - Ceiling: X pts
DEF:  [Team]

TOTAL CEILING: XXX pts
```

### Decision Summary
- **"NO CHANGES"** - Current lineup maximizes ceiling
- **"X CHANGES NEEDED"** - List specific swaps

## Key Fields Reference

From `mcp__tokenbowl__get_roster` response:
- **Ceiling projection**: `player["stats"]["projected"]["fantasy_points_high"]`
- **Mean projection**: `player["stats"]["projected"]["fantasy_points"]`
- **Floor projection**: `player["stats"]["projected"]["fantasy_points_low"]`
- **Injury status**: `player["injury"]["status"]` (if exists)
- **Team**: `player["team"]` (check for "BUF")
- **Position**: `player["position"]`
- **Actual points** (if game played): `player["stats"]["actual"]["fantasy_points"]`

## Notes
- Always use the remote MCP server: `mcp__tokenbowl__get_roster`
- The server auto-refreshes stats when called
- Ceiling (high projection) is the primary decision factor
- Bills players get tiebreaker within 1-point ceiling difference
- Ignore rankings, matchups, and other complex factors - just maximize ceiling