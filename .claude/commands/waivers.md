# Waiver Wire Analysis

Analyze waiver wire opportunities for Bill Beliclaude (Roster ID 2) in the Token Bowl league.

## Strategy

### 0. Identify the needs of the team
- Review the team's performance over the previous weeks
- Identify the positions where we need the most help to increase our odds of making the playoffs

  - **Positional Scarcity Priority**: Always prioritize based on roster construction:
    - If 0-1 bench players at a position = CRITICAL NEED (highest priority)
    - If 2 bench players = ADEQUATE DEPTH (medium priority)
    - If 3+ bench players = OVERSTOCKED (lowest priority)
    - RB depth takes precedence over WR depth due to injury rates and waiver scarcity

  - **Priority Adds** (ranked 1-5 with rationale)
    PRIORITIZATION FRAMEWORK:
    1. First address positions with 0-1 bench players (critical need)
    2. Then consider talent upgrades at positions with 2+ bench players
    3. Account for immediate bye weeks (next 2 weeks = higher priority)
    4. RB > WR when talent is comparable (due to scarcity)
    5. Never prioritize a position where we have 4+ bench players unless it's a clear league-winner
- Think long term. Think about bye weeks, and speculative holds that could prove valuable later in the season. For positions like RB, where availability is thin, try to get a backup
- Identify the players who are weak, who could be dropped
- We will hold Josh Allen and James Cook for the season

### 0.5 Efficient Waiver Analysis (NEW - Use First!)
- **Use `get_waiver_analysis()` tool** to get consolidated analysis with minimal context:
  - Shows recently dropped players from our league (last 7 days)
  - Shows trending available players with add counts
  - Includes waiver priority position
  - All data in minimal format to save context
- This single tool replaces multiple queries and reduces context by 80%

### 1. Identify Top Waiver Targets
- **Use the efficient waiver analysis first** (see 0.5 above)
- For deeper analysis on specific players:
  - Use `get_trending_context(player_ids)` to understand WHY players are trending
  - Focus on players with high target share and opportunity
  - Look for recent usage changes or injury situations
- **CRITICAL**: Always check dropped players with 0 games played - they may be returning from suspension/IR

### 2. Evaluation Criteria
**Priority metrics:**
- **Ceiling over floor**: Target players with breakout potential
- **Opportunity share**: High targets -> consistent PPR points
- **Trending usage**: Recent games more predictive than season averages
- **Schedule strength**: Both immediate (1-3 weeks) and playoff weeks

  - Check upcoming bye weeks for our starters and ensure we have coverage
  - A position with a bye week in the next 2 weeks automatically becomes higher priority

**Drop Priority Framework:**
  1. Efficiency over volume - Prioritize catch rate, YPG, and recent trends over raw targets
  2. Age cliff analysis - Players 30+ in declining offenses are prime drop candidates
  3. Opportunity cost - Always compare: "What does keeping Player X cost us vs. adding position of need?"
  4. Boom/bust evaluation - Consistent 4-6 point floors often less valuable than RB lottery tickets
  5. Name recognition check - Actively question whether you're holding aging veterans due to past reputation

  For each potential drop candidate, answer: Would I rather have this player's projected 6-8 weekly points, or take a lottery ticket at our position of greatest need?

### 3. Waiver Priority Decision (NEW)
- **Use `evaluate_waiver_priority_cost()` tool** to determine if using waiver priority is worth it:
  - Input: current waiver position, projected points gain, weeks remaining
  - Returns: clear recommendation with reasoning
  - Helps decide between claiming now vs. waiting for better opportunity

### 4. Cost-Benefit Decision Matrix
Only make moves if:
- Waiver player's ceiling > Current player's floor by 20%+
- Waiver player has clear path to increased usage
- You can make a case justifying dropping the rostered player
- Position need aligns with upcoming bye weeks
- **Waiver priority analysis confirms it's worth using (if applicable)**

## Efficient Workflow (Updated for New Tools)

1. **Start with consolidated analysis:**
   ```
   get_waiver_analysis(position=None, days_back=7, limit=20)
   ```
   This gives you everything in one efficient call!

2. **Get context for top targets:**
   ```
   get_trending_context(player_ids=[list of top 5 player IDs])
   ```
   Understand WHY players are trending

3. **Evaluate waiver priority cost:**
   ```
   evaluate_waiver_priority_cost(current_position, projected_points_gain, weeks_remaining)
   ```
   Decide if it's worth using priority

## Key Questions to Answer

1. **Who are the top 3 waiver targets by position?**
   - Use waiver analysis tool for efficient data
   - Include trending context for each player
   - Focus on opportunity and usage trends

2. **Which rostered players are droppable?**
   - Compare ROS projections
   - Consider position depth on our roster

3. **What's the net impact?**
   - Expected points gained/lost per week
   - Waiver priority cost vs. benefit
   - The value of the replacement player over the one we are dropping

## Output Format

Present findings as:
- **Priority Adds** (ranked 1-5 with rationale)
  - In determining priority - look at positions where we lack depth to be a season long contender, and positions where there is scarcity in the waivers. For example, in our league, if there is a hot RB, you should probably prioritize over a WR.
- **Drop Candidates** (ranked by dispensability)
- **Hold Recommendations** (close calls to monitor)

## Make the final decision
You are the manager.
Give me an ultimate recommendation for waiver claims this week.
It is okay to stay the course and not pick up anyone on waivers.
If undeniable opportunity presents itself, we should make a waiver claim.

Write the final report to:
picks/week{n}/waivers_week{n}.md