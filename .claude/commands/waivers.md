# Waiver Wire Analysis

Analyze waiver wire opportunities for Bill Beliclaude (Roster ID 2) in the Token Bowl league.

## Goal

Identify high-value waiver claims that improve our championship odds through:
1. Roster need analysis (positions with critical depth gaps)
2. Trending player identification (breakout candidates and league-winners)
3. Recently dropped player evaluation (hidden gems from opponent mistakes)
4. Defense streaming optimization (maximize weekly points)
5. Strategic priority assessment (when to use waiver position)

**Philosophy**: Be aggressive with speculative adds that could win the championship. Better to miss on upside plays than miss playoffs holding mediocre players.

## Execution Phases

### Phase 1: Assess Team Needs

Use the **roster-analyst subagent** to identify positions of need:
- What positions have critical depth gaps (0-1 bench players)?
- Which positions face upcoming bye weeks?
- What are our weakest starting positions?
- Which players are droppable (declining value, excess depth)?

**Reference**: See `.claude/reference/_fantasy_framework.md` for roster construction priorities.

**Key Framework**:
- RB depth is critical (3-4 total, including speculative handcuffs)
- WR depth is important (4-6 total)
- QB/TE/K/DEF - minimal bench needs (can stream)
- Prioritize positions with 0-1 bench depth first

**Untouchables**: Josh Allen and James Cook are not droppable.

### Phase 2: Identify Waiver Opportunities

#### Step 1: Get Consolidated Analysis
```
get_waiver_analysis(position=None, days_back=7, limit=20)
```
This returns recently dropped players AND trending available players in one efficient call.

#### Step 2: Expand Trending Analysis
```
get_trending_players(type="add", limit=25, position=None)
```
Focus on:
- Players with 20-100 adds (sweet spot for early adoption)
- Compare ROS projections to current scoring
- Identify breakout candidates before they fully break out

#### Step 3: Deep Dive on Top Candidates

For each serious candidate (top 10 from Steps 1-2):
```
search_players_by_name(name="Player Name")
```
Extract:
- ROS projections vs recent performance
- Bye week (critical - check if on bye THIS week)
- Depth chart position and role
- Injury status

### Phase 3: Research Priority Targets

Use the **player-researcher subagent** for ALL serious candidates to:
- Investigate injury status and severity
- Analyze usage trends (snap counts, target/carry share)
- Review expert consensus on ROS outlook
- Identify hidden context (coaching changes, schedule, etc.)

**Research is mandatory** - Never make a claim without understanding WHY a player is trending or was dropped.

### Phase 4: Defense Streaming Analysis

Use the **defense-streaming-analyst subagent** to:
- Compare current DEF projection vs top 3 available options
- Get clear streaming recommendation (STREAM / HOLD / CONSIDER)
- Understand matchup quality and home/away factors
- Identify multi-week streaming opportunities

**Reference**: See `.claude/reference/_mcp_tools_cheatsheet.md` for tool usage.

### Phase 5: Waiver Priority Decision

For high-impact adds, use:
```
evaluate_waiver_priority_cost(current_position, projected_ROS_gain, weeks_remaining)
```
Returns: Clear recommendation on whether to use waiver priority now vs wait.

**Decision Framework**:
- **ALWAYS claim if**: ROS projection 25%+ above current roster equivalent
- **STRONGLY CONSIDER if**: ROS projection 15-25% above AND trending up
- **CONSIDER if**: Speculative add with 40%+ playoff week upside
- **PASS if**: Marginal upgrade (<10% ROS improvement) unless critical need

## Output Format

Write comprehensive analysis to: `picks/week{n}/waivers_week{n}.md`

### Structure

**Executive Summary** (3-4 sentences):
- Top 3 moves with brief rationale
- Estimated net ROS impact on championship odds

**Priority Adds** (Ranked 1-5):
For each add, include:
- Player name, position, team
- Current scoring vs ROS projection (e.g., "8.5 PPG → ROS 12.3 PPG = +44% upside")
- Trending data (adds in last 24 hours)
- Bye week and playoff schedule strength
- Speculative upside narrative (why could be league-winner)
- Percentage improvement over player being dropped

**Drop Candidates** (Ranked by priority):
- Player name and reason (declining ROS, excess depth, etc.)
- ROS projection vs recent performance
- Opportunity cost of holding vs adding at position of need

**Defense Streaming Recommendation**:
- Current DEF projection vs top available option
- Clear recommendation (STREAM / HOLD)
- Specific add/drop if streaming

**Speculative Stashes** (If roster space allows):
- High-upside holds who won't help now but could win playoffs
- Timeline for potential breakout

**Net Impact**:
- Total projected points gained for playoffs
- Championship probability impact estimate

## Key Reminders

**Bye Week Handling (CRITICAL)**:
- Always check bye_week field for each player
- Never recommend a player on bye THIS WEEK
- Flag bye week players explicitly: "ON BYE - Cannot play this week"

**ROS Focus**:
- Prioritize season-long value over single week
- Playoff schedule (weeks 15-17) matters more than next week
- Target players whose ROS projections exceed current value by 20%+

**Positional Scarcity**:
- RB > WR when talent comparable (due to scarcity and injury rates)
- Always maintain 3-4 RBs total (including speculative handcuffs)
- Never use bench spot for backup K/DEF/TE

**Research-Driven**:
- Every serious add/drop must have web research backing
- Understand WHY players are trending or were dropped
- Verify injury status and usage trends

**Be Aggressive**:
- Championship teams are built on speculative hits
- Don't hold mediocre players out of fear
- Take calculated risks on high-upside lottery tickets
