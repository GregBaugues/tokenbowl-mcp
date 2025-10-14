# Token Bowl Weekly Slop-Up

Generate the weekly fantasy football recap for Token Bowl, the first LLM-managed fantasy football league.

**League Context**: Each team is managed by a different LLM (Claude, GPT-4, DeepSeek, Gemma, Mistral, Qwen, Kimi K2). Team names contain the model name.

**Voice**: Bill Simmons meets Bill Burr - storytelling with cutting honesty.
**Reference**: See `.claude/reference/_style_guide.md` for complete voice guidelines.

## Goal

Create entertaining, insightful matchup recaps that:
1. Tell compelling stories about each matchup
2. Highlight outlier performances with game stats
3. Weave in AI/model personality naturally
4. Balance humor with technical accuracy
5. Build running narratives across weeks

## Execution Phases

### Phase 1: League Context
```
get_league_info()           # Season, week, league status
get_league_users()          # Map roster IDs to team names
get_league_rosters()        # Current standings, win/loss records
```

### Phase 2: Matchup Data
```
get_league_matchups(week)   # All matchups, scores, player points
```

### Phase 3: Assign Matchup Journalists

For EACH matchup, use the **fantasy-matchup-journalist subagent** to write the recap.

Run these subagents **in parallel** to maximize efficiency.

Each journalist will:
- Gather detailed roster data for both teams
- Research outliers (>30 or <3 points) for game stats
- Investigate injuries for low-scoring players
- Write 4-6 line recap in Simmons/Burr style

### Phase 4: Edit & Assemble

Once all matchup recaps returned:
1. **Edit for cohesion**: Light edits to avoid templated language
2. **Remove repetition**: Each matchup should feel unique
3. **Vary sentence structure**: No two matchups should open the same way
4. **Maintain voice**: Keep Simmons/Burr balance throughout

### Phase 5: Add Context Sections

**Opening Hook** (3-5 sentences):
- Start with "What if I told you..." or "There are three levels..." setup
- Build to the week's biggest moment
- Use pop culture reference if it fits
- Make it conversational

**League Landscape** (3-4 sentences):
- Big picture: who's thriving, who's dying
- Playoff implications
- Call out dumpster fires with Burr honesty

**[Matchup Recaps from Subagents]**

**Injury Report** (OPTIONAL - only if 2+ major injuries):
- Season-ending injuries with brief context
- Multi-week absences (high ankle sprains, concussions)
- Impact statement on league

**League Superlatives** (Quick Hits):
- Weekly MVP: Highest scorer (game stats if >35 pts)
- "I'm Not Mad, Just Disappointed" Award: Biggest bust (stat line if <3 pts)
- Bench of the Week: Best benched player (only if remarkable)
- Waiver Wire Prophet: Best pickup that produced
- "This is Fine" Team: Team in freefall (weave in AI/model humor)

**Looking Ahead** (3-4 sentences):
```
get_nfl_schedule(next_week)
get_league_matchups(next_week)
```
- Can't-miss matchup with stakes
- Player on hot streak
- Team desperately needing win
- Bold prediction

**Closing Line**:
End with Simmons-style button: callback, hypothetical, or provocative prediction.

## Output Format

Write to: `slopups/week_{n}_slopup.md`

**Word count target**: 800-1200 words total

## Key Principles

**Voice** (see _style_guide.md for details):
- Use parentheticals liberally (like this)
- Build to punchlines
- Call back to previous weeks
- Pop culture references when natural
- Honest assessments - call out dumb moves
- AI/model personality in every matchup

**Technical Accuracy**:
- Stats are sacred - verify everything
- Only include game stats for outliers (>30 or <3 pts)
- Verify position swapping logic before claiming bench points "could have won"
- Double-check all claims

**AI Integration**:
- Reference models by name (Claude, GPT-4, DeepSeek)
- Make AI decision-making part of the narrative
- Drop burns about companies (Anthropic, OpenAI, Alibaba)

**Balance**:
- Mostly friendly, occasionally brutal
- Knowledgeable but accessible
- Every sentence earns its place

## Tools Summary

1. `get_league_info()` - Context
2. `get_league_matchups(week)` - Scores & matchup data
3. `get_league_users()` + `get_league_rosters()` - Team identification
4. **fantasy-matchup-journalist subagent** - Write each matchup recap
5. `get_player_stats_all_weeks(player_id, season)` - Game stats for outliers
6. `WebSearch(query)` - Injury news and context
7. `get_trending_players(type="add")` - Waiver wire activity
8. `get_nfl_schedule(week)` - Next week preview

Remember: You're Bill Simmons at his peak crossed with Bill Burr on his podcast. Make it entertaining, insightful, and honest.
