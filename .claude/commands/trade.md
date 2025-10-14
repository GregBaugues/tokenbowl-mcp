# Trade Analysis & Proposal Generator

Analyze trade opportunities for Bill Beliclaude (Roster ID 2) in the Token Bowl league.

**Reference**: See `.claude/reference/_fantasy_framework.md` for evaluation criteria.

## Goal

Identify and execute value-creating trades by:
1. Analyzing our roster needs and trade assets
2. Profiling opponents for exploitable weaknesses
3. Constructing 60/40 trades (appear fair, favor us)
4. Timing proposals for maximum psychological impact
5. Maximizing championship odds through roster optimization

**Untouchables**: Josh Allen and James Cook are not available for trade.

## Execution Phases

### Phase 1: Assess Our Roster

Use the **roster-analyst subagent** to:
- Identify positions with critical needs (0-1 bench depth)
- Identify positions with tradeable surplus (3+ bench depth)
- Evaluate which starters are underperforming
- Determine our expendable assets (bench depth, aging veterans)

**Trade Asset Identification**:
- Players at overstocked positions (3+ bench)
- Underperformers with name value (sell high on reputation)
- High-floor veterans we can package for high-ceiling players
- Players with unsustainable TD rates (sell before regression)

### Phase 2: Scout Opponents

Use the **opponent-scout subagent** to:
- Analyze all 9 opposing rosters for weaknesses and strengths
- Identify teams with complementary needs (they need what we have)
- Profile vulnerable managers (losing streaks, injuries, bye week crunches)
- Find exploitable psychological angles

**Target Identification**:
- Teams with 0-1 bench at positions where we have surplus
- Teams dealing with recent injuries or bye week hell
- Managers panicking (0-3, 1-4 starts) who overpay
- Teams with talent stuck on bench (want to "unlock" value)

### Phase 3: Research Trade Targets

For top trade target candidates, use the **player-researcher subagent** to:
- Verify current production is sustainable (or inflated)
- Analyze playoff schedule (weeks 15-17) strength
- Check for hidden injury concerns or usage red flags
- Compare expert ROS projections vs market perception

This helps us:
- **Buy low**: Target underperformers with strong underlying metrics
- **Sell high**: Move overperformers before regression
- **Exploit information asymmetry**: We know things they don't

### Phase 4: Construct Trade Proposals

Build proposals that are **60/40 in our favor**:

**Psychological Tactics**:
- Frame as "helping them" with bye weeks or injuries
- Emphasize recent good games of players we're trading away
- Downplay concerns about players we're acquiring
- Use 2-for-1 trades (quantity for quality favors us)
- Package mediocre starter with bench player to acquire stud

**Timing Strategy**:
- Propose after our players have good games (peak value)
- Target managers after their players have bad games (panic)
- Strike during bye week desperation (time-sensitive need)

**Value Assessment**:
- Calculate net points gained/lost per week
- Consider playoff schedule implications
- Evaluate injury risk differential
- Ensure we're exploiting valuation discrepancies

### Phase 5: Prioritize & Execute

Rank proposals by:
1. Net expected points per week (+2 or more)
2. Fills critical roster need (0-1 bench positions)
3. Exploits clear desperation/naivety
4. Improves playoff week matchups

## Output Format

Write to: `picks/week{n}/trades_week{n}.md`

### Structure

**Our Roster Analysis**:
- Positions of need (ranked by priority)
- Trade assets (ranked by expendability)
- Weakest starters to upgrade

**Top 3 Trade Targets**:
For each target manager:
- Their roster weaknesses that align with our assets
- Their surplus positions that align with our needs
- Psychological angle to exploit (panic, bye week, injury)
- Specific players to target from their roster

**Recommended Trade Proposals** (3-5):
```
TRADE #X:
We Send: [Players]
We Receive: [Players]
Target Manager: [Name/Roster ID]

Pitch Angle: [How to frame this trade]
Hidden Value: [Why this actually favors us]
Expected Weekly Gain: [+/- points]
ROS Impact: [Championship odds improvement]
```

**Negotiation Strategy**:
- Initial offer (slightly aggressive)
- Fallback offer (if rejected)
- Walk-away point (minimum acceptable)
- Timeline (before waivers, after games, etc.)

**Final Recommendation**:
- Which trade to send first
- Backup options if rejected
- Weekly point projections with/without trade

## Trade Philosophy

**Core Principles**:
1. **Target desperation** - Losing teams make bad trades
2. **Exploit information asymmetry** - We know ROS projections better
3. **Sell high** - Trade after our players' big games
4. **Buy low** - Target after their players' bad games
5. **Package mediocrity** - 2-for-1 favors side getting 1 stud
6. **Playoff schedule** - Weeks 15-17 matchups determine championships

**Decision Matrix** - Only Execute If:
- Net positive expected points per week (+2 or more)
- Fills critical roster need (0-1 bench depth positions)
- Exploits clear valuation discrepancy
- Improves playoff week matchups
- Takes advantage of manager desperation/naivety

## What NOT to Do

- Don't propose obviously lopsided trades (kills future negotiations)
- Don't trade Josh Allen or James Cook (untouchables)
- Don't create new holes (don't trade away depth to upgrade)
- Don't ignore playoff schedule (weeks 15-17)
- Don't trade based on name recognition alone (check underlying metrics)
