# Start/Sit Analysis

Analyze the Bill Beliclaude roster (Roster ID 2) and provide detailed start/sit recommendations for the current week.

## Phase 1: Gather Roster Data

1. **Get current roster with `get_roster(roster_id=2)`**
   - This returns all starters and bench players with complete data
   - Each player includes: name, position, team, bye_week, projected points, ROS projections, injury status
   - **CRITICAL: The roster response includes `"week": N` field - THIS IS THE CURRENT WEEK NUMBER**
   - **Extract this week number and use it for ALL subsequent operations**

2. **Get NFL schedule with `get_nfl_schedule(week=<week_from_roster_data>)`**
   - Pass the week number from the roster data (step 1)
   - DO NOT assume or hardcode the week number
   - Shows game times and matchups for context

3. **CRITICAL: Identify bye week players**
   - Extract `bye_week` field from each player
   - **Compare each player's bye_week to the current week from roster data**
   - **IF player.bye_week == current_week: player is ON BYE and has 0.0 projected points**
   - Create a list of all bye week players to exclude from starting lineup

## Phase 2: Player Analysis

Use the Fantasy Player Analyst agent to analyze ALL roster players (starters + bench).

**For each player, provide:**

1. **Player Capsule** (2-3 sentences):
   - **BYE WEEK CHECK**: If player.bye_week == current_week, START with "ON BYE THIS WEEK - Cannot start"
   - Recent performance trend (last 2-3 games)
   - Week matchup quality (opponent defense vs position)
   - Key opportunity metrics (targets, snap %, red zone usage)
   - Injury status if applicable

2. **Week Outlook**:
   - **MUST START** - Elite option, no question (never use for bye week players)
   - **START** - Strong play with solid floor (never use for bye week players)
   - **FLEX CONSIDERATION** - Viable but boom/bust or competing for spot
   - **SIT** - Better options available or unfavorable situation
   - **ON BYE** - Cannot start this week (projected = 0.0)

3. **Ceiling/Floor**: Quick hit on upside vs downside for current week

## Phase 3: Lineup Construction

### Step 1: Lock in MUST START players (NOT on bye)
- QB, RB1, RB2, WR1, WR2, TE1, K, DEF if no better options
- Exclude any player where bye_week == current_week

### Step 2: Identify Flex Competition
- List all viable flex candidates (WR3+, RB3+, TE2 if applicable)
- **EXCLUDE any player on bye this week**
- Compare projections, matchups, and recent form
- Rank by: Ceiling > Floor > Consistency

### Step 3: Defense Evaluation
- **ALWAYS evaluate if defense should be streamed**
- Use `get_waiver_wire_players(position='DEF', limit=10, include_stats=True)`
- Compare current DEF projection vs top 3 available options
- Recommendation framework:
  - 2+ points higher: STRONG RECOMMEND STREAM
  - 1-2 points higher: RECOMMEND STREAM
  - 0-1 points higher: OPTIONAL
- **Include specific streaming options with projections in final report**

### Step 4: Bye Week Coverage (if applicable)
- If any starters are on bye, identify bench replacements
- Ensure all starting positions are filled with active (non-bye) players

## Phase 4: Final Recommendations

Provide a complete lineup with:

1. **Confirmed Starters** (with confidence level)
   - Mark any changes from current lineup
   - Explain all lineup changes

2. **Flex Decision** (detailed comparison if contested)
   - Show analysis of competing options
   - Clear recommendation with rationale

3. **Defense Streaming** (REQUIRED)
   - Current DEF projection
   - Top 3 streaming options with projections
   - Clear recommendation (stream or hold)

4. **Bench Players** (sit/hold with brief rationale)

5. **Projected Total Points** (sum of all starters)

## Critical Rules

**BYE WEEK HANDLING (CRITICAL):**
- ✅ **ALWAYS check each player's bye_week field**
- ✅ **IF bye_week == current_week: projected points = 0.0 or null**
- ✅ **NEVER recommend starting a player on bye**
- ✅ **Flag bye week players explicitly in analysis: "ON BYE THIS WEEK"**
- ✅ **Exclude bye week players from flex competition**
- ✅ **Suggest bench replacements for any starting position affected by bye**

**DEFENSE STREAMING:**
- ✅ **ALWAYS evaluate defense streaming options**
- ✅ **Provide top 3 DEF options with projections**
- ✅ **Include specific add/drop recommendation**

**FLEX DECISIONS:**
- Compare only active (non-bye) players
- Prioritize ceiling in favorable matchups
- Consider game script and volume trends

## Output Format

Write comprehensive analysis to:
**picks/week{n}/startsit_week{n}.md**

Where `{n}` is the current week number extracted from the roster data in Phase 1.

Include:
- Executive summary of key decisions
- Individual player analysis (all 15 roster players)
- Lineup comparison table (current vs recommended)
- Defense streaming analysis with options
- Final recommendations with confidence levels
- Projected score range
