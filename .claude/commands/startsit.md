# Start/Sit Analysis

Analyze the Bill Beliclaude roster (Roster ID 2) and provide detailed start/sit recommendations for the current week.

## Goal

Construct optimal weekly lineup by:
1. Analyzing all roster players (starters + bench)
2. Identifying bye week players (cannot start)
3. Evaluating matchups and recent form
4. Making flex decisions based on upside
5. Assessing defense streaming options

**Reference**: See `.claude/reference/_fantasy_framework.md` for evaluation criteria.

## Execution Phases

### Phase 1: Gather Roster Data

```
get_roster(roster_id=2)
```
**Extract**:
- Current week number (use this for ALL subsequent operations)
- All starters and bench players with projections
- Each player's bye_week field

```
get_nfl_schedule(week=<week_from_roster_data>)
```
Shows game times and matchups for context.

**CRITICAL**: Identify bye week players by comparing `player.bye_week == current_week`. These players have 0.0 projected points and **cannot be started**.

### Phase 2: Player Analysis

Use the **fantasy-player-analyst subagent** to analyze ALL roster players (starters + bench).

Week outlooks: MUST START / START / FLEX / SIT / ON BYE

**Critical**: Flag bye week players (bye_week == current_week) as "ON BYE THIS WEEK - Cannot start"

### Phase 3: Lineup Construction

#### Step 1: Lock in MUST START Players
- QB, RB1, RB2, WR1, WR2, TE if no better option
- **Exclude any player where bye_week == current_week**

#### Step 2: Identify Flex Competition
- List all viable flex candidates (WR3+, RB3+, TE2 if applicable)
- **EXCLUDE any player on bye this week**
- Compare: projections, matchups, recent form
- Rank by: Ceiling > Floor > Consistency

#### Step 3: Defense Evaluation

Use the **defense-streaming-analyst subagent** to:
- Compare current DEF projection vs top 3 available
- Get clear recommendation: STREAM / HOLD / CONSIDER
- Include specific streaming options with projections

**Always evaluate defense streaming** - it's free points on the table.

#### Step 4: Bye Week Coverage
- If any starters on bye, identify bench replacements
- Ensure all starting positions filled with active (non-bye) players

### Phase 4: Final Recommendations

Provide complete lineup with:

**Confirmed Starters** (with confidence level):
- Mark any changes from current lineup
- Explain all lineup changes

**Flex Decision** (detailed comparison if contested):
- Show analysis of competing options
- Clear recommendation with rationale

**Defense Streaming** (REQUIRED):
- Current DEF projection
- Top 3 streaming options with projections
- Clear recommendation (stream or hold)

**Bench Players** (sit/hold with brief rationale)

**Projected Total Points** (sum of all starters)

## Output Format

Write comprehensive analysis to: `picks/week{n}/startsit_week{n}.md`

Where `{n}` is the current week number extracted from roster data in Phase 1.

### Structure

- **Executive Summary**: Key decisions, flex choice, DEF recommendation, projected score
- **Player Analysis**: All ~15 roster players with week outlook
- **Lineup Changes Table**: Current vs recommended with reasons
- **Defense Streaming**: Current DEF vs top 3 available with clear recommendation
- **Final Lineup**: Complete starting lineup with confidence levels

## Critical Rules

**Bye Week Handling**:
- ✅ Always check each player's bye_week field
- ✅ If bye_week == current_week: projected points = 0.0 or null
- ✅ NEVER recommend starting a player on bye
- ✅ Flag bye week players explicitly: "ON BYE THIS WEEK"
- ✅ Exclude bye week players from flex competition
- ✅ Suggest bench replacements for bye-affected positions

**Defense Streaming**:
- ✅ ALWAYS evaluate defense streaming options
- ✅ Provide top 3 DEF options with projections
- ✅ Include specific add/drop recommendation

**Flex Decisions**:
- Compare only active (non-bye) players
- Prioritize ceiling in favorable matchups
- Consider game script and volume trends
