# Issue #72: Fix MCP error -32602 on long-lived sessions

GitHub Issue: https://github.com/GregBaugues/sleeper-mcp/issues/72

## Problem Summary

When MCP server sessions persist for extended periods (hours), calls to `get_roster` and potentially other tools fail with error code `-32602: Invalid request parameters`. This breaks core functionality for users with long-running sessions.

## Root Cause Analysis

The issue appears to be related to:
1. **Parameter serialization/deserialization**: After long sessions, FastMCP may not be correctly handling parameter type conversion
2. **Missing type validation**: The tools expect specific types (e.g., `int` for roster_id) but may receive strings or other types
3. **No connection health checks**: Long-lived connections may degrade without proper monitoring
4. **Insufficient error context**: Errors don't show what parameter value was actually received

## Implementation Plan

### Phase 1: Add Robust Parameter Validation (Priority: HIGH)

For each MCP tool that accepts parameters, we need to:

1. **Add explicit type conversion and validation**
   - Convert parameters to expected types
   - Validate ranges and constraints
   - Provide clear error messages

2. **Tools to update** (all tools with parameters):
   - `get_roster(roster_id: int)` - validate 1-10 range
   - `get_league_matchups(week: int)` - validate 1-18 range
   - `get_league_transactions(round: int)` - validate positive integer
   - `get_recent_transactions(limit: int, ...)` - validate limits
   - `get_user(username_or_id: str)` - validate string format
   - `search_players_by_name(name: str)` - validate min length
   - `get_player_by_sleeper_id(player_id: str)` - validate ID format
   - `get_trending_players(type: str)` - validate "add" or "drop"
   - `get_player_stats_all_weeks(player_id: str, season: str)` - validate formats
   - `get_waiver_wire_players(...)` - validate all parameters
   - `get_waiver_analysis(...)` - validate all parameters
   - `get_trending_context(player_ids: List[str], ...)` - validate list
   - `evaluate_waiver_priority_cost(...)` - validate numeric ranges
   - `get_nfl_schedule(week: int)` - validate week number
   - `search(query: str)` - validate non-empty
   - `fetch(id: str)` - validate ID format

### Phase 2: Add Connection Health Monitoring (Priority: MEDIUM)

1. **Add health check endpoint**
   - `/health` endpoint for monitoring
   - Include session age and last activity

2. **Add logging for parameter issues**
   - Log received parameter types and values
   - Track parameter validation failures
   - Use Logfire for structured logging

### Phase 3: Improve Error Messages (Priority: MEDIUM)

1. **Enhanced error responses**
   - Include actual parameter values received
   - Provide expected type/format
   - Add helpful suggestions

## Implementation Details

### Parameter Validation Pattern

```python
async def get_roster(roster_id: int) -> Dict[str, Any]:
    """Get detailed roster information..."""
    try:
        # Type conversion and validation
        try:
            roster_id = int(roster_id)
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to convert roster_id to int: {roster_id} ({type(roster_id).__name__})")
            return {
                "error": f"Invalid roster_id parameter: expected integer, got {type(roster_id).__name__}",
                "value_received": str(roster_id)[:100],  # Truncate for safety
                "expected": "integer between 1 and 10"
            }

        # Range validation
        if not 1 <= roster_id <= 10:
            logger.error(f"Roster ID out of range: {roster_id}")
            return {
                "error": f"Roster ID must be between 1 and 10",
                "value_received": roster_id,
                "valid_range": "1-10"
            }

        # Rest of the function logic...

    except Exception as e:
        logger.error(f"Unexpected error in get_roster: {e}", exc_info=True)
        return {"error": f"Unexpected error: {str(e)}"}
```

### Testing Strategy

1. **Unit tests for parameter validation**
   - Test with various invalid types
   - Test boundary values
   - Test None/null values

2. **Integration tests**
   - Simulate long-running sessions
   - Test parameter handling after timeouts

## Files to Modify

1. `sleeper_mcp.py` - Add validation to all parameterized tools
2. `tests/test_sleeper_mcp.py` - Add parameter validation tests

## Success Criteria

1. All MCP tools handle invalid parameters gracefully
2. Clear error messages indicate what went wrong
3. Long-lived sessions continue to work without parameter errors
4. Tests cover all parameter validation scenarios
5. Logging provides debugging information for future issues

## Related Improvements

- Consider adding automatic session refresh
- Add metrics for parameter validation failures
- Consider FastMCP version upgrade if parameter handling improved