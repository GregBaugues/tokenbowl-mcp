# Issue #113: Refactor Prompts

**Issue Link**: https://github.com/GregBaugues/tokenbowl-mcp/issues/113

## Problem Statement

The prompts in `.claude/commands/` and `.claude/agents/` have become bloated and are suffering from context pollution, which is negatively impacting performance. These prompts are critical to the team's weekly fantasy football performance and need to be refactored for:

1. **Reduced bloat** - Remove unnecessary instructions and redundancy
2. **Better modularity** - Use subagents to isolate context and reduce pollution
3. **Improved maintainability** - Clear separation of concerns
4. **Performance optimization** - Leverage latest MCP tools more efficiently

## Current State Analysis

### Slash Commands (`.claude/commands/`)

1. **waivers.md** (265 lines)
   - **Issues**: Extremely bloated with repetitive instructions, multiple frameworks stacked on each other
   - **Key functions**: Waiver wire analysis with ROS focus, streaming defense/kicker
   - **Redundancy**: Multiple mentions of same tools, repeated priority frameworks
   - **Tools used**: `get_waiver_analysis()`, `get_trending_players()`, `get_recent_transactions()`, `search_players_by_name()`, `WebSearch`, `evaluate_waiver_priority_cost()`

2. **wrapup.md** (182 lines)
   - **Issues**: Very detailed but could delegate matchup writing to subagents more effectively
   - **Key functions**: Weekly slopup (recap) generation in Bill Simmons + Bill Burr style
   - **Current approach**: Uses fantasy-matchup-journalist subagent for each matchup (good!)
   - **Redundancy**: Style guidelines repeated between this and the journalist agent

3. **startsit.md** (127 lines)
   - **Issues**: Phase structure is clear but could be more concise, bye week handling repeated many times
   - **Key functions**: Start/sit recommendations for weekly lineup decisions
   - **Current approach**: Uses fantasy-player-analyst subagent (good!)
   - **Redundancy**: Multiple "CRITICAL" sections about bye weeks, defense streaming repeated

4. **trade.md** (166 lines)
   - **Issues**: Very aggressive tone, some instructions could be consolidated
   - **Key functions**: Trade analysis and proposal generation
   - **Opportunity**: Could create a subagent for opponent roster weakness analysis

5. **horoscope.md** (21 lines)
   - **Status**: Simple and clean, minimal refactoring needed
   - **Opportunity**: Could be enhanced with subagent for deeper player analysis

6. **issue.md** (36 lines)
   - **Status**: Good structure, delegates to subagent appropriately
   - **Minor optimization**: Could be slightly more concise

### Subagents (`.claude/agents/`)

1. **fantasy-matchup-journalist.md** (180 lines)
   - **Issues**: Comprehensive but has style guideline duplication with wrapup.md
   - **Opportunity**: Extract shared style guidelines to a separate reference document

2. **fantasy-player-analyst.md** (41 lines)
   - **Status**: Well-scoped, clean, minimal refactoring needed
   - **Opportunity**: Could reference a shared fantasy analysis framework

3. **github-issue-planner.md** (not reviewed yet, but exists)
   - **Status**: To be reviewed

## Refactoring Strategy

### Principle 1: Extract Shared Knowledge to Reference Documents

Create shared reference documents that multiple prompts/agents can reference instead of duplicating content:

- `_style_guide.md` - Shared Bill Simmons + Bill Burr voice guidelines
- `_fantasy_analysis_framework.md` - Shared evaluation criteria (targets, snap %, red zone, etc.)
- `_mcp_tools_quick_reference.md` - Quick reference for most-used tokenbowl tools

### Principle 2: Create Focused Subagents

New subagents to create:

1. **roster-analyst** - Analyzes roster depth, identifies needs and trade assets
   - Tools: `get_roster()`, `get_league_rosters()`, `search_players_by_name()`
   - Used by: waivers, trade, startsit commands

2. **opponent-scout** - Analyzes opponent rosters for weaknesses and strengths
   - Tools: `get_roster()`, `get_league_rosters()`, `get_league_users()`
   - Used by: trade command

3. **player-researcher** - Deep dive research on specific players using web search
   - Tools: `WebSearch`, `WebFetch`, `get_player_stats_all_weeks()`, `search_players_by_name()`
   - Used by: waivers, startsit commands

4. **defense-streaming-analyst** - Specialized defense streaming recommendations
   - Tools: `get_waiver_wire_players(position='DEF')`, `get_nfl_schedule()`
   - Used by: waivers, startsit commands

### Principle 3: Simplify Command Prompts

Each command should be a thin orchestrator that:
1. States the goal clearly (1-2 sentences)
2. Lists the phases/steps (bullet points)
3. Delegates to subagents for complex analysis
4. Specifies output format and location

Remove:
- Repeated tool usage examples
- Style guidelines (reference shared docs instead)
- Redundant "CRITICAL" warnings
- Multiple competing frameworks

### Principle 4: Optimize Tool Usage

Based on review of MCP tools (28 tools available):
- Prioritize consolidated tools like `get_waiver_analysis()` over multiple separate calls
- Use minimal format flags (`include_stats=False`) to reduce context
- Leverage subagents for data gathering to keep main context clean

## Detailed Refactoring Plan

### Phase 1: Create Foundation Documents

1. Create `.claude/reference/_style_guide.md`
   - Extract shared voice guidelines from wrapup.md and fantasy-matchup-journalist.md
   - ~40 lines: Simmons + Burr characteristics, DO/DON'T lists

2. Create `.claude/reference/_fantasy_framework.md`
   - Extract shared evaluation criteria (volume, targets, matchups, etc.)
   - ~30 lines: Core principles for player evaluation

3. Create `.claude/reference/_mcp_tools_cheatsheet.md`
   - Quick reference for 10 most-used tools with examples
   - ~50 lines: Tool name, purpose, key parameters

### Phase 2: Create New Subagents

4. Create `.claude/agents/roster-analyst.md`
   - Purpose: Analyze roster depth and identify positions of need
   - Tools: get_roster, get_league_rosters, search_players_by_name
   - ~60 lines

5. Create `.claude/agents/opponent-scout.md`
   - Purpose: Profile opponent rosters for trade opportunities
   - Tools: get_roster, get_league_rosters, get_league_users
   - ~50 lines

6. Create `.claude/agents/player-researcher.md`
   - Purpose: Deep web research on specific players
   - Tools: WebSearch, WebFetch, get_player_stats_all_weeks, search_players_by_name
   - ~70 lines

7. Create `.claude/agents/defense-streaming-analyst.md`
   - Purpose: Weekly defense streaming recommendations
   - Tools: get_waiver_wire_players, get_nfl_schedule
   - ~50 lines

### Phase 3: Refactor Command Prompts

8. Refactor `waivers.md`
   - Target: Reduce from 265 lines to ~100 lines
   - Changes:
     - Remove redundant frameworks and repeated tool examples
     - Consolidate "CRITICAL" bye week warnings into one clear section
     - Reference _fantasy_framework.md for evaluation criteria
     - Delegate roster needs analysis to roster-analyst subagent
     - Delegate player research to player-researcher subagent
     - Delegate defense streaming to defense-streaming-analyst subagent
     - Keep only the orchestration logic and final decision framework

9. Refactor `wrapup.md`
   - Target: Reduce from 182 lines to ~80 lines
   - Changes:
     - Remove duplicated style guidelines, reference _style_guide.md
     - Simplify data gathering steps (already delegates to journalist)
     - Keep orchestration and structure, remove repeated instructions

10. Refactor `startsit.md`
    - Target: Reduce from 127 lines to ~60 lines
    - Changes:
      - Consolidate bye week handling into single section
      - Delegate defense analysis to defense-streaming-analyst subagent
      - Reference _fantasy_framework.md for evaluation criteria
      - Keep phase structure but make more concise

11. Refactor `trade.md`
    - Target: Reduce from 166 lines to ~90 lines
    - Changes:
      - Delegate roster analysis to roster-analyst subagent
      - Delegate opponent analysis to opponent-scout subagent
      - Consolidate psychology/tactics sections
      - Keep proposal construction and decision matrix

12. Refactor `fantasy-matchup-journalist.md`
    - Target: Reduce from 180 lines to ~100 lines
    - Changes:
      - Remove duplicated style guidelines, reference _style_guide.md
      - Simplify data gathering steps
      - Keep unique voice characteristics and matchup structure

### Phase 4: Test & Validate

13. Create test scenarios for each refactored command
    - Test waivers command with mock week
    - Test startsit command with mock roster
    - Test trade command with mock league state
    - Test wrapup command with completed week

14. Validate subagent invocations work correctly
    - Ensure PROACTIVE language triggers agents appropriately
    - Verify tool scoping is correct

### Phase 5: Documentation

15. Update main CLAUDE.md with:
    - Reference to new structure
    - How to use reference documents
    - When each subagent is invoked

## Expected Outcomes

1. **~50% reduction in command prompt length** (average 265 → ~130 lines)
2. **Better context isolation** - Subagents handle data-heavy tasks
3. **DRY principle** - Shared reference docs eliminate duplication
4. **Improved maintainability** - Changes to style/framework propagate everywhere
5. **Clearer responsibilities** - Each agent has a single, well-defined purpose

## Testing Strategy

For each refactored command:
1. Run command with test data
2. Verify subagents are invoked correctly
3. Check output quality matches or exceeds original
4. Measure context usage (should be lower)
5. Validate no functionality is lost

## Risks & Mitigations

**Risk**: Over-modularization makes commands harder to understand
**Mitigation**: Keep command prompts as clear orchestrators, maintain README

**Risk**: Subagent invocation overhead
**Mitigation**: Only delegate truly complex tasks, keep simple tasks inline

**Risk**: Breaking existing workflows
**Mitigation**: Thorough testing before deployment, maintain backups

## Success Metrics

- [ ] All command prompts reduced by 30%+ lines
- [ ] Zero duplication of style guidelines across files
- [ ] At least 4 new focused subagents created
- [ ] Reference documents created and linked
- [ ] All tests pass with refactored prompts
- [ ] User reports improved performance and clarity
