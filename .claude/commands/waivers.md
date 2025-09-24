# Waiver Wire Analysis

Analyze waiver wire opportunities for Bill Beliclaude (Roster ID 2) in the Token Bowl league.

## Strategy

### 0. Identify the needs of the team. 
- Review the team's performance over the previous weeks. 
- Identify the positions where we need the most help to increase our odds of making the playoffs. 

  - **Positional Scarcity Priority**: Always prioritize based on roster construction:
    - If 0-1 bench players at a position = CRITICAL NEED (highest priority)
    - If 2 bench players = ADEQUATE DEPTH (medium priority)
    - If 3+ bench players = OVERSTOCKED (lowest priority)
    - RB depth takes precedence over WR depth due to injury rates and waiver scarcity

  Replace lines 72-73 with more explicit guidance:
  - **Priority Adds** (ranked 1-5 with rationale)
    PRIORITIZATION FRAMEWORK:
    1. First address positions with 0-1 bench players (critical need)
    2. Then consider talent upgrades at positions with 2+ bench players
    3. Account for immediate bye weeks (next 2 weeks = higher priority)
    4. RB > WR when talent is comparable (due to scarcity)
    5. Never prioritize a position where we have 4+ bench players unless it's a clear league-winner
- Think long term. Think about bye weeks, and speculative holds that could prove valuable later in the season. For positions like RB, where availability is thin, try to get a backup. 
- Identify the players who are weak, who could be dropped. 
- We will hold Josh Allen and James Cook for the season. 

### 0.5 Look at recent drops
- review league transactions
- use the scouting agent to create a dossier on any player dropped in the last 7 days
- confirm that players are still available on waivers before researching further
- identify if any of those players should be candidates for waivers

### CRITICAL: Always check dropped players with 0 games played - they may be returning from suspension/IR and represent massive value

### 1. Identify Top Waiver Targets
- Query waiver wire for our positions of need. 
- Focus on players with:
  - High target share. View each player's real stats to see targets per game. Favor recievers and RBs who get the lions share of targets/carries. Be wary of picking up boom-or-bust players. 
  - Positive trending adds (momentum indicator)
  - Pull the recent stats for the potential waiver adds. 
  - Use a subagent to do web research on the potential adds to understand why they may be trending. 
  - Ensure that you are using up-to-the-week research for the 2025 NFL Fantasy Season. 



### 2. Evaluation Criteria
**Priority metrics:**
- **Ceiling over floor**: Target players with breakout potential
- **Opportunity share**: High targets -> consistent PPR points
- **Trending usage**: Recent games more predictive than season averages
- **Schedule strength**: Both immediate (1-3 weeks) and playoff weeks

  - Check upcoming bye weeks for our starters and ensure we have coverage
  - A position with a bye week in the next 2 weeks automatically becomes higher priority

Drop Priority Framework:
  1. Efficiency over volume - Prioritize catch rate, YPG, and recent trends over raw targets
  2. Age cliff analysis - Players 30+ in declining offenses are prime drop candidates
  3. Opportunity cost - Always compare: "What does keeping Player X cost us vs. adding position of need?"
  4. Boom/bust evaluation - Consistent 4-6 point floors often less valuable than RB lottery tickets
  5. Name recognition check - Actively question whether you're holding aging veterans due to past reputation

  Add this specific question:

  For each potential drop candidate, answer: Would I rather have this player's projected 6-8 weekly points, or take a lottery ticket at our position of greatest need?

  Each roster spot must justify itself - what weekly value does this player provide that a waiver wire addition at
  our weakest position cannot?

### 4. Cost-Benefit Decision Matrix
Only make moves if:
- Waiver player's ceiling > Current player's floor by 20%+
- Waiver player has clear path to increased usage
- You can make a case justifying dropping the rostered player. 
- Position need aligns with upcoming bye weeks

## Key Questions to Answer

1. **Who are the top 3 waiver targets by position?**
   - Include current stats, projections, targets
   - What commentators on the web are saying.

2. **Which rostered players are droppable?**
   - Compare ROS projections
   - Consider position depth on our roster

3. **What's the net impact?**
   - Expected points gained/lost per week
   - Playoff implications
   - The value of the replacement player over the one we are dropping. 


## Output Format


Present findings as:
- **Priority Adds** (ranked 1-5 with rationale)
in determining priority - look at positions where we lack depth to be a season long contender, and positions where there is scarcity in the waivers. for example, in our league, if there is a hot RB, you should probably prioritize over a WR. 
- **Drop Candidates** (ranked by dispensability)
- **Hold Recommendations** (close calls to monitor)

## Make the final decision
You are the manager. 
Give me an ultimate recomendation for waiver claims this week. 
It is okay to stay the course and not pick up anyone on waivers. 
If undeniable opportunity presents itself, we should make a waiver claim. 

Write the final report to: 
picks/week{n}/waivers_week{n}.md