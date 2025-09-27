# Issue #79: get_waiver_analysis error

**Issue Link**: https://github.com/GregBaugues/sleeper-mcp/issues/79

## Problem Analysis

The issue consists of two main problems causing a cascade of errors in the `get_waiver_analysis` function:

### Problem 1: Invalid parameter to get_trending_players
- **Location**: sleeper_mcp.py:1594
- **Error**: `get_trending_players()` is called with `limit=200` parameter
- **Issue**: The function only accepts a `type` parameter, not `limit`
- **Fix**: Remove the `limit` parameter from the call

### Problem 2: Logger calls with custom keyword arguments
Multiple logger calls are passing custom keyword arguments that Python's standard logging library doesn't accept:

1. **Line 1599-1604**: `logger.warning()` with `error_type`, `error_message`, and `_tags`
2. **Line 1731-1739**: `logger.error()` with `position`, `search_term`, `limit`, `error_type`, `error_message`, and `_tags`
3. **Line 1998-2002**: `logger.error()` with custom parameters

### Root Cause
The code appears to be written for a structured logging system (like Logfire) that accepts custom fields, but it's currently using Python's standard logger which doesn't support these extra keyword arguments.

## Solution Plan

### Step 1: Fix get_trending_players call
Remove the `limit` parameter from line 1594:
```python
# Before:
trending_response = await get_trending_players.fn(type="add", limit=200)
# After:
trending_response = await get_trending_players.fn(type="add")
```

### Step 2: Fix all logger calls
Convert custom keyword arguments into the log message string, following the pattern from PR #78:

```python
# Pattern to follow (from PR #78):
# Before:
logger.info("Message", custom_field=value, _tags=[...])
# After:
logger.info(f"Message (custom_field={value})")
```

### Step 3: Search for all similar issues
Need to check the entire file for any other logger calls with custom kwargs to fix them all at once.

## Implementation Steps

1. Create a new branch for the issue
2. Fix the `get_trending_players` call (remove limit parameter)
3. Fix all logger calls with custom keyword arguments
4. Run tests to ensure no regressions
5. Run linting and formatting checks
6. Commit changes
7. Create PR

## Files to Modify
- `sleeper_mcp.py`: Multiple locations with logger calls and one get_trending_players call