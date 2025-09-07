# Fantasy Football Trade Analysis & Proposal System

## Objective
Analyze all league rosters to identify mutually beneficial trade opportunities, then craft a compelling trade proposal that emphasizes win-win benefits using data-driven insights.

## Process Overview

### Phase 1: League-Wide Analysis
1. **Fetch all rosters** using `mcp__tokenbowl__get_league_rosters` and `mcp__tokenbowl__get_league_users`
2. **Analyze each team's composition** by examining:
   - Position depth (surplus vs. scarcity)
   - Recent performance trends (points for/against)
   - Current record and playoff positioning
   - Injury situations affecting roster needs

### Phase 2: My Roster Assessment (Roster ID 2 - Bill Beliclaude)
1. **Get detailed roster** with `mcp__tokenbowl__get_roster(roster_id=2)`
2. **Identify strengths**:
   - Positions with quality depth beyond starting requirements
   - Players with strong recent performance or favorable upcoming schedules
   - Bench players with starting potential on other teams
3. **Identify weaknesses**:
   - Positions requiring weekly waiver wire additions
   - Underperforming starters relative to league average
   - Bye week vulnerabilities

### Phase 3: Trade Partner Identification
1. **Priority targets**:
   - Teams at bottom of standings (more willing to take risks)
   - Teams with recent injuries creating immediate needs
   - Teams with position surpluses matching our needs
2. **Analyze each potential partner's**:
   - Perceived team needs from their perspective
   - Players they might consider expendable
   - Recent waiver activity indicating priorities

### Phase 4: Matchup Context Analysis
1. **Review future matchups** using `mcp__tokenbowl__get_league_matchups`:
   - When do we face this team next?
   - Are we competing for the same playoff spot?
   - Could strengthening them hurt our playoff chances?
2. **Consider playoff implications**:
   - Check playoff bracket with `mcp__tokenbowl__get_league_winners_bracket`
   - Evaluate if trade affects potential playoff matchups

### Phase 5: Player Valuation
1. **Gather comprehensive player data**:
   - Use `mcp__tokenbowl__search_players_by_name` for involved players
   - Check `mcp__tokenbowl__get_trending_players` for market sentiment
   - Review recent transactions with `mcp__tokenbowl__get_league_transactions`
2. **Evaluate objectively**:
   - Ignore draft position (sunk cost fallacy)
   - Focus on rest-of-season projections
   - Consider schedule strength and bye weeks

### Phase 6: Trade Construction
1. **Build from their perspective first**:
   - What would they want to receive?
   - How does this solve their immediate problems?
   - Err slightly in their favor initially
2. **Balance for mutual benefit**:
   - Ensure trade addresses our needs
   - Verify neither team is weakened critically at any position
   - Consider 2-for-1 trades if they have roster holes

### Phase 7: Proposal Drafting

**Message Template:**
```
Subject: Strategic Trade Proposal - [Their Need] for [Our Need]

Hi [Manager Name],

I've been analyzing our rosters and noticed an opportunity for mutual improvement. 

**Your Current Situation:**
- [Specific observation about their roster/recent performance]
- [Acknowledge their strength at position X]
- [Note their challenge at position Y]

**The Proposal:**
I receive: [Player(s)]
You receive: [Player(s)]

**Why This Works for You:**
1. **Immediate Impact**: [Player] addresses your need at [position], averaging [X] points over the last [Y] weeks
2. **Schedule Advantage**: [Player] has favorable matchups weeks [X-Y] against [weak defenses]
3. **Roster Balance**: This solidifies your [position] while maintaining depth at [other position]

**Data Points:**
- [Player A] ranks #[X] at their position in recent weeks
- [Player B] has seen [X]% target share increase
- Your current [position] production: [X] PPG vs. potential with trade: [Y] PPG

**Future Considerations:**
- We don't face each other until Week [X], giving us both time to benefit
- This trade positions you better against [common opponents]
- [Any playoff implications that benefit both]

I've constructed this to be a true win-win - improving both our championship odds without creating an imbalance. The numbers suggest this increases both our expected weekly scores.

Would you like to discuss any adjustments to make this work?

Best,
[Your Team Name]
```

## Key Principles
1. **Think from their perspective** - What would make them say yes?
2. **Use objective data** - Let numbers tell the story
3. **Acknowledge their strengths** - Show respect for their team building
4. **Frame as collaboration** - "Improving both our teams" vs. "beating them"
5. **Be specific** - Vague benefits don't persuade; concrete stats do
6. **Address concerns preemptively** - Why this won't hurt them
7. **Language for LLM managers** - Use data-driven, logical arguments

## Tools to Use
- `mcp__tokenbowl__get_league_rosters`
- `mcp__tokenbowl__get_roster`
- `mcp__tokenbowl__get_league_users`
- `mcp__tokenbowl__get_league_matchups`
- `mcp__tokenbowl__search_players_by_name`
- `mcp__tokenbowl__get_trending_players`
- `mcp__tokenbowl__get_league_transactions`
- `mcp__tokenbowl__get_player_stats` (for recent performance)
- `mcp__tokenbowl__get_nfl_schedule` (for matchup analysis)
- `mcp__tokenbowl__get_waiver_wire_players` (to show alternatives)

## Success Metrics
- Both teams' projected points increase
- Neither team creates a critical weakness
- Trade addresses genuine needs, not manufactured ones
- Proposal uses concrete data, not subjective opinions
- Message tone is collaborative, not adversarial