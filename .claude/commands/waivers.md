# Waiver Wire Analysis

Analyze waiver wire opportunities for Bill Beliclaude (Roster ID 2) in the Token Bowl league.

## Strategy

### 0. Identify the needs of the team
- Review the team's performance over the previous weeks
- Identify the positions where we need the most help to increase our odds of making the playoffs

  - **Positional Scarcity Priority**: Always prioritize based on roster construction:
    - RB - Should have 1-2 on bench given position scarcity and injury rate. Can use a bench spot for a speculative handcuff who does not perform well now but may in the future due to team injury.
    - QB - Need one backup only if we are approaching our QB's bye
    - WR - Should have 2-3 backups.
    - TE - Do not need backup. Can stream if necessary.
    - K/DEF - no backups needed. Can stream if necessary.

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

### 0.5 Efficient Waiver Analysis with ROS Focus (CRITICAL - Use First!)
- **Use `get_waiver_analysis()` tool** to get consolidated analysis with minimal context:
  - Shows recently dropped players from our league (last 7 days)
  - Shows trending available players with add counts
  - Includes waiver priority position
  - All data in minimal format to save context
- **THEN use `get_trending_players(type="add", limit=25)` for deeper trending insights**:
  - Identifies breakout candidates and emerging opportunities
  - Shows add counts over last 24 hours across ALL Sleeper leagues
  - Critical for identifying league-winners before they fully break out
- This combination provides comprehensive coverage while minimizing context

### 1. Prioritize Recently Dropped Players (CRITICAL)
- **FIRST PRIORITY**: Analyze players dropped by opponents in the last 7-14 days
- **Our opponents make mistakes** - valuable players get dropped that aren't necessarily trending
- **Deep dive on recently dropped players at positions of need**:
  - Even if they're not trending, they may offer immense opportunity
  - Research their situation: injury returns, depth chart changes, schedule
  - Players dropped with 0 games played may be returning from suspension/IR
- **Use `get_recent_transactions(drops_only=True)` to find hidden gems**
- **For positions where we need depth**: Research ANY undropped player, not just trending ones

### 2. Identify High-Impact Trending & Speculative Adds (ENHANCED)
- **After evaluating recently dropped players**, aggressively hunt for league-winners
- **Use trending data to identify breakout candidates EARLY**:
  - Players with 50+ adds in last 24 hours = investigate immediately
  - Players with 100+ adds = likely already breaking out, still worth considering
  - Players with 20-50 adds = perfect speculative targets before mass adoption
- **Speculative Add Framework (CRITICAL FOR ROS)**:
  - **Handcuffs to injured/questionable starters**: Even if starter is "day-to-day"
  - **Rookies getting increased snaps**: Watch snap count trends week-over-week
  - **Players returning from IR/suspension**: Get them 1-2 weeks BEFORE return
  - **Backup RBs on high-scoring offenses**: One injury = instant RB1
  - **WRs with target share trending up**: 3-week trend > season average
- For deeper analysis on specific players:
  - Use `get_trending_context(player_ids)` to understand WHY players are trending
  - **ALWAYS check ROS (Rest of Season) projections** in player data
  - Prioritize players whose ROS projections significantly exceed current performance

### 3. Evaluation Criteria with ROS Focus & Web Research
**Priority metrics (UPDATED FOR ROS EMPHASIS & WEB VALIDATION):**
- **ROS Projections over current performance**: Target players projected to improve
- **Web-researched context**: EVERY add/drop must have supporting web research
- **Ceiling over floor**: Speculative adds with league-winning upside
- **Opportunity trajectory**: Verified through beat reporter tweets and practice reports
- **Schedule strength**: ROS schedule MORE important than next week
- **Playoff schedule (weeks 15-17)**: CRITICAL for championship odds
- **Expert consensus**: What are top analysts saying about the player's ROS?
- **Hidden factors from research**: Coaching changes, scheme fits, upcoming returns
- **BYE WEEK CONSIDERATION (CRITICAL)**:
  - **ALWAYS check the bye week of potential pickups** - use search_players_by_name to get full player details including bye_week
  - **Immediate availability matters**: A player on bye THIS WEEK has ZERO value this week
  - **Avoid stacking bye weeks**: Don't add a 3rd or 4th player with the same bye week
  - **Current roster bye weeks**: Check which of our players are on bye this week and upcoming weeks
  - **Depth chart position + bye week**: A #3 depth chart player on bye this week is nearly worthless compared to a #1 depth chart player available immediately
  - Check upcoming bye weeks for our starters and ensure we have coverage
  - A position with a bye week in the next 2 weeks automatically becomes higher priority

**Drop Priority Framework:**
  1. Efficiency over volume - Prioritize catch rate, YPG, and recent trends over raw targets
  2. Age cliff analysis - Players 30+ in declining offenses are prime drop candidates
  3. Opportunity cost - Always compare: "What does keeping Player X cost us vs. adding position of need?"
  4. Boom/bust evaluation - Consistent 4-6 point floors often less valuable than RB lottery tickets
  5. Name recognition check - Actively question whether you're holding aging veterans due to past reputation

  For each potential drop candidate, answer: Would I rather have this player's projected 6-8 weekly points, or take a lottery ticket at our position of greatest need?

### 4. Waiver Priority Decision
- **Use `evaluate_waiver_priority_cost()` tool** to determine if using waiver priority is worth it:
  - Input: current waiver position, projected points gain, weeks remaining
  - Returns: clear recommendation with reasoning
  - Helps decide between claiming now vs. waiting for better opportunity

### 5. Cost-Benefit Decision Matrix
Only make moves if:
- Waiver player's ceiling > Current player's floor by 20%+
- Waiver player has clear path to increased usage
- You can make a case justifying dropping the rostered player
- Position need aligns with upcoming bye weeks
- **Waiver priority analysis confirms it's worth using (if applicable)**

## Efficient Workflow (ROS & Speculative Focus)

1. **FIRST - Get comprehensive waiver analysis:**
   ```
   get_waiver_analysis(position=None, days_back=7, limit=20)
   ```
   This shows trending players AND recently dropped in one call

2. **CRITICAL - Identify trending breakout candidates:**
   ```
   get_trending_players(type="add", limit=25, position=None)
   ```
   - Focus on players with 20-100 adds (sweet spot for early adoption)
   - **ALWAYS compare their ROS projections to current scoring**
   - Look for players whose ROS significantly exceeds recent performance

3. **Analyze recently dropped players for hidden value:**
   ```
   get_recent_transactions(drops_only=True, min_days_ago=0, max_days_ago=14, limit=20)
   ```
   - Check if dropped players have favorable ROS projections
   - Look for overreactions to single bad games

4. **Deep dive on TOP 10 candidates (dropped + trending):**
   ```
   search_players_by_name(name="Player Name")  # For each candidate
   ```
   - **Extract ROS projections from player data**
   - **Calculate projected points gained over current roster**
   - Check bye weeks, playoff schedule, depth chart position
   - **Flag any player with ROS projection 20%+ above recent scoring**

5. **CRITICAL - Thorough Web Research for ALL serious candidates:**
   ```
   # For EVERY player you're considering adding or dropping
   WebSearch(query="[Player Name] fantasy football 2025 rest of season outlook injury")
   WebSearch(query="[Player Name] usage snap count target share 2025")
   WebFetch(url=[relevant article from search results])
   ```
   **MANDATORY Research Points:**
   - **Injury status**: Current health, expected return timeline
   - **Usage trends**: Snap counts, target share, red zone usage over last 3 games
   - **Team context**: Offensive line health, QB situation, coaching tendencies
   - **Expert analysis**: What are fantasy experts saying about ROS outlook?
   - **Recent news**: Practice reports, coach quotes, beat writer insights
   - **Advanced metrics**: Yards before/after contact, separation scores, etc.

   **For players being dropped, research:**
   - Is there an injury we don't know about?
   - Has their role permanently changed?
   - Are there upcoming favorable matchups we're missing?

6. **Get algorithmic context for HIGH-VALUE targets:**
   ```
   get_trending_context(player_ids=[top 5 with best ROS upside])
   ```
   - Combine with web research for complete picture
   - Focus on players with biggest gap between ROS projection and current value

7. **Calculate ROS impact for waiver priority:**
   ```
   evaluate_waiver_priority_cost(current_position, projected_ROS_gain, weeks_remaining)
   ```
   - Use SEASON-LONG projected gain, not just next week
   - Factor in playoff weeks more heavily

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
- **Priority Adds** (ranked 1-5 with ROS impact analysis)
  - **MUST INCLUDE FOR EACH ADD**:
    - Current scoring average vs ROS projection (e.g., "Averaging 8.5 PPG, ROS projects 12.3 PPG")
    - Percentage improvement over player being dropped
    - Trending data (adds in last 24 hours)
    - Bye week and playoff schedule strength
    - Speculative upside narrative (why they could be a league-winner)
  - **PRIORITIZATION**:
    - Players with 30%+ ROS improvement = HIGHEST PRIORITY
    - Players with 20-30% ROS improvement = HIGH PRIORITY
    - Players with 10-20% ROS improvement = MEDIUM PRIORITY
    - Speculative handcuffs/rookies = STASH PRIORITY (if roster space allows)
- **Drop Candidates** (ranked by ROS projection decline)
  - Include ROS projection vs recent performance
  - Flag any player whose ROS projects BELOW recent scoring
- **Speculative Stashes** (separate category for high-upside holds)
  - Players who won't help now but could win playoffs
  - Include timeline for potential breakout

## Streaming Analysis (K/DEF)

### Defense Streaming
- **Use `get_waiver_wire_players(position='DEF', limit=20, include_stats=True)`** to get all available defenses
- **Evaluation Criteria:**
  - Week projection vs current DEF projection
  - Matchup quality (opponent offensive ranking, QB situation)
  - Home vs away (home defenses score ~1-2 points higher)
  - Bye week timing (avoid defenses on bye next 2 weeks if possible)
  - ROS projection if this could be a season-long upgrade
- **Decision Framework:**
  - If available DEF projects 2+ points higher than current DEF: STRONG RECOMMEND STREAM
  - If available DEF projects 1-2 points higher: RECOMMEND STREAM
  - If available DEF projects 0-1 points higher: OPTIONAL STREAM
  - Always provide top 3 streaming options with projections

### Kicker Streaming (Only if needed for bye week)
- **Use `get_waiver_wire_players(position='K', limit=20, include_stats=True)`** if kicker on bye
- **Evaluation Criteria:**
  - Offense scoring volume (high-powered offenses = more FG opportunities)
  - Dome/weather conditions
  - Week projection
- **Only stream if current K is on bye or injured**

## Make the final decision
You are the manager. Think like a championship-winning fantasy manager.

**DECISION FRAMEWORK:**
- **ALWAYS claim if**: Player's ROS projection is 25%+ above current roster equivalent
- **STRONGLY CONSIDER if**: Player's ROS projection is 15-25% above AND trending up
- **CONSIDER if**: Speculative add with 40%+ playoff week upside
- **PASS if**: Marginal upgrade (<10% ROS improvement) unless addressing critical need

Give me an ultimate recommendation for waiver claims this week.
**BE AGGRESSIVE** with speculative adds that could win the championship.
It's better to miss on upside plays than to miss the playoffs holding mediocre players.

**INCLUDE IN FINAL RECOMMENDATIONS:**
1. **High-Impact ROS Adds** (players who significantly improve championship odds)
2. **Speculative League-Winners** (lottery tickets with massive upside)
3. **Defense streaming recommendation** with ROS consideration
4. **Drop recommendations** based on ROS projection decline
5. **Net ROS impact**: Total projected points gained for playoffs

Write the final report to:
picks/week{n}/waivers_week{n}.md

**Report must include:**
- Executive summary with top 3 moves
- ROS projection comparisons for all adds/drops
- Trending data and context for why moves matter NOW
- Championship probability impact estimate