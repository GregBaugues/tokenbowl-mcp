# Issue #77: TypeError: Logger._log() got an unexpected keyword argument 'count'

**Issue Link**: https://github.com/GregBaugues/sleeper-mcp/issues/77

## Problem Analysis

The error occurs in `sleeper_mcp.py` at line 281-286 in the `get_roster` function. The code is trying to pass custom keyword arguments (`count`, `roster_id`, and `_tags`) to the standard Python `logger.info()` method, but Python's logging library doesn't accept these arbitrary keyword arguments.

### Error Location
```python
logger.info(
    "Spot refreshing stats for roster players",
    count=len(player_ids_set),
    roster_id=roster_id,
    _tags=["mcp_tool", "get_roster", "spot_refresh"],
)
```

### Root Cause
The standard Python `logging.Logger` class's `info()` method doesn't accept arbitrary keyword arguments like `count`, `roster_id`, and `_tags`. These need to be either:
1. Included in the log message string itself, or
2. Passed using the `extra` parameter dictionary

## Solution Plan

### Step 1: Fix the immediate error
Convert the custom keyword arguments into the log message string or use the `extra` parameter properly.

### Step 2: Check for similar issues
Search the codebase for any other instances where custom keyword arguments are being passed to logger methods.

### Step 3: Implementation approach
Since this appears to be attempting to use Logfire-style logging with tags, but using the standard Python logger, I'll:
1. Include the `count` and `roster_id` information directly in the log message
2. Remove the `_tags` parameter (or convert it to use `extra` if needed elsewhere)

### Step 4: Testing
1. Run the code locally to ensure the error is fixed
2. Run linting and formatting checks
3. Run the test suite to ensure no regressions

## Code Change

The fix will be to change the logging call to:
```python
logger.info(
    f"Spot refreshing stats for roster players (count={len(player_ids_set)}, roster_id={roster_id})"
)
```

This embeds the information directly in the log message string, which is compatible with Python's standard logging library.