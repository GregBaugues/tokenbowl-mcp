# Issue #99: Fix test_get_trending_players mocked test player_id expectation

**Issue Link**: https://github.com/GregBaugues/sleeper-mcp/issues/99

## Problem Analysis

The mocked test `test_get_trending_players` in `tests/test_sleeper_mcp_mocked.py:301` is failing because it expects a `player_id` field in the result, but receives `full_name` instead.

### Error
```
FAILED tests/test_sleeper_mcp_mocked.py::TestPlayerToolsMocked::test_get_trending_players - AssertionError: assert 'player_id' in {'full_name': 'Patrick Mahomes', 'position': 'QB', 'count': 150}
```

## Root Cause

After analyzing the code in `sleeper_mcp.py`, the `get_trending_players` function works as follows:

1. Calls Sleeper API to get trending players (returns `player_id` and `count`)
2. Enriches the data using `get_players_from_cache()` which returns full player data
3. For players found in cache, it copies the full player data and adds the `count` field
4. **The cached player data does NOT include `player_id` by default** - it has fields like `full_name`, `position`, `team`, etc.

### The Mock Setup Issue

In the test (lines 318-322), the mock cache returns:
```python
mock_cache.return_value = {
    "4046": {"full_name": "Patrick Mahomes", "position": "QB"},
    "4034": {"full_name": "Davante Adams", "position": "WR"},
}
```

The test expects `player_id` in the result (line 328), but the function copies the cached player data which only has `full_name` and `position`.

## Solution

The mock cache data should include `player_id` to match the actual cached player structure. Looking at how the cache works, cached player data should include all player fields including `player_id`.

The fix is to update the mock data to include `player_id`:

```python
mock_cache.return_value = {
    "4046": {"player_id": "4046", "full_name": "Patrick Mahomes", "position": "QB"},
    "4034": {"player_id": "4034", "full_name": "Davante Adams", "position": "WR"},
}
```

## Implementation Plan

1. Update mock cache data in test to include `player_id` field
2. Verify the fix by running the specific test
3. Run full test suite to ensure no regressions
4. Commit and create PR

## Related Issues

- Similar to #98 (player field structure issue)
- Part of #90 Phase 1 refactoring work
- VCR-based integration test passes (indicates function works correctly in production)