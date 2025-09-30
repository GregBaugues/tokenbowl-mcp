# Issue #94: Add Tests for Untested Complex Tools

**Issue**: https://github.com/GregBaugues/sleeper-mcp/issues/94

## Overview

Add integration tests for 13 MCP tools that currently lack dedicated test coverage, prioritized by complexity and usage. This will increase confidence in future deployments and refactoring.

## Current Test Coverage Analysis

**Total Tests**: 176 tests across multiple files
- `test_sleeper_mcp.py`: 16 integration tests
- `test_parameter_validation.py`: 16 validation tests
- `test_valid_parameters.py`: 9 validation tests
- Other test files: enrichment, decorators, validation logic

**Existing Integration Tests** (in test_sleeper_mcp.py):
- ✅ `test_get_league_info`
- ✅ `test_get_league_rosters`
- ✅ `test_get_league_users`
- ✅ `test_get_league_matchups`
- ✅ `test_get_league_transactions`
- ✅ `test_get_recent_transactions`
- ✅ `test_get_roster` (added in #89)
- ✅ `test_get_user`
- ✅ `test_get_trending_players`
- ✅ `test_search_player_by_name_mock` (mocked, not VCR)
- ✅ `test_get_player_by_sleeper_id_mock` (mocked, not VCR)

**Tools Needing Integration Tests** (from issue #94):

### High Priority (Complex & Frequently Used)
1. `get_player_stats_all_weeks` - 197 lines, aggregation logic
2. `get_waiver_wire_players` - 264 lines, filtering and enrichment
3. `get_waiver_analysis` - 256 lines, analysis logic
4. `get_trending_context` - 144 lines, web search integration
5. `search_players_by_name` - Cache-based search (has mock test, needs VCR test)
6. `get_player_by_sleeper_id` - Cache-based lookup (has mock test, needs VCR test)

### Medium Priority (Less Complex or Less Used)
7. `evaluate_waiver_priority_cost` - Calculation logic
8. `get_nfl_schedule` - External API integration
9. `fetch` - ChatGPT compatibility tool
10. `search` - ChatGPT compatibility tool

### Lower Priority (Simple, Rarely Used)
11. `get_league_drafts` - Simple API wrapper
12. `get_league_traded_picks` - Simple API wrapper
13. `get_league_winners_bracket` - Simple API wrapper

## Implementation Plan

### Phase 1: High-Priority Tools (THIS PR)

Focus on the most complex and frequently used tools that have business logic requiring testing.

#### 1. `test_get_player_stats_all_weeks`
- Test with known player (Patrick Mahomes, ID: 4046)
- Verify weekly stats structure
- Verify season totals aggregation
- Test with current season (2024)
- Use VCR cassette

#### 2. `test_get_waiver_wire_players` (3 test cases)
- `test_get_waiver_wire_players_basic` - Test with limit parameter
- `test_get_waiver_wire_players_with_position` - Test position filter (RB, WR, etc.)
- `test_get_waiver_wire_players_with_search` - Test search term filtering
- Verify available players are not on rosters
- Test enrichment data (trending, projections)

#### 3. `test_get_waiver_analysis`
- Test analysis output structure
- Verify recently_dropped, trending_available fields
- Test with position filter
- Verify minimal format for efficiency

#### 4. `test_get_trending_context`
- Test with multiple player IDs
- Verify 2-3 sentence explanations
- **Note**: May require mocking web search, not VCR
- Test max_players parameter

#### 5. Convert existing mock tests to VCR tests
- `test_search_players_by_name` - Add VCR-based integration test
- `test_get_player_by_sleeper_id` - Add VCR-based integration test

### Phase 2: Medium-Priority Tools (Future PR)

#### 6. `test_evaluate_waiver_priority_cost`
- Test calculation logic with various inputs
- Test recommended_action output
- Test expected_value and break_even_threshold

#### 7. `test_get_nfl_schedule`
- Test with current week (None parameter)
- Test with specific week number
- Verify game structure, scores, teams

#### 8. `test_fetch` - ChatGPT compatibility
- Test with player resource (player_4046)
- Test with roster resource (roster_2)
- Verify proper data structure

#### 9. `test_search` - ChatGPT compatibility
- Test with player name query
- Test with general query
- Verify results array structure

### Phase 3: Lower-Priority Tools (Future PR)

#### 10. `test_get_league_drafts`
- Test basic API wrapper
- Verify draft structure

#### 11. `test_get_league_traded_picks`
- Test traded picks structure
- Verify roster IDs

#### 12. `test_get_league_winners_bracket`
- Test playoff bracket structure
- Verify matchup data

## Testing Strategy

1. **Use VCR cassettes** for integration tests that call external APIs
   - Record real API responses once
   - Replay during tests for speed and reliability
   - Commit cassettes to git

2. **Mock external dependencies** where VCR doesn't work
   - Web searches (`get_trending_context`)
   - Non-deterministic data

3. **Test structure**:
   - Happy path first (valid inputs, expected outputs)
   - Edge cases (empty results, boundary conditions)
   - Error handling (already covered by validation tests)

4. **Keep tests simple and readable**
   - Clear test names
   - Minimal setup
   - Clear assertions

## Success Criteria

- ✅ All high-priority tools have integration tests
- ✅ Tests use VCR cassettes where appropriate
- ✅ Tests are repeatable and reliable
- ✅ CI runs tests successfully
- ✅ Test coverage increases from ~16 to ~25+ integration tests

## Estimated Impact

**New Tests in Phase 1**: ~8-10 test functions
**Files Modified**: `tests/test_sleeper_mcp.py`
**VCR Cassettes**: ~8-10 new cassettes in `tests/cassettes/`
**Risk Level**: Low (only adding tests, no code changes)

## Notes

- Validation tests already exist for all these tools (in `test_parameter_validation.py`)
- Focus is on integration tests that exercise real API calls and business logic
- Some tools like `search_players_by_name` already have mock tests - we'll add VCR tests alongside
- `get_trending_context` may need special handling due to web search dependency