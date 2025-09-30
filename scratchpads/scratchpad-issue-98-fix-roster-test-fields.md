# Issue #98: Fix test_get_roster player field expectations

GitHub Issue: https://github.com/GregBaugues/sleeper-mcp/issues/98

## Problem Description

The integration test `test_get_roster` in `tests/test_sleeper_mcp.py` is failing with an assertion error about missing player name fields.

**Error**: `assert ('full_name' in player_data or 'first_name' in player_data)`

The test expects player data to contain either `full_name` or `first_name` fields, but the actual player data returned contains a `name` field instead.

## Root Cause Analysis

### Actual Data Structure (from test output)
```python
{
    'player_id': '11638',
    'name': 'Ricky Pearsall',  # ← This is what we get
    'position': 'WR',
    'team': 'SF',
    'status': 'Active',
    'stats': {...},
    'injury': {...},
    'news': [...]
}
```

### Code Location (sleeper_mcp.py:235-241)
```python
player_info = {
    "player_id": player_id,
    "name": player_data.get("full_name", f"{player_id} (Unknown)"),  # Line 237
    "position": player_data.get("position"),
    "team": player_data.get("team"),
    "status": player_data.get("status"),
}
```

The `get_roster` function explicitly creates a `name` field from the cached player's `full_name` field. This is the correct behavior - it provides a simplified, normalized interface.

### Test Expectation (tests/test_sleeper_mcp.py:207)
```python
assert "full_name" in first_starter or "first_name" in first_starter
```

The test is checking for the wrong field names. It should check for `name` instead.

## Historical Context

From PR #64 (filter player cache fields):
- The player cache was refactored to only keep essential fields
- Fields kept include: `first_name`, `last_name`, `full_name`, etc.
- The cache DOES contain `full_name` (line 23 in scratchpad-issue-63)
- The `get_roster` function transforms this into a `name` field for simplicity

## Solution

Update the test assertion to check for the `name` field instead of `full_name` or `first_name`.

**Change in tests/test_sleeper_mcp.py:207**:
```python
# Old (incorrect):
assert "full_name" in first_starter or "first_name" in first_starter

# New (correct):
assert "name" in first_starter
```

## Implementation Plan

1. ✅ Understand the issue and root cause
2. ✅ Document findings in scratchpad
3. Create branch `issue-98-fix-roster-test-fields`
4. Update test assertion in tests/test_sleeper_mcp.py:207
5. Run the specific test to verify fix
6. Run full test suite to ensure no regressions
7. Commit with clear message
8. Open PR with explanation

## Impact Assessment

- **Severity**: Low (test-only fix)
- **Production Impact**: None (functionality works correctly)
- **Test Coverage**: Improves accuracy of test assertions
- **Breaking Changes**: None

## Benefits

- Tests accurately reflect actual data structure
- Better alignment between implementation and tests
- Clearer understanding of API contract