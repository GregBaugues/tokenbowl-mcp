# Issue #95: Fix UnboundLocalError in spot_refresh_player_stats

**GitHub Issue**: [#95](https://github.com/GregBaugues/sleeper-mcp/issues/95)
**Author**: GregBaugues
**Status**: Open
**Severity**: Medium

## Problem Summary

The `spot_refresh_player_stats` function in `cache_client.py` has an `UnboundLocalError` at line 332 in its exception handler. The error occurs because the exception handler references `player_id` which is not defined in that scope.

## Root Cause Analysis

Looking at the code structure in `cache_client.py:225-338`:

```python
def spot_refresh_player_stats(player_ids: Optional[Set[str]] = None) -> bool:
    try:
        # Lines 238-273: Fetch stats from API
        # Lines 275-286: Get cache
        # Lines 288-290: Decompress cache
        # Lines 292-311: Loop through filtered_stats
        for player_id, stats in filtered_stats.items():  # ← player_id defined here
            # Update player stats
        # Lines 313-327: Save cache and metadata
        return True

    except Exception as e:
        logger.error(
            "Error in spot refresh",
            player_id=player_id,  # ← Line 332: UnboundLocalError!
            error_type=type(e).__name__,
            error_message=str(e),
            exc_info=True,
            _tags=["cache", "redis", "spot_refresh", "error"],
        )
        return False
```

**The Problem**:
- `player_id` is only defined inside the `for` loop at line 294
- If an exception occurs before reaching the loop (lines 238-290), `player_id` is undefined
- The exception handler at line 332 tries to use `player_id`, causing `UnboundLocalError`

**Trigger Scenarios**:
1. API calls fail (lines 247-260)
2. Cache doesn't exist (lines 280-286)
3. Decompression fails (line 289)
4. JSON parsing fails (line 290)

## Related Issues

- Discovered during work on #88 (cleanup and refactor)
- Affects `get_league_matchups` tool which calls `spot_refresh_player_stats`
- Test failure: `tests/test_sleeper_mcp.py::TestLeagueTools::test_get_league_matchups`

## Solution

The fix should remove the `player_id` reference from the exception handler since it's not reliably in scope at that point.

**Option 1 - Simple Fix (RECOMMENDED)**: Remove `player_id` from error logging
```python
except Exception as e:
    logger.error(
        "Error spot refreshing player stats",
        error_type=type(e).__name__,
        error_message=str(e),
        exc_info=True,
        _tags=["cache", "redis", "spot_refresh", "error"],
    )
    return False
```

**Option 2 - Track Current Player**: Add a variable to track which player is being processed
```python
current_player_id = None
try:
    # ... existing code ...
    for player_id, stats in filtered_stats.items():
        current_player_id = player_id
        # ... processing ...
except Exception as e:
    logger.error(
        f"Error spot refreshing player stats",
        current_player_id=current_player_id,  # May still be None
        error_type=type(e).__name__,
        error_message=str(e),
        exc_info=True,
        _tags=["cache", "redis", "spot_refresh", "error"],
    )
```

**Recommendation**: Go with Option 1. It's simpler and the function already returns False on any error, so we don't need per-player tracking in the exception handler.

## Implementation Plan

1. Create branch: `issue-95-fix-unboundlocalerror`
2. Apply fix to `cache_client.py:330-337`
3. Run the failing test: `uv run pytest tests/test_sleeper_mcp.py::TestLeagueTools::test_get_league_matchups -xvs`
4. Run full test suite to ensure no regressions
5. Check linting: `uv run ruff check . && uv run ruff format . --check`
6. Commit changes
7. Create PR

## Testing Strategy

**Primary Test**:
```bash
uv run pytest tests/test_sleeper_mcp.py::TestLeagueTools::test_get_league_matchups -xvs
```

**Full Test Suite**:
```bash
uv run pytest
```

**Linting** (required before PR):
```bash
uv run ruff check .
uv run ruff format . --check
```

## Additional Notes

The issue description mentions that `logger.warning` at line 282-285 uses a `_tags` parameter which standard Python logger doesn't support. This appears to be a Logfire-specific feature. However, since the code is using Logfire (imported at the top of the file), this is not an actual bug - just a note for future reference.

## Files to Modify

- `cache_client.py` - Line 330-337 (exception handler)

## Expected Outcome

After the fix:
- No more `UnboundLocalError` when exceptions occur before the player loop
- Error logging still captures exception type and message
- Test `test_get_league_matchups` passes
- All other tests continue to pass