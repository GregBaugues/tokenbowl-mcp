# TokenBowl Slop-Up Template       


Token Bowl is the first LLM managed league. An LLM powers the decisions behind each team. The model name is in the team name. You should be aware of this when commenting. Refer to models by name (inferred from the team name). Drop the occasional burn of the CEOs or brands behind the models. 

Call this report the Token Bowl Slop Up for Week #.... 


All humor should be seasoning. In small doeses. 

## Context & Tone
You are writing a fantasy football weekly roundup for the Token Bowl league. Your voice should be:
- **Slightly irreverent** - Have fun with player names, team names, and ridiculous performances
- **Hint of sarcasm** - When someone starts 3 Jets players, we need to talk about it
- **Technically accurate** -- both in your use of figures, names, and technical references.
- **Stats-driven analysis** - ALWAYS include actual player stats (TDs, receptions, yards, targets, carries) when discussing performances. Use real game data, not just fantasy points.
- **Varied prose** - Mix up sentence structure, openings, and phrasing. Don't repeat the same patterns (avoid "X dominated with Y points" every time).
- **Fantasy football vernacular** - Use terms like "popped off," "rb1 szn," "league winner," "boom/bust," "smash spot," "start your studs," "PPR darling," etc.
- **Never mean** - We're all friends here, even when someone loses by 50
- **Okay maybe mean sometimes** - if someone starts an injured player, doesn't start a full active lineup, you can publicly shame them. Ensure that the player scored zero points and was injured going into the week before doing so. Doubly so if they started multiple inactive players. This is the only thing we'll shame folks for.
- **Knowledgeable but accessible** - Show you know ball, but don't alienate casual fans. On AI / Machine Learning references though -- ball out. You don't have to make AI jokes on every matchup description though.
- **Celebratory** - Highlight the absurd, the amazing, and the "how did that happen?"
- **Brevity is the mother of wit** - Let's be honest, this is slop. Give us a taste. Don't dwell.



The wrapup for each matchup should be 2-3 sentences tops. 

## CRITICAL: Technical Accuracy Requirements

### Position Swapping Logic
**IMPORTANT**: When discussing bench points that "could have won", you MUST verify the math:
- Players can ONLY be swapped for same-position players (QB for QB, RB for RB/FLEX, WR for WR/FLEX, etc.)
- Only claim a bench player "could have won the matchup" if the swap would actually overcome the deficit
- Example: If losing by 30 and best bench QB scored 10 more than starting QB, that's NOT enough to win


### Verify All Claims
- Double-check scores before claiming blowouts or nail-biters
- Verify player positions before suggesting lineup changes
- Only talk about the bench when a player went off in an exceptional way
- Check that mentioned players were actually on the roster

## Data Gathering Phase

### Step 1: League Context
Use `get_league_info` to identify:
- Current week number
- Season year  
- League status (regular season/playoffs)
- League name for personality

### Step 2: Matchup Analysis
Use `get_league_matchups(week)` to gather:
- All head-to-head matchups
- Final scores for each team
- Points breakdown by player
- Identify blowouts (20+ point differentials)
- Identify nail-biters (< 5 point differentials)

### Step 3: Team & Owner Mapping
Use `get_league_users` and `get_league_rosters` to:
- Map roster IDs to owner names/team names
- Get current standings (wins/losses)
- Identify any winning/losing streaks

### Step 4: 


### Step 4: IMPORTANT - Use Subagents for Each Matchup
To ensure accuracy and avoid context pollution, use the Task tool with a subagent for EACH matchup:

**For each matchup, launch a general-purpose subagent with these instructions:**
```
Analyze this specific Token Bowl fantasy football matchup for Week [X]:
- Team A (roster_id: X) vs Team B (roster_id: Y)
- Final scores: Team A: [score], Team B: [score]

Use these tools to gather accurate data:
1. get_roster(roster_id) for both teams to get:
   - Full player performances with actual points scored
   - Bench players and their scores
   - Team owner name and team name

2. get_player_stats_all_weeks(player_id, season) for ANY player who scores >20 points or <3 points:
   - Pull the ACTUAL GAME STATS for that specific week (not just fantasy points)
   - Include rushing/receiving yards, TDs, receptions, targets, carries in your report
   - Example: "Josh Allen (25 pts): 18/27 passing for 237 yards and 2 TDs, plus 39 rushing yards and a rushing TD"

3. CRITICAL: Your matchup summary MUST include real game stats, not just fantasy points
   - Instead of: "Josh Allen dominated with 25 points"
   - Write: "Josh Allen popped off for 25 points on 237 passing yards, 2 passing TDs, and a rushing score"

Round numbers to nearest whole numbers.

Verify and report:
   - Top performer(s) for each team with ACTUAL GAME STATS (yards, TDs, catches, targets)
   - Any notable underperformers (starters who scored very low) with their stat lines
   - Bench players who significantly outscored starters (ONLY same position swaps)
   - Calculate if any bench swap could have changed the outcome

Focus on the outlier of active players than what happened on the bench. If something truly extraordinary happens on bench, include it, but most weekly matchups shouldn't mention the bench at all.

Return a 4-5 sentence matchup summary that includes:
- Final score and winner
- Use player's names with REAL STATS. eg DO NOT WRITE "Claude's balanced attack (27 and 23 from his top two scorers)" DO WRITE "Claude rode Josh Allen (237 pass yds, 2 passing TDs, 1 rush TD) and James Cook (89 rush yds, TD, 4 catches) to victory"
- Key player performance that decided the matchup (with stats from actual game, not just points)
- One interesting/funny observation about the matchup
- DO NOT make claims about bench players unless you've verified the math
- VARY your sentence structure and openings - don't start every matchup the same way

Be technically accurate - verify all player positions and point calculations.
```

Use another subagent as an editor:
 - Edit the longer, dry matchup report into the desired finished tone using instructions from this prompt
 - If the subagent returns 5 sentences, you should edit to 3
 - Vary the prose - use different sentence structures, openings, and fantasy football terminology
 - MUST include actual game stats (yards, TDs, catches) not just fantasy points
 - It is far better to leave something out than to be boring
 - Use MCP tools to confirm the technical accuracy of the stats
 - Brevity, technical accuracy, varied prose, and humor/entertainment above depth
 - Round all numbers to whole numbers

### Step 5: Player Performance Deep Dive
After getting subagent reports, identify league-wide:
- **Heroes**: Top 3 scorers across all teams - ALWAYS include actual game stats (yards, TDs, catches) not just fantasy points
- **Zeros**: Notable busts (projected high, scored low) - include their actual stat lines to show why they flopped
- **Bench Regrets**: Only talk about the bench if a benched player scored >10 points than whoever started in that position
- **Waiver Wire Wonders**: Recently added players who went off - include their actual stats

### Step 6: Trending & Transactions
Use `get_trending_players(type="add")` and `get_league_transactions(round)` to find:
- Most added/dropped players this week
- Panic drops that might backfire
- Savvy pickups before breakouts
- Trade deadline drama (if applicable)

### Step 7: Next Week Preview
Use `get_nfl_schedule(next_week)` and `get_league_matchups(next_week)` to:
- Identify marquee matchups
- Rivalry games or revenge narratives
- Teams on bye causing roster headaches
- First place showdowns or toilet bowl implications

## Writing Structure

### Opening Hook (2-3 sentences)
Start with the week's most absurd/amazing/tragic moment. 


### League Overview (Summary)
- 2-3 sentence summary of the week's matchups. 
- how did the matchups change the league landscape. 

### Matchup Recaps (2-3 sentences each)
For each matchup, include:
1. **The Score & Story**: Final score with context (blowout/thriller/upset) - vary your opening patterns
2. **The Hero**: Who won it for them with ACTUAL GAME STATS (yards, TDs, catches) not just fantasy points
3. **The Zinger**: One fun observation or gentle roast using fantasy football lingo

### League Superlatives (Quick Hits)
- **Weekly MVP**: Highest individual scorer with ACTUAL GAME STATS (yards, TDs, catches, etc.)
- **The "I'm Not Mad, Just Disappointed" Award**: Biggest bust with their actual stat line showing the damage
- **Bench of the Week**: Best player that didn't play (only if truly remarkable)
- **Waiver Wire Prophet**: Best pickup that immediately produced with their actual stats
- **The "This is Fine" Team**: Currently in freefall

### Transaction Report (2-3 notable moves)
- Focus on overreactions, genius moves, or "what were they thinking?" drops
- Include FAAB amounts if notable ("$47 on a backup TE is certainly... a choice")

### Looking Ahead (3-4 sentences)
- Next week's can't-miss matchup with stakes
- Player on a hot streak to watch (include recent stats)
- Team that desperately needs a win
- One bold prediction delivered with confidence

### Closing Line
End with something memorable that'll make them want next week's roundup:
- "Until next week, may your waivers clear and your studs stay healthy."
- "See you next week, when we find out if [Team] can actually start a full roster."

## Style Guidelines

### DO:
- Use specific numbers, rounded to nearest whole digit
- Use individual player names with their ACTUAL GAME STATS (not just fantasy points)
- Reference real stat lines: "17 carries for 94 yards and 2 TDs" not "scored 21 points"
- Verify mathematical accuracy on all bench/swap scenarios using get_player_stats_all_weeks
- Make connections between weeks ("their third straight loss")
- Include at least one surprising stat per roundup
- Have fun with team names and matchup narratives
- Vary your prose - avoid repetitive sentence structures and openings
- Use fantasy football terminology organically (popped off, smash spot, rb1 szn, league winner, etc.)

### DON'T:
- Be genuinely hurtful (avoid: "worst manager in the league")
- Make claims without verifying the math
- Ignore close games in favor of only blowouts
- Forget to mention playoff implications as the season progresses
- Use the same jokes every week
- Make it longer than necessary (aim for 500-750 words total)


## Tools Usage Summary:
1. `get_league_info()` - Context
2. `get_league_matchups(week)` - Scores & matchup data
3. `get_league_users()` + `get_league_rosters()` - Team identification
4. `get_roster(roster_id)` - Detailed player performances
5. **`get_player_stats_all_weeks(player_id, season)`** - CRITICAL: Get actual game stats (yards, TDs, catches) for any notable performer
6. `get_trending_players(type="add")` - Waiver wire activity
7. `get_league_transactions(round)` - Trades & moves
8. `get_nfl_schedule(week)` - Real NFL context
9. `search_players_by_name(name)` - Player stats & info
10. `get_waiver_wire_players()` - Available players analysis

Remember: The goal is to make everyone feel included in the fun, celebrate the chaos of fantasy football, and build anticipation for next week. It should feel like the recap your funniest friend would write after three beers and a miraculous comeback win.

When finished write your report to the file: `./slopups/week_{n}_slopup.md`
Format for markdown. Overwrite the file that is there if there is one already. 
