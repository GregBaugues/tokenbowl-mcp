# Issue #88: Cleanup Codebase and Plan for Refactor

**GitHub Issue**: [#88](https://github.com/GregBaugues/tokenbowl-mcp/issues/88)
**Author**: GregBaugues
**Task**: Identify refactoring opportunities and assess test coverage

## Executive Summary

After thorough analysis, the codebase is in good shape following the cleanup in PR #84 (issue #75). The main file `sleeper_mcp.py` has grown to 2,935 lines with 23 MCP tools, which presents opportunities for modular refactoring. Test coverage is solid with 64+ tests, but 13 tools lack dedicated test coverage.

## Current State Analysis

### Codebase Structure

```
sleeper-mcp/
├── sleeper_mcp.py          # 2,935 lines - Main MCP server with 23 tools
├── cache_client.py         #   484 lines - Cache interface
├── build_cache.py          #   844 lines - Cache building functions
├── scripts/                # 3 utility scripts (446 lines total)
│   ├── manual_cache_refresh.py
│   ├── parse_trade_proposal.py
│   └── extract_trade_proposal.py
├── data/                   # Week-specific data files
├── picks/                  # Weekly picks (week1-week16)
├── slopups/                # Weekly summaries
├── scratchpads/            # Development notes
└── tests/                  # 7 test files, 1,654 lines, 64 tests
```

### File Size Analysis

| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| sleeper_mcp.py | 2,935 | Main server with 23 MCP tools | **Needs modularization** |
| build_cache.py | 844 | Cache building logic | Good |
| cache_client.py | 484 | Cache interface | Good |
| Tests | 1,654 | 64 tests across 7 files | **Gaps identified** |

### MCP Tools Breakdown (sleeper_mcp.py)

The main file contains 23 MCP tools, organized into these logical groups:

1. **League Operations** (8 tools)
   - get_league_info
   - get_league_rosters
   - get_roster (complex, 296 lines)
   - get_league_users
   - get_league_matchups
   - get_league_transactions
   - get_league_traded_picks
   - get_league_drafts
   - get_league_winners_bracket

2. **Player Data** (5 tools)
   - search_players_by_name
   - get_player_by_sleeper_id
   - get_trending_players
   - get_player_stats_all_weeks (complex, 197 lines)
   - get_recent_transactions

3. **Waiver Wire Analysis** (4 tools)
   - get_waiver_wire_players (complex, 264 lines)
   - get_waiver_analysis (complex, 256 lines)
   - get_trending_context (complex, 144 lines)
   - evaluate_waiver_priority_cost

4. **NFL Data** (1 tool)
   - get_nfl_schedule

5. **ChatGPT Compatibility** (2 tools)
   - search (complex, 148 lines)
   - fetch (complex, 160 lines)

6. **Infrastructure** (3 functions)
   - log_mcp_tool decorator (107 lines)
   - Server setup and startup logic

### Complexity Hotspots

Functions over 100 lines that merit attention:

1. **get_roster** (296 lines, lines 212-507)
   - Fetches roster data
   - Enriches with player details from cache
   - Calculates projections and stats
   - Organizes into starters/bench/taxi/IR
   - **Refactor candidate**: Extract player enrichment logic

2. **get_waiver_wire_players** (264 lines, lines 1510-1773)
   - Validates parameters
   - Fetches rostered players
   - Filters available players
   - Enriches with stats and trending data
   - Highlights recent drops
   - **Refactor candidate**: Extract filtering and enrichment logic

3. **get_waiver_analysis** (256 lines, lines 2035-2290)
   - Analyzes recently dropped players
   - Fetches trending players
   - Filters for availability
   - Provides position-based recommendations
   - **Refactor candidate**: Extract analysis logic

4. **get_player_stats_all_weeks** (197 lines, lines 1311-1507)
   - Fetches stats for all weeks
   - Aggregates season totals
   - Enriches with player data
   - **Refactor candidate**: Extract aggregation logic

5. **search** (148 lines, lines 2515-2662)
   - ChatGPT compatibility wrapper
   - Searches players, waiver wire, teams
   - **Keep as-is**: Integration layer should stay together

6. **fetch** (160 lines, lines 2663-2822)
   - ChatGPT compatibility wrapper
   - Fetches player, roster, user, matchup details
   - **Keep as-is**: Integration layer should stay together

7. **log_mcp_tool** decorator (107 lines, lines 58-164)
   - Defensive error handling
   - Logfire span management
   - Parameter serialization
   - **Keep as-is**: Critical infrastructure

## Refactoring Opportunities

### Major Refactor: Modularize sleeper_mcp.py

**Goal**: Break the 2,935-line main file into focused modules while maintaining FastMCP's single-file pattern for tool registration.

**Approach**: Extract business logic into separate modules, keep tool definitions in main file.

```
sleeper-mcp/
├── sleeper_mcp.py          # Tool definitions only (~800 lines)
├── lib/
│   ├── __init__.py
│   ├── league_tools.py     # League operations logic
│   ├── player_tools.py     # Player data logic
│   ├── waiver_tools.py     # Waiver wire logic
│   ├── enrichment.py       # Player enrichment utilities
│   ├── validation.py       # Parameter validation
│   └── decorators.py       # log_mcp_tool decorator
├── cache_client.py
├── build_cache.py
└── tests/
    ├── test_sleeper_mcp.py
    ├── test_league_tools.py
    ├── test_player_tools.py
    └── test_waiver_tools.py
```

**Benefits**:
- Easier to navigate and maintain
- Better separation of concerns
- Easier to test business logic in isolation
- Tool definitions remain clear and discoverable
- No impact on MCP tool registration

**Implementation Plan**:

1. **Phase 1**: Extract utilities (low risk)
   - Create `lib/validation.py` for parameter validation
   - Create `lib/decorators.py` for log_mcp_tool
   - Update imports in sleeper_mcp.py
   - Run tests to verify no breakage

2. **Phase 2**: Extract enrichment logic (medium risk)
   - Create `lib/enrichment.py` for player data enrichment
   - Extract common patterns from get_roster, get_waiver_wire_players
   - Examples:
     - `enrich_player_data(player_ids, include_stats=False)`
     - `enrich_with_trending_data(players)`
     - `calculate_projections(player, week)`

3. **Phase 3**: Extract business logic (higher risk)
   - Create `lib/league_tools.py` with logic for league operations
   - Create `lib/player_tools.py` with logic for player operations
   - Create `lib/waiver_tools.py` with logic for waiver operations
   - Keep MCP tool definitions in sleeper_mcp.py as thin wrappers
   - Each tool becomes: validate params → call business logic → return result

4. **Phase 4**: Cleanup and optimization
   - Remove any dead code
   - Standardize error handling
   - Add type hints throughout
   - Update documentation

**Example Refactor**:

Before (sleeper_mcp.py):
```python
@mcp.tool()
@log_mcp_tool
async def get_roster(roster_id: int) -> Dict[str, Any]:
    # 296 lines of validation, fetching, enrichment, organization
    ...
```

After (sleeper_mcp.py):
```python
from lib.league_tools import get_roster_with_enrichment

@mcp.tool()
@log_mcp_tool
async def get_roster(roster_id: int) -> Dict[str, Any]:
    """Get detailed roster information with full player data for a specific team.
    [docstring...]
    """
    return await get_roster_with_enrichment(roster_id, LEAGUE_ID, BASE_URL)
```

lib/league_tools.py:
```python
async def get_roster_with_enrichment(
    roster_id: int,
    league_id: str,
    base_url: str
) -> Dict[str, Any]:
    # Validation
    # Fetching
    # Enrichment
    # Organization
    ...
```

### Minor Refactors (Can do immediately)

1. **Standardize error responses**
   - All tools use similar error dict format
   - Extract to utility function: `create_error_response(message, **context)`

2. **Extract common validation patterns**
   - Many tools validate week, roster_id, position, etc.
   - Create reusable validators in `lib/validation.py`

3. **Consolidate player enrichment**
   - Multiple tools enrich player data with cache info
   - Extract to shared utility functions

4. **Add type hints consistently**
   - Some functions have full type hints, others don't
   - Add throughout for better IDE support and documentation

## Test Coverage Analysis

### Current Test Stats
- **Total tests**: 64+
- **Test files**: 7
- **Test lines**: 1,654
- **Testing approach**: Mix of VCR cassettes (recorded API responses) and mocked tests

### Test Files Overview

1. **test_sleeper_mcp.py** - Main integration tests with VCR
2. **test_sleeper_mcp_mocked.py** - Mocked unit tests
3. **test_parameter_validation.py** - Parameter validation tests
4. **test_simple_valid_params.py** - Simple validation tests
5. **test_valid_parameters.py** - More validation tests
6. **test_integration.py** - Basic import and setup tests
7. **conftest.py** - Pytest configuration and fixtures

### Tools WITHOUT Dedicated Tests (13 tools)

**High Priority** (Complex tools used frequently):
1. ✗ `get_roster` - 296 lines, complex enrichment logic
2. ✗ `get_player_stats_all_weeks` - 197 lines, aggregation logic
3. ✗ `get_waiver_wire_players` - 264 lines, filtering and enrichment
4. ✗ `get_waiver_analysis` - 256 lines, analysis logic
5. ✗ `get_trending_context` - 144 lines, web search integration
6. ✗ `search_players_by_name` - Cache-based search
7. ✗ `get_player_by_sleeper_id` - Cache-based lookup

**Medium Priority** (Less complex or less used):
8. ✗ `evaluate_waiver_priority_cost` - Calculation logic
9. ✗ `get_nfl_schedule` - External API integration
10. ✗ `fetch` - ChatGPT compatibility tool
11. ✗ `search` - ChatGPT compatibility tool (has indirect tests via validation)

**Lower Priority** (Simple, rarely used):
12. ✗ `get_league_drafts` - Simple API wrapper
13. ✗ `get_league_traded_picks` - Simple API wrapper
14. ✗ `get_league_winners_bracket` - Simple API wrapper

### Testing Recommendations

#### 1. Add Integration Tests for Complex Tools (Priority 1)

**get_roster**:
```python
@pytest.mark.vcr()
async def test_get_roster():
    result = await sleeper_mcp.get_roster.fn(roster_id=2)
    assert "owner" in result
    assert "roster_id" in result
    assert "starters" in result
    assert "bench" in result
    assert len(result["starters"]) > 0
```

**get_waiver_wire_players**:
```python
@pytest.mark.vcr()
async def test_get_waiver_wire_players_basic():
    result = await sleeper_mcp.get_waiver_wire_players.fn(limit=10)
    assert "players" in result
    assert "total_available" in result
    assert len(result["players"]) <= 10

@pytest.mark.vcr()
async def test_get_waiver_wire_players_with_position():
    result = await sleeper_mcp.get_waiver_wire_players.fn(position="QB", limit=5)
    assert "players" in result
    for player in result["players"]:
        assert player["position"] == "QB"
```

**get_player_stats_all_weeks**:
```python
@pytest.mark.vcr()
async def test_get_player_stats_all_weeks():
    # Use known player ID
    result = await sleeper_mcp.get_player_stats_all_weeks.fn(
        player_id="4046",  # Patrick Mahomes
        season="2024"
    )
    assert "player" in result
    assert "weekly_stats" in result
    assert "season_totals" in result
```

#### 2. Add Unit Tests for Business Logic (Priority 2)

After refactoring, add unit tests for extracted business logic:

```python
# Test enrichment functions
def test_enrich_player_data():
    player_ids = ["4046", "7528"]
    result = enrich_player_data(player_ids, include_stats=True)
    assert len(result) == 2
    assert result[0]["player_id"] == "4046"

# Test validation functions
def test_validate_roster_id():
    assert validate_roster_id(5) == 5
    with pytest.raises(ValueError):
        validate_roster_id(0)
    with pytest.raises(ValueError):
        validate_roster_id(11)
```

#### 3. Add Cache Tests (Priority 2)

Test cache integration more thoroughly:

```python
def test_cache_player_search():
    results = search_players_unified("mahomes")
    assert len(results) > 0
    assert results[0]["last_name"].lower() == "mahomes"

def test_cache_player_lookup():
    player = get_player_by_id("4046")
    assert player is not None
    assert player["first_name"] == "Patrick"
```

#### 4. Test Coverage Goals

**Minimum acceptable coverage**:
- All complex tools (>100 lines) have integration tests
- All validation logic has unit tests
- Critical paths (waiver wire, roster lookups) well-tested
- Error handling tested for common failure modes

**Nice to have**:
- Business logic functions have >80% coverage
- Edge cases tested (empty results, invalid data)
- Performance tests for cache operations

#### 5. Testing Strategy After Refactor

Once business logic is extracted:
1. **Unit tests** for extracted modules (lib/*.py)
2. **Integration tests** for MCP tools (sleeper_mcp.py)
3. **Mock external dependencies** (httpx, cache) in unit tests
4. **Use VCR cassettes** for integration tests

## Light Cleanup Tasks

These can be done immediately without major refactoring:

### 1. Add Missing Type Hints
- Review all functions and add complete type hints
- Use `from typing import Optional, List, Dict, Any` consistently

### 2. Standardize Docstrings
- Ensure all tools have consistent docstring format:
  - Description
  - Args section with types
  - Returns section with type
  - Examples where helpful

### 3. Remove Commented Code
- Lines 2490-2504 in sleeper_mcp.py have commented-out draft picks tool
- Either delete or uncomment and test

### 4. Update Dependencies
- Check for dependency updates in pyproject.toml
- Test with latest versions

### 5. Add pytest-cov Plugin
- Add `pytest-cov>=5.0.0` to test dependencies
- Enable coverage reporting in CI/CD

### 6. Improve Error Messages
- Audit all error responses for clarity
- Ensure they include:
  - What went wrong
  - What was expected
  - What was received

### 7. Add Logging Consistency
- Review log levels (DEBUG, INFO, WARNING, ERROR)
- Ensure consistent format and context

## Implementation Recommendations

### Do Now (This PR)
1. Add missing tests for high-priority tools
2. Add pytest-cov for coverage reporting
3. Remove commented code
4. Standardize error responses
5. Add missing type hints
6. Document refactoring plan in this scratchpad

### Do Soon (Next PR)
1. Extract validation utilities
2. Extract log_mcp_tool decorator
3. Add more unit tests
4. Add type hints throughout

### Do Later (Major Refactor)
1. Extract business logic into lib/ modules
2. Refactor complex tools to use extracted logic
3. Add comprehensive test suite for new modules
4. Update documentation

## Success Criteria

### For This Issue
- ✓ Refactoring plan documented
- ✓ Test gaps identified
- ✓ Light cleanup completed
- ✓ New tests added for critical tools
- ✓ Coverage reporting enabled

### For Future Refactor
- sleeper_mcp.py reduced to <1000 lines
- Business logic extracted to lib/ modules
- Test coverage >80% for business logic
- All complex tools have integration tests
- Documentation updated
- CI/CD passes with new structure

## Notes

- FastMCP requires tools to be registered in a single file, so we keep tool definitions in sleeper_mcp.py
- Business logic can be extracted without breaking MCP tool registration
- Current VCR cassette approach is good for integration tests
- Consider adding performance benchmarks for cache operations
- Logfire integration is working well for observability

## Related Issues
- #75 - Spring cleaning (completed in PR #84)
- #72 - MCP parameter validation
- #66 - Waiver wire improvements
- #53 - Player stats all weeks

## References
- FastMCP docs: https://gofastmcp.com/llms.txt
- Render deployment: srv-d2o5vv95pdvs739hqde0
- Redis cache: red-d2o755emcj7s73b8bj9g