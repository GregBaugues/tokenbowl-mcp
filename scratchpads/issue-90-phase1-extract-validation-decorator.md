# Issue #90: Phase 1 - Extract Validation and Decorator Utilities

**GitHub Issue**: [#90](https://github.com/GregBaugues/sleeper-mcp/issues/90)
**Parent Issue**: [#88](https://github.com/GregBaugues/sleeper-mcp/issues/88)
**Author**: GregBaugues
**Phase**: 1 of 4 in refactoring plan
**Risk Level**: LOW - Only extracting utilities, no business logic changes

## Objective

Extract validation utilities and the `log_mcp_tool` decorator from `sleeper_mcp.py` into separate, testable modules. This is the first step in reducing the main file from 2,935 lines to ~800 lines.

## Current State Analysis

### Target Code Locations

1. **log_mcp_tool decorator** (lines 58-164, 107 lines)
   - Wraps all MCP tool functions
   - Handles defensive error handling
   - Integrates with Logfire for observability
   - Serializes parameters safely
   - Logs success/failure with detailed context

2. **Validation Patterns** (scattered throughout file)
   - Roster ID validation (lines 232-251): int conversion, 1-10 range check
   - Week validation (lines 562, 2351): 1-18 range check
   - Position validation (lines 1555-1566, 1806-1815): QB/RB/WR/TE/DEF/K
   - Limit validation (lines 1569-1580): positive int with max cap
   - String validation (scattered): non-empty string checks
   - Error response creation (scattered): consistent error dict format

### Common Validation Patterns Identified

From analysis of `sleeper_mcp.py`:

1. **Type Conversion with Error Handling**
   ```python
   try:
       roster_id = int(roster_id)
   except (TypeError, ValueError):
       return {"error": "...", "value_received": "...", "expected": "..."}
   ```

2. **Range Validation**
   ```python
   if not 1 <= roster_id <= 10:
       return {"error": "Roster ID must be between 1 and 10", ...}
   ```

3. **Enum Validation**
   ```python
   valid_positions = ["QB", "RB", "WR", "TE", "DEF", "K"]
   position = str(position).upper()
   if position not in valid_positions:
       return {"error": "...", "valid_values": valid_positions}
   ```

4. **String Validation**
   ```python
   if search_term is not None:
       search_term = str(search_term).strip()
       if not search_term:
           return {"error": "..."}
   ```

## Implementation Plan

### Step 1: Create Module Structure

Create new `lib/` directory with:
- `lib/__init__.py` - Package initialization
- `lib/validation.py` - Parameter validation functions
- `lib/decorators.py` - log_mcp_tool decorator

### Step 2: Extract Validation Functions

Create reusable validation functions in `lib/validation.py`:

```python
def validate_roster_id(roster_id: int) -> int
def validate_week(week: int) -> int
def validate_position(position: Optional[str]) -> Optional[str]
def validate_limit(limit: int, max_value: int = 200) -> int
def validate_non_empty_string(value: str, param_name: str) -> str
def validate_days_back(days_back: int, max_value: int = 30) -> int
def create_error_response(message: str, **context) -> Dict[str, Any]
```

Each function will:
- Accept a parameter value
- Perform type conversion if needed
- Validate constraints
- Raise `ValueError` with descriptive message on failure
- Return validated value on success

The MCP tools will wrap these in try/except and call `create_error_response()` on failure.

### Step 3: Extract Decorator

Move `log_mcp_tool` decorator (lines 58-164) to `lib/decorators.py`:
- Keep all error handling logic intact
- Maintain Logfire integration
- Preserve parameter serialization with truncation
- Keep defensive span creation/closure

### Step 4: Update Main File

In `sleeper_mcp.py`:
1. Add imports:
   ```python
   from lib.validation import (
       validate_roster_id,
       validate_week,
       validate_position,
       validate_limit,
       validate_non_empty_string,
       validate_days_back,
       create_error_response,
   )
   from lib.decorators import log_mcp_tool
   ```

2. Replace inline validation with utility function calls
3. Wrap validation calls in try/except blocks
4. Use `create_error_response()` for consistent error formatting

### Step 5: Add Comprehensive Tests

**tests/test_validation.py**:
- Test each validation function with valid inputs
- Test each function with invalid inputs (type errors, range errors)
- Test boundary conditions
- Test error response format

**tests/test_decorators.py**:
- Test decorator applies to async functions
- Test success case logging
- Test error case logging
- Test parameter serialization
- Test span creation/closure
- Test defensive error handling

### Step 6: Verify Integration

- Run full test suite (`uv run pytest`)
- Verify all existing tests pass
- Run linting (`uv run ruff check .`)
- Run formatting check (`uv run ruff format . --check`)
- Manually test a few MCP tools to ensure no regression

## Detailed Task Breakdown

### Task 1: Create lib/__init__.py
```python
"""Utility modules for Token Bowl MCP Server."""

from lib.validation import (
    validate_roster_id,
    validate_week,
    validate_position,
    validate_limit,
    validate_non_empty_string,
    validate_days_back,
    create_error_response,
)
from lib.decorators import log_mcp_tool

__all__ = [
    "validate_roster_id",
    "validate_week",
    "validate_position",
    "validate_limit",
    "validate_non_empty_string",
    "validate_days_back",
    "create_error_response",
    "log_mcp_tool",
]
```

### Task 2: Create lib/validation.py

Key functions to implement:

1. **validate_roster_id(roster_id: Union[int, str]) -> int**
   - Convert to int
   - Validate range 1-10
   - Raise ValueError with message on failure

2. **validate_week(week: Union[int, str]) -> int**
   - Convert to int
   - Validate range 1-18
   - Raise ValueError with message on failure

3. **validate_position(position: Optional[str]) -> Optional[str]**
   - If None, return None
   - Convert to uppercase string
   - Validate against ["QB", "RB", "WR", "TE", "DEF", "K"]
   - Raise ValueError with message on failure

4. **validate_limit(limit: Union[int, str], max_value: int = 200) -> int**
   - Convert to int
   - Validate > 0
   - Cap at max_value
   - Raise ValueError with message on failure

5. **validate_non_empty_string(value: str, param_name: str) -> str**
   - Convert to string and strip
   - Validate not empty
   - Raise ValueError with message on failure

6. **validate_days_back(days_back: Union[int, str], min_value: int = 1, max_value: int = 30) -> int**
   - Convert to int
   - Validate range min_value to max_value
   - Raise ValueError with message on failure

7. **create_error_response(message: str, **context) -> Dict[str, Any]**
   - Create standardized error dict
   - Include message and any context fields
   - Format: `{"error": message, **context}`

### Task 3: Create lib/decorators.py

Move `log_mcp_tool` decorator from lines 58-164:
- Add necessary imports (logging, functools, logfire)
- Keep all defensive error handling
- Preserve parameter serialization logic
- Maintain span creation/closure with error handling

### Task 4: Update sleeper_mcp.py

Replace all inline validation patterns with utility calls. Example transformation:

**Before:**
```python
try:
    roster_id = int(roster_id)
except (TypeError, ValueError):
    logger.error(f"Failed to convert roster_id to int: {roster_id}")
    return {
        "error": f"Invalid roster_id parameter: expected integer",
        "value_received": str(roster_id)[:100],
        "expected": "integer between 1 and 10",
    }

if not 1 <= roster_id <= 10:
    logger.error(f"Roster ID out of range: {roster_id}")
    return {
        "error": "Roster ID must be between 1 and 10",
        "value_received": roster_id,
        "valid_range": "1-10",
    }
```

**After:**
```python
try:
    roster_id = validate_roster_id(roster_id)
except ValueError as e:
    logger.error(f"Roster ID validation failed: {e}")
    return create_error_response(
        str(e),
        value_received=str(roster_id)[:100],
        expected="integer between 1 and 10",
    )
```

### Task 5: Add Unit Tests

**tests/test_validation.py** (~200 lines):
```python
import pytest
from lib.validation import (
    validate_roster_id,
    validate_week,
    validate_position,
    validate_limit,
    validate_non_empty_string,
    validate_days_back,
    create_error_response,
)


class TestValidateRosterId:
    def test_valid_roster_id_int(self):
        assert validate_roster_id(5) == 5

    def test_valid_roster_id_string(self):
        assert validate_roster_id("5") == 5

    def test_roster_id_boundary_lower(self):
        assert validate_roster_id(1) == 1

    def test_roster_id_boundary_upper(self):
        assert validate_roster_id(10) == 10

    def test_roster_id_too_low(self):
        with pytest.raises(ValueError, match="between 1 and 10"):
            validate_roster_id(0)

    def test_roster_id_too_high(self):
        with pytest.raises(ValueError, match="between 1 and 10"):
            validate_roster_id(11)

    def test_roster_id_invalid_type(self):
        with pytest.raises(ValueError, match="integer"):
            validate_roster_id("invalid")


# Similar test classes for other validation functions...
```

**tests/test_decorators.py** (~150 lines):
```python
import pytest
from unittest.mock import Mock, patch, AsyncMock
from lib.decorators import log_mcp_tool


class TestLogMcpTool:
    @pytest.mark.asyncio
    async def test_decorator_success(self):
        """Test decorator with successful function execution"""
        @log_mcp_tool
        async def sample_tool(param1: str, param2: int):
            return {"result": "success", "param1": param1, "param2": param2}

        result = await sample_tool("test", 42)
        assert result == {"result": "success", "param1": "test", "param2": 42}

    @pytest.mark.asyncio
    async def test_decorator_with_exception(self):
        """Test decorator with function that raises exception"""
        @log_mcp_tool
        async def failing_tool():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            await failing_tool()

    @pytest.mark.asyncio
    async def test_decorator_with_error_response(self):
        """Test decorator with error response dict"""
        @log_mcp_tool
        async def error_tool():
            return {"error": "Something went wrong"}

        result = await error_tool()
        assert "error" in result

    # More tests for parameter serialization, logging, etc...
```

### Task 6: Run Tests and Verification

```bash
# Run full test suite
uv run pytest -v

# Run with coverage
uv run pytest --cov=lib --cov-report=term-missing

# Run linting
uv run ruff check .

# Run formatting check
uv run ruff format . --check
```

## Files to Create

1. `lib/__init__.py` (~30 lines)
2. `lib/validation.py` (~200 lines)
3. `lib/decorators.py` (~120 lines)
4. `tests/test_validation.py` (~300 lines)
5. `tests/test_decorators.py` (~200 lines)

## Files to Modify

1. `sleeper_mcp.py` - Remove decorator and inline validation, add imports, use utility functions

## Expected Impact

### Lines of Code Changes

- **sleeper_mcp.py**: -250 to -300 lines (removing decorator + inline validation)
- **New lib/ modules**: +350 lines (reusable, testable code)
- **New tests**: +500 lines (comprehensive coverage)
- **Net change**: +600 lines total, but main file reduced by 250-300 lines

### Benefits

1. **Maintainability**: Validation logic in one place, easy to update
2. **Testability**: Can unit test validation without MCP integration
3. **Reusability**: Validation functions used across all tools
4. **Readability**: MCP tools become cleaner and more focused
5. **Type Safety**: Better type hints in extracted modules
6. **Error Consistency**: Standardized error responses

### Risk Mitigation

- LOW RISK: Only extracting utilities, no business logic changes
- All existing tests must pass
- New unit tests provide safety net
- Incremental approach (decorator + validation only)
- No changes to MCP tool behavior or signatures

## Success Criteria

- ✓ `sleeper_mcp.py` reduced by 200-300 lines
- ✓ All 23 MCP tools continue to work identically
- ✓ All existing integration tests pass
- ✓ New unit tests added for validation functions (>90% coverage)
- ✓ New unit tests added for decorator (>80% coverage)
- ✓ Linting passes (`ruff check`)
- ✓ Formatting passes (`ruff format --check`)
- ✓ No breaking changes to MCP tool behavior
- ✓ Code is cleaner and more maintainable

## Testing Strategy

### Unit Tests (New)

- Test each validation function independently
- Test success cases
- Test failure cases
- Test boundary conditions
- Test type conversions
- Test error messages

### Integration Tests (Existing)

- All existing tests in `test_sleeper_mcp.py` must pass
- All existing tests in `test_parameter_validation.py` must pass
- All existing tests in other test files must pass

### Manual Testing

After changes, manually test a few MCP tools:
- `get_roster(2)` - Should work with valid roster ID
- `get_roster(0)` - Should return validation error
- `get_league_matchups(1)` - Should work with valid week
- `get_waiver_wire_players(position="QB")` - Should filter by position

## Commit Strategy

Make small, focused commits:

1. "Create lib/ module structure with __init__.py"
2. "Add validation utilities to lib/validation.py with tests"
3. "Extract log_mcp_tool decorator to lib/decorators.py with tests"
4. "Update sleeper_mcp.py imports and replace roster_id validation"
5. "Update sleeper_mcp.py: replace week validation"
6. "Update sleeper_mcp.py: replace position validation"
7. "Update sleeper_mcp.py: replace limit validation"
8. "Update sleeper_mcp.py: replace string validation"
9. "Run full test suite and verify all tests pass"
10. "Run linting and formatting"

## Notes

- Keep the decorator's defensive error handling - it's critical for production stability
- Maintain all Logfire integration - observability is important
- Preserve error message formats - they're user-facing
- Don't change any MCP tool signatures or behavior
- Update documentation if needed

## Related Issues

- #88 - Parent issue: Cleanup codebase and plan for refactor
- #91 - Phase 2: Extract player enrichment utilities
- #92 - Phase 3: Extract business logic to lib/ modules
- #93 - Phase 4: Final cleanup and optimization

## References

- FastMCP docs: https://gofastmcp.com/llms.txt
- Original refactoring plan: `scratchpads/issue-88-cleanup-and-refactor-plan.md`
- Current main file: `sleeper_mcp.py` (2,935 lines)