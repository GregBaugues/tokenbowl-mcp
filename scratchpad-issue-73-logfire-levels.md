# Issue #73: Improve Logfire Integration - Log Levels and Structured Error Tracking

**Issue Link**: https://github.com/GregBaugues/sleeper-mcp/issues/73

## Problem Summary
Currently, all logs are being sent to Logfire as INFO level, making it difficult to identify and track errors, warnings, and debug information. Need to properly categorize log levels and add structured error tracking.

## Current State Analysis

### Current Implementation
- `sleeper_mcp.py`: Uses `logfire.LogfireLoggingHandler()` with basic config
- `cache_client.py`: Uses standard Python logger (inherits from root logger)
- All log levels (ERROR, WARNING, INFO) appear as INFO in Logfire
- Error logging uses string interpolation without structured data
- No exception context (exc_info) being passed
- No performance metrics or spans

### Files Using Logging
1. **sleeper_mcp.py**:
   - 15 `logger.error()` calls
   - 6 `logger.warning()` calls
   - 11 `logger.info()` calls
   - 0 `logger.debug()` calls (some commented out)

2. **cache_client.py**:
   - 3 `logger.error()` calls
   - 3 `logger.warning()` calls
   - 9 `logger.info()` calls

## Implementation Plan

### Phase 1: Fix Log Level Propagation (Priority: HIGH)
1. Update Logfire configuration to use proper logger setup
2. Ensure Python log levels are correctly passed to Logfire
3. Test that ERROR, WARNING, INFO levels appear correctly in Logfire

### Phase 2: Add Structured Logging (Priority: HIGH)
1. Convert all error logs to include `exc_info=True`
2. Add structured attributes instead of string interpolation
3. Add consistent tags for filtering

### Phase 3: Add Performance Monitoring (Priority: MEDIUM)
1. Wrap MCP tool functions with Logfire spans
2. Track execution time and success rates
3. Add cache hit/miss metrics

### Phase 4: Enhanced Error Context (Priority: LOW)
1. Add request IDs for tracing
2. Include session duration in errors
3. Track error patterns

## Step-by-Step Tasks

1. **Create new branch for the issue**
   - Branch name: `issue-73-fix-logfire-levels`

2. **Fix Logfire Configuration**
   - Update logfire initialization to properly handle log levels
   - Test with a sample error to verify levels work

3. **Update Error Logging in sleeper_mcp.py**
   - Add `exc_info=True` to all error logs
   - Convert to structured logging format
   - Add appropriate tags

4. **Update Error Logging in cache_client.py**
   - Same updates as sleeper_mcp.py
   - Ensure consistency across files

5. **Add Spans to MCP Tools**
   - Start with get_roster as a test
   - If successful, expand to other tools

6. **Add Cache Metrics**
   - Track cache hits/misses
   - Add performance metrics

7. **Test Implementation**
   - Verify log levels appear correctly
   - Check structured data is captured
   - Ensure performance metrics work

8. **Documentation**
   - Update any relevant docs
   - Add comments for future maintainers

## Code Examples to Implement

### Fix Logfire Configuration
```python
# Instead of:
logfire.configure()
logging.basicConfig(
    level=logging.INFO,
    handlers=[logfire.LogfireLoggingHandler()],
    format="%(name)s - %(levelname)s - %(message)s",
)

# Use:
logfire.configure(
    send_to_logfire='always',
    console=False,  # Avoid duplicate console output
)

# Get a proper Logfire logger
logger = logfire.get_logger(__name__)
logger.setLevel(logging.INFO)  # Or DEBUG based on env
```

### Update Error Logging
```python
# Before:
logger.error(f"Error getting roster {roster_id}: {e}")

# After:
logger.error(
    "Failed to get roster",
    roster_id=roster_id,
    error_type=type(e).__name__,
    error_message=str(e),
    exc_info=True,
    _tags=["mcp_tool", "get_roster", "error"]
)
```

### Add Spans
```python
# Wrap tool functions
@mcp.tool()
async def get_roster(roster_id: int) -> Dict[str, Any]:
    with logfire.span(
        "get_roster",
        roster_id=roster_id,
        _tags=["mcp_tool", "roster"]
    ) as span:
        try:
            # existing code
            span.set_attribute("success", True)
            return result
        except Exception as e:
            span.set_attribute("success", False)
            span.set_attribute("error_type", type(e).__name__)
            raise
```

## Success Criteria
- [ ] Errors appear as ERROR level in Logfire
- [ ] Warnings appear as WARNING level
- [ ] Stack traces are captured for exceptions
- [ ] Can filter logs by level in Logfire dashboard
- [ ] Structured data (roster_id, error_type, etc.) is searchable
- [ ] Performance metrics available for MCP tools (stretch goal)

## Testing Approach
1. Create a test endpoint that generates different log levels
2. Verify each level appears correctly in Logfire
3. Test exception tracking with intentional errors
4. Monitor production logs after deployment