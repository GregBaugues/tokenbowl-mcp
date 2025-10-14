# Fantasy Football Analysis Framework

Core principles for evaluating players and making start/sit, waiver, and trade decisions.

## Evaluation Criteria

### Opportunity Metrics (Most Important)
- **Target share** - Percentage of team targets (WR/TE)
- **Snap percentage** - Time on field (all positions)
- **Red zone usage** - Touches inside the 20 (RB/WR/TE)
- **Route participation** - Percentage of pass plays (WR/TE)
- **Carry share** - Percentage of team rushes (RB)

### Performance Metrics
- **Recent trend** - Last 3 games weighted more than season average
- **Efficiency** - Yards per carry, yards per target, catch rate
- **Game script fit** - Does their role match expected game flow?
- **Home vs away** - Some players have significant splits

### Situational Factors
- **Matchup quality** - Opponent defense ranking vs position
- **Weather conditions** - Wind, rain, cold (especially for passing games)
- **Primetime games** - Some players perform better on national TV
- **Divisional matchups** - Familiarity can reduce scoring
- **Revenge games** - Narrative matters (players vs former teams)

### Forward-Looking Indicators
- **Rest of Season (ROS) projections** - Future outlook vs current scoring
- **Upcoming schedule** - Next 3-4 weeks and playoff schedule (weeks 15-17)
- **Bye week timing** - Immediate availability matters
- **Injury trajectory** - Is player recovering or declining?
- **Depth chart changes** - Competition for snaps/targets

## Positional Priorities

### Roster Construction Guidelines
- **RB** - Most scarce, highest injury rate. Keep 3-4 rostered (2-3 starters + 1-2 bench)
  - Speculative handcuffs valuable even if not producing now
- **WR** - More available, deeper benches. Keep 4-6 rostered (3 starters + 1-3 bench)
- **QB** - Only need backup if starter's bye approaching (within 2 weeks)
- **TE** - One starter sufficient, can stream if needed
- **K/DEF** - No bench spots, stream weekly based on matchups

### Priority Framework for Adds
1. First address positions with 0-1 bench players (critical need)
2. Then consider talent upgrades at positions with 2+ bench players
3. Account for immediate bye weeks (next 2 weeks = higher priority)
4. RB > WR when talent is comparable (due to scarcity)
5. Never prioritize a position where we have 4+ bench players unless it's a clear league-winner

## Decision Frameworks

### Waiver Adds - Only Claim If:
- Player's ROS projection is 20%+ above current roster equivalent
- Fills critical roster need (position with 0-1 bench depth)
- Clear path to increased usage (injury, depth chart change)
- Waiver priority cost justified by season-long impact

### Start/Sit - Start Player If:
- Opportunity metrics trending up (snaps, targets, carries)
- Favorable matchup (opponent weak vs position)
- Recent performance strong (last 2-3 games)
- NOT on bye week (always check bye_week field)

### Trade - Only Execute If:
- Net positive expected points per week (+2 or more)
- Fills critical roster need (0-1 bench depth positions)
- Exploits clear valuation discrepancy
- Improves playoff week matchups (weeks 15-17)

## Common Fantasy Principles

- **"Volume is king"** - Opportunity matters more than efficiency early season
- **"Start your studs"** - Don't overthink elite players, even in tough matchups
- **"Sell high, buy low"** - Trade after big games, acquire after bad ones
- **"Regression to the mean"** - Unsustainable TD rates will normalize
- **"Trust the process"** - Focus on opportunity, not week-to-week variance
- **"Playoff schedule matters"** - Weeks 15-17 matchups can determine championships
- **"Handcuff your stud RBs"** - Insurance against injury at scarce position

## Red Flags

- **Declining snap percentage** (3-week trend down)
- **Target share dropping** (losing work to teammates)
- **Age + declining offense** (30+ years old on bad teams)
- **Injury-prone with recurring issues**
- **Bad offensive line** (especially impacts RBs and QBs)
- **Coaching changes** that don't fit player's skillset
