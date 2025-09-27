# Issue #81: Intermittent TypeError in get_league_matchups

GitHub Issue: https://github.com/GregBaugues/sleeper-mcp/issues/81

## Problem Summary
The `get_league_matchups` MCP tool is experiencing intermittent `TypeError: 'coroutine' object is not iterable` errors in production. The error occurs at line 74 in the `log_mcp_tool` decorator when creating a logfire span.

## Investigation Findings

### Error Details
- **Location**: `sleeper_mcp.py:74` in `log_mcp_tool.<locals>.wrapper`
- **Error**: `TypeError: 'coroutine' object is not iterable`
- **Pattern**: Intermittent - sometimes works, sometimes fails
- **Line 74**: `with logfire.span(...)`

### Code Analysis

The decorator structure is:
```python
@mcp.tool()
@log_mcp_tool
async def get_league_matchups(week: int) -> List[Dict[str, Any]]:
```

The `log_mcp_tool` decorator wraps async functions and creates a logfire span:
```python
def log_mcp_tool(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        tool_name = func.__name__
        # ... prepare params ...
        with logfire.span(
            f"mcp_tool.{tool_name}",
            tool_name=tool_name,
            parameters=params,
            _tags=["mcp_tool", tool_name],
        ) as span:
```

## Root Cause Hypothesis

After extensive investigation, I believe the issue is related to how the decorator interacts with the FastMCP framework. The error "'coroutine' object is not iterable" at the `logfire.span` line suggests that one of the parameters being passed might sometimes be a coroutine.

### Potential Issues:
1. **Race condition**: Under certain conditions, the decorator might be receiving a wrapped coroutine function instead of the actual function
2. **Decorator stacking order**: The interaction between `@mcp.tool()` and `@log_mcp_tool` might cause issues
3. **Parameter serialization**: The params dictionary construction might fail in certain cases

## Proposed Solution

### Option 1: Add defensive checks (Preferred)
Add error handling and type checking in the decorator to ensure all parameters are properly resolved:

```python
def log_mcp_tool(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        tool_name = func.__name__

        # Defensive parameter preparation
        params = {}
        try:
            if args:
                params["args"] = [str(arg)[:200] for arg in args]
            if kwargs:
                params["kwargs"] = {
                    k: str(v)[:200] if v is not None else None
                    for k, v in kwargs.items()
                }
        except Exception as e:
            logger.warning(f"Error preparing params for {tool_name}: {e}")
            params = {"error": "Could not serialize parameters"}

        # Create span with error handling
        try:
            with logfire.span(
                f"mcp_tool.{tool_name}",
                tool_name=tool_name,
                parameters=params,
                _tags=["mcp_tool", tool_name],
            ) as span:
                # Rest of the function...
        except TypeError as e:
            # Fallback: log without span if there's an issue
            logger.error(f"Error creating span for {tool_name}: {e}")
            # Execute function without span tracking
            return await func(*args, **kwargs)
```

### Option 2: Simplify the decorator
Remove potential problematic parameters from the span creation:

```python
with logfire.span(f"mcp_tool.{tool_name}") as span:
    span.set_attribute("tool_name", tool_name)
    span.set_attribute("parameters", params)
    span.set_attribute("tags", ["mcp_tool", tool_name])
```

### Option 3: Change decorator order
Try reversing the decorator order (less likely to work but worth testing):

```python
@log_mcp_tool
@mcp.tool()
async def get_league_matchups(week: int) -> List[Dict[str, Any]]:
```

## Implementation Plan

1. ✅ Understand the issue from GitHub
2. ✅ Investigate the code and identify potential causes
3. ✅ Document findings in scratchpad
4. Create a new branch `fix-issue-81-coroutine-error`
5. Implement Option 1 (defensive checks) first
6. Test the fix locally with the specific tool
7. Run the full test suite
8. If Option 1 doesn't work, try Option 2
9. Create PR with detailed explanation

## Testing Strategy

1. Test `get_league_matchups` multiple times to ensure no errors
2. Test other tools with `@log_mcp_tool` decorator
3. Run existing test suite
4. Monitor production logs after deployment

## Notes

- The issue is intermittent, making it hard to reproduce locally
- The error suggests a type issue where something expected to be iterable is a coroutine
- Similar TypeErrors were fixed in recent PRs (#78, #80), but those were different issues
- The fix should be defensive to handle edge cases gracefully