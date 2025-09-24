# Trade Analysis & Proposal Generator

Analyze trade opportunities for Bill Beliclaude (Roster ID 2) in the Token Bowl league.

## Strategy

### 0. Team Needs Assessment
- Review Bill Beliclaude's roster performance over previous weeks
- Identify positions of critical need to improve playoff odds:
  - **Positional Depth Analysis**:
    - 0-1 bench players = CRITICAL NEED (highest trade priority)
    - 2 bench players = ADEQUATE DEPTH (medium priority)
    - 3+ bench players = TRADEABLE ASSETS (use as trade bait)
    - RB depth prioritized over WR due to injury rates and scarcity
  - Consider upcoming bye weeks (next 2-3 weeks highest priority)
  - Identify our weakest starting positions based on recent performance
- **Untouchables**: Josh Allen and James Cook are not available for trade

### 1. Identify Trade Assets (Our Expendable Players)
- Analyze our roster for tradeable pieces:
  - Players at overstocked positions (3+ bench depth)
  - Underperforming starters with name value
  - High-floor veterans we can package for high-ceiling players
  - Players with favorable past performance but declining opportunity
- Use efficiency metrics to identify overvalued assets:
  - Players with unsustainable TD rates
  - Players benefiting from temporary injury situations
  - Aging veterans coasting on reputation

### 2. League-Wide Roster Analysis
- Scan all 9 opposing rosters to identify:
  - **Their weaknesses**: Positions where they have 0-1 bench players
  - **Their strengths**: Positions where they have surplus (3+ bench)
  - **Recent injuries**: Teams dealing with IR/OUT designations
  - **Bye week crunches**: Teams facing multiple byes at same position
- Target managers with complementary needs (they need what we have excess of)

### 3. Trade Target Identification
For each opposing roster, identify:
- **Buy-low candidates**:
  - Players underperforming but with positive underlying metrics
  - Players returning from injury/suspension
  - Players in new situations with upside
  - Talented players on struggling teams
- **Sell-high opportunities**:
  - Our players at peak value (recent big games)
  - Players with unsustainable production
  - Veterans we can move based on name recognition
- Focus on acquiring:
  - High target share players
  - Players with increasing snap counts
  - Backfield leaders and handcuffs
  - Players with soft upcoming schedules

### 4. Trade Psychology & Leverage
- **Manager Profiling**:
  - Identify managers who are panicking (0-3, 1-4 starts)
  - Target managers who overreact to recent performances
  - Find managers with fan bias for certain teams/players
- **Negotiation Tactics**:
  - Frame trades as "helping them" with their bye weeks
  - Emphasize recent good games of players we're trading away
  - Downplay injuries/concerns about players we're acquiring
  - Use 2-for-1 trades to make them feel they're getting more value
  - Package a mediocre starter with a bench player to acquire a stud

### 5. Trade Proposal Construction
Build proposals that are:
- **Weighted 60/40 in our favor** (appear fair but favor us)
- **Psychologically appealing**:
  - Offer name-brand players for lesser-known studs
  - Package quantity for quality
  - Target their emotional attachments and biases
- **Strategically timed**:
  - Propose after our players have good games
  - Target managers after their players have bad games
  - Strike during bye week desperation

### 6. Value Assessment Framework
For each potential trade:
- Calculate net points gained/lost per week
- Consider playoff schedule implications
- Evaluate injury risk differential
- Assess the "winner" using multiple trade calculators
- Ensure we're exploiting information asymmetry

## Key Questions to Answer

1. **What are our 3 biggest roster needs?**
   - Include current depth and bye week coverage
   - Identify specific player archetypes needed

2. **Which managers are most vulnerable to trade?**
   - Recent losses, injury problems, bye week issues
   - Historical trade patterns and tendencies

3. **What are our best trade packages?**
   - 2-for-1 upgrades at positions of need
   - Selling high on overperformers
   - Buying low on underperformers

4. **Net impact analysis:**
   - Expected points gained per week
   - Playoff roster improvement
   - Risk/reward assessment

## Output Format

### Trade Proposal Summary
Present findings as:

1. **Our Roster Needs** (ranked by priority)
   - Position, current depth, target player profile

2. **Our Trade Assets** (ranked by expendability)
   - Player name, position, trade value assessment

3. **Top 3 Trade Targets**
   - Target manager (roster ID and name)
   - Their needs that align with our assets
   - Specific players to target from their roster
   - Psychological angle to exploit

4. **Recommended Trade Proposals** (3-5 proposals)
   Format each as:
   ```
   TRADE #X:
   We Send: [Players]
   We Receive: [Players]
   Target Manager: [Name/Roster ID]

   Pitch Angle: [How to frame this trade]
   Hidden Value: [Why this actually favors us]
   Expected Weekly Gain: [+/- points]
   ```

5. **Negotiation Script**
   - Initial offer (slightly more aggressive)
   - Fallback offer (if rejected)
   - Walk-away point (minimum acceptable)

## Decision Matrix

Only execute trades if:
- Net positive expected points per week (+2 or more)
- Fills critical roster need (0-1 bench depth positions)
- Exploits clear valuation discrepancy
- Improves playoff week matchups
- Takes advantage of manager desperation/naivety

## Final Recommendation

You are the general manager. Make the ultimate call:
- Which trade proposal to send first
- Backup options if rejected
- Players to avoid trading at all costs
- Timeline for execution (before waivers, after games, etc.)

Write the final trade analysis to:
`picks/week{n}/trades_week{n}.md`

Include:
- Detailed rationale for each proposal
- Expected manager responses
- Contingency plans
- Weekly point projections with/without trade