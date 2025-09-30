# Issue #92: Phase 3 - Extract Business Logic to lib/ Modules

**GitHub Issue**: [#92](https://github.com/GregBaugues/sleeper-mcp/issues/92)
**Parent Issue**: [#88](https://github.com/GregBaugues/sleeper-mcp/issues/88)
**Depends On**:
- #90 (Phase 1) - ✅ COMPLETED
- #91 (Phase 2) - ✅ COMPLETED

**Author**: GregBaugues
**Phase**: 3 of 4 in refactoring plan
**Risk Level**: HIGH - Major restructuring of business logic

## Objective

Extract business logic from 23 MCP tool definitions into focused modules (`league_tools.py`, `player_tools.py`, `waiver_tools.py`), making `sleeper_mcp.py` a thin layer of tool definitions.

## Current State Analysis

### File Sizes After Phase 2
- **sleeper_mcp.py**: 2,583 lines (down from 2,935 originally)
- **lib/validation.py**: 190 lines ✅
- **lib/decorators.py**: 137 lines ✅
- **lib/enrichment.py**: 401 lines ✅

### Target State
- **sleeper_mcp.py**: ~800 lines (tool definitions only)
- **lib/league_tools.py**: ~600 lines (9 league operations)
- **lib/player_tools.py**: ~500 lines (5 player operations)
- **lib/waiver_tools.py**: ~600 lines (4 waiver operations)

## Implementation Strategy

Based on the issue description, the recommended approach is to do this in **3 separate PRs**:

1. **PR 1**: Extract league_tools.py + update 9 league tools
2. **PR 2**: Extract player_tools.py + update 5 player tools
3. **PR 3**: Extract waiver_tools.py + update 4 waiver tools

This reduces risk and makes code review manageable.

## PR 1: League Tools Module

### Tools to Extract (9 tools)

1. `get_league_info` - Basic league information
2. `get_league_rosters` - All team rosters
3. `get_roster` - **Complex (296 lines)** - Single roster with enrichment
4. `get_league_users` - League participants
5. `get_league_matchups` - Weekly matchups
6. `get_league_transactions` - Transaction history
7. `get_league_traded_picks` - Traded draft picks
8. `get_league_drafts` - Draft information
9. `get_league_winners_bracket` - Playoff bracket

### Create lib/league_tools.py

**Functions to implement:**

```python
async def fetch_league_info(league_id: str, base_url: str) -> Dict[str, Any]:
    """Fetch and return league information."""

async def fetch_league_rosters(league_id: str, base_url: str) -> List[Dict[str, Any]]:
    """Fetch all team rosters in the league."""

async def fetch_roster_with_enrichment(
    roster_id: int,
    league_id: str,
    base_url: str
) -> Dict[str, Any]:
    """
    Fetch roster and enrich with full player data.
    This is the most complex function - 296 lines in current implementation.
    """

async def fetch_league_users(league_id: str, base_url: str) -> List[Dict[str, Any]]:
    """Fetch all users in the league."""

async def fetch_league_matchups(
    league_id: str,
    week: int,
    base_url: str
) -> List[Dict[str, Any]]:
    """Fetch matchups for a specific week."""

async def fetch_league_transactions(
    league_id: str,
    round_num: int,
    base_url: str
) -> List[Dict[str, Any]]:
    """Fetch transactions with player enrichment."""

async def fetch_league_traded_picks(
    league_id: str,
    base_url: str
) -> List[Dict[str, Any]]:
    """Fetch traded draft picks."""

async def fetch_league_drafts(league_id: str, base_url: str) -> List[Dict[str, Any]]:
    """Fetch draft information."""

async def fetch_league_winners_bracket(
    league_id: str,
    base_url: str
) -> List[Dict[str, Any]]:
    """Fetch playoff winners bracket."""
```

### Update sleeper_mcp.py

Transform each tool from containing business logic to being a thin wrapper:

**Before (get_roster example):**
```python
@mcp.tool()
@log_mcp_tool
async def get_roster(roster_id: int) -> Dict[str, Any]:
    # ... 296 lines of validation, fetching, enrichment
    ...
```

**After:**
```python
from lib.league_tools import fetch_roster_with_enrichment

@mcp.tool()
@log_mcp_tool
async def get_roster(roster_id: int) -> Dict[str, Any]:
    """Get detailed roster information with full player data for a specific team.

    Args:
        roster_id: The roster ID (1-10) for the team you want to view.
              Can be an integer or string (will be converted).
              Valid range: 1-10. Roster ID 2 is Bill Beliclaude.

    Returns roster including:
    - Team information (owner, record, points)
    - Full player details for all rostered players
    - Current week projections and scoring
    - Organized into starters, bench, taxi, and IR
    - Useful meta information (projected points for starters, bench points, etc.)

    Returns:
        Dict with roster info and enriched player data
    """
    try:
        roster_id = validate_roster_id(roster_id)
    except ValueError as e:
        logger.error(f"Roster ID validation failed: {e}")
        return create_error_response(
            str(e),
            value_received=str(roster_id)[:100],
            expected="integer between 1 and 10",
        )

    return await fetch_roster_with_enrichment(roster_id, LEAGUE_ID, BASE_URL)
```

### Tests to Create

**tests/test_league_tools.py** (~400-500 lines):

```python
import pytest
from unittest.mock import AsyncMock, patch, Mock
from lib import league_tools

class TestFetchLeagueInfo:
    @pytest.mark.asyncio
    async def test_fetch_league_info_success(self):
        # Mock httpx response
        # Call function
        # Assert results

    @pytest.mark.asyncio
    async def test_fetch_league_info_api_error(self):
        # Mock API error
        # Call function
        # Assert error handling

class TestFetchRosterWithEnrichment:
    @pytest.mark.asyncio
    async def test_fetch_roster_basic(self):
        # Test basic roster fetching

    @pytest.mark.asyncio
    async def test_fetch_roster_with_projections(self):
        # Test with player projections

    @pytest.mark.asyncio
    async def test_fetch_roster_organization(self):
        # Test starters/bench/taxi/IR organization

    # More tests for this complex function...

# Similar test classes for other functions...
```

## PR 2: Player Tools Module

### Tools to Extract (5 tools)

1. `search_players_by_name` - Search for players
2. `get_player_by_sleeper_id` - Get player by ID
3. `get_trending_players` - Trending adds/drops
4. `get_player_stats_all_weeks` - **Complex (197 lines)** - Season stats
5. `get_recent_transactions` - Recent league transactions

### Create lib/player_tools.py

**Functions to implement:**

```python
async def search_players_unified(
    name: str,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Search for players by name with unified Sleeper + Fantasy Nerds data."""

async def fetch_player_by_id(player_id: str) -> Dict[str, Any]:
    """Get unified player data by Sleeper ID."""

async def fetch_trending_players(
    type: str,
    base_url: str
) -> List[Dict[str, Any]]:
    """Get trending NFL players based on recent add/drop activity."""

async def fetch_player_stats_all_weeks(
    player_id: str,
    season: Optional[str],
    base_url: str
) -> Dict[str, Any]:
    """
    Get real stats for all weeks of a season for a specific player.
    This is complex - 197 lines in current implementation.
    """

async def fetch_recent_transactions(
    league_id: str,
    limit: int,
    transaction_type: Optional[str],
    include_failed: bool,
    drops_only: bool,
    min_days_ago: Optional[int],
    max_days_ago: Optional[int],
    include_player_details: bool,
    base_url: str
) -> List[Dict[str, Any]]:
    """Get the most recent transactions, sorted by most recent first."""
```

### Tests to Create

**tests/test_player_tools.py** (~400-500 lines)

## PR 3: Waiver Tools Module

### Tools to Extract (4 tools)

1. `get_waiver_wire_players` - **Complex (264 lines)** - Available players
2. `get_waiver_analysis` - **Complex (256 lines)** - Waiver recommendations
3. `get_trending_context` - **Complex (144 lines)** - Why players are trending
4. `evaluate_waiver_priority_cost` - Priority cost analysis

### Create lib/waiver_tools.py

**Functions to implement:**

```python
async def fetch_waiver_wire_players(
    league_id: str,
    base_url: str,
    position: Optional[str],
    search_term: Optional[str],
    limit: int,
    include_stats: bool,
    highlight_recent_drops: bool,
    verify_availability: bool
) -> Dict[str, Any]:
    """
    Get NFL players available on the waiver wire.
    This is complex - 264 lines in current implementation.
    """

async def fetch_waiver_analysis(
    league_id: str,
    base_url: str,
    position: Optional[str],
    days_back: int,
    limit: int
) -> Dict[str, Any]:
    """
    Get comprehensive waiver wire analysis with minimal context usage.
    This is complex - 256 lines in current implementation.
    """

async def fetch_trending_context(
    player_ids: List[str],
    max_players: int
) -> Dict[str, str]:
    """
    Get concise explanations for why players are trending.
    Uses web search - 144 lines in current implementation.
    """

def calculate_waiver_priority_cost(
    current_position: int,
    projected_points_gain: float,
    weeks_remaining: int
) -> Dict[str, Any]:
    """Calculate if using waiver priority is worth it."""
```

### Tests to Create

**tests/test_waiver_tools.py** (~500-600 lines)

## Detailed Implementation Steps

### Step 1: Set up branch and structure
```bash
git checkout -b issue-92-phase3-league-tools
```

### Step 2: Create lib/league_tools.py
- Extract business logic from each league tool
- Pass configuration (LEAGUE_ID, BASE_URL) as parameters
- Keep all enrichment logic intact using lib/enrichment utilities
- Maintain error handling patterns
- Add comprehensive docstrings
- Add type hints throughout

### Step 3: Update MCP tools
- Import from lib.league_tools
- Keep tool docstrings (they're used by MCP)
- Keep validation logic (or move to business logic)
- Make tool functions thin wrappers

### Step 4: Add tests
- Mock httpx.AsyncClient
- Mock cache operations
- Test success cases
- Test error cases
- Test edge cases

### Step 5: Verify and commit
```bash
# Run tests
LOGFIRE_IGNORE_NO_CONFIG=1 uv run pytest --tb=line

# Run linting
uv run ruff check .
uv run ruff format . --check

# Commit
git add lib/league_tools.py tests/test_league_tools.py sleeper_mcp.py lib/__init__.py
git commit -m "Extract league operations to lib/league_tools.py"
```

### Step 6: Create PR for league tools
```bash
gh pr create --title "Phase 3.1: Extract league operations to lib/league_tools.py" \
  --body "Part 1 of Phase 3 refactoring. Extracts 9 league operation tools..."
```

### Step 7-9: Repeat for player_tools.py (new branch/PR)
### Step 10-12: Repeat for waiver_tools.py (new branch/PR)

## Key Design Principles

### 1. Configuration as Parameters
Business logic functions should not access global variables. Pass configuration explicitly:
```python
# Good
async def fetch_league_info(league_id: str, base_url: str) -> Dict:
    ...

# Bad
async def fetch_league_info() -> Dict:
    league_id = LEAGUE_ID  # Global access
    ...
```

### 2. Dependency Injection
Functions should accept dependencies rather than creating them:
```python
# Good
async def fetch_roster(roster_id: int, league_id: str, base_url: str, client: httpx.AsyncClient):
    ...

# Acceptable (creates client internally)
async def fetch_roster(roster_id: int, league_id: str, base_url: str):
    async with httpx.AsyncClient(timeout=30.0) as client:
        ...
```

### 3. Pure Business Logic
Business logic should focus on the "what", not the "how" of MCP integration:
- No MCP-specific code
- No @mcp.tool() decorators
- No @log_mcp_tool decorators
- Return plain data structures
- Let MCP tools handle serialization

### 4. Comprehensive Error Handling
Maintain defensive error handling:
- Catch and handle httpx errors
- Catch and handle cache errors
- Return meaningful error responses
- Log errors appropriately

### 5. Type Hints
All functions should have complete type hints:
```python
async def fetch_roster_with_enrichment(
    roster_id: int,
    league_id: str,
    base_url: str
) -> Dict[str, Any]:
    ...
```

## Expected Impact

### Lines of Code Changes (Total across 3 PRs)

**PR 1 (League Tools):**
- sleeper_mcp.py: -600 lines
- lib/league_tools.py: +600 lines
- tests/test_league_tools.py: +500 lines

**PR 2 (Player Tools):**
- sleeper_mcp.py: -500 lines
- lib/player_tools.py: +500 lines
- tests/test_player_tools.py: +400 lines

**PR 3 (Waiver Tools):**
- sleeper_mcp.py: -800 lines
- lib/waiver_tools.py: +800 lines
- tests/test_waiver_tools.py: +600 lines

**Total Impact:**
- sleeper_mcp.py: ~800 lines (down from 2,583)
- New lib/ modules: +1,900 lines (reusable, testable)
- New tests: +1,500 lines (comprehensive coverage)

## Success Criteria

### For Each PR
- ✓ All existing integration tests pass
- ✓ New unit tests provide >80% coverage
- ✓ Linting and formatting pass
- ✓ No breaking changes to tool behavior
- ✓ Tool signatures remain identical
- ✓ Error responses remain consistent

### For Phase 3 Overall
- ✓ `sleeper_mcp.py` reduced to ~800 lines (tool definitions only)
- ✓ Business logic separated by concern (league/player/waiver)
- ✓ All 23 tools work identically to before
- ✓ All tests pass
- ✓ No breaking changes
- ✓ Code is more maintainable and testable
- ✓ Type hints throughout

## Risk Mitigation

**HIGH RISK**: This is major restructuring

**Mitigation strategies:**
1. **Three separate PRs** - Easier to review and roll back if needed
2. **Comprehensive testing** - Unit tests for all new functions
3. **Integration tests** - All existing tests must pass
4. **Small commits** - One logical change per commit
5. **Manual testing** - Test each tool after refactoring
6. **Gradual rollout** - PR 1 merged before starting PR 2

## Testing Strategy

### Unit Tests (New)
- Test business logic functions in isolation
- Mock external dependencies (httpx, cache)
- Test success and failure cases
- Test edge cases and boundary conditions
- Focus on business logic correctness

### Integration Tests (Existing)
- All existing VCR-based tests must pass
- Verify tool behavior is unchanged
- Check error responses match expectations
- Ensure enrichment still works correctly

### Manual Testing
After each PR:
- Test affected tools manually
- Verify no regressions
- Check error handling
- Validate enrichment logic

## Notes

- Keep all docstrings in the MCP tool definitions (they're part of the tool interface)
- Business logic functions can have shorter docstrings focused on implementation
- Use lib/enrichment utilities extensively in the new modules
- Maintain backward compatibility with cache data structures
- Keep defensive error handling throughout
- Log errors at the business logic level, not just in MCP tools

## Related Issues

- #88 - Parent issue: Cleanup codebase and plan for refactor
- #90 - Phase 1: Extract validation and decorator utilities (✅ COMPLETED)
- #91 - Phase 2: Extract player enrichment utilities (✅ COMPLETED)
- #93 - Phase 4: Final cleanup and optimization (Future)

## References

- FastMCP docs: https://gofastmcp.com/llms.txt
- Original refactoring plan: `scratchpads/issue-88-cleanup-and-refactor-plan.md`
- Phase 1 plan: `scratchpads/issue-90-phase1-extract-validation-decorator.md`
- Phase 2 plan: `scratchpads/issue-91-phase2-extract-enrichment.md`
- Current main file: `sleeper_mcp.py` (2,583 lines)