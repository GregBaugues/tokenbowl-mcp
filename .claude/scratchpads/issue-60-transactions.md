# Issue #60: Add Transactions to the MCP Server

**GitHub Issue**: [#60](https://github.com/GregBaugues/sleeper-mcp/issues/60)
**Created by**: GregBaugues
**Task**: Write a tool that will retrieve recent transactions in the league

## Current State Analysis

The `get_league_transactions(round)` tool already exists in `sleeper_mcp.py` (lines 368-391) and:
- Takes a `round` parameter (default: 1)
- Returns transactions for a specific round/week
- Is fully tested and documented
- Works correctly (verified with manual testing)

## Problem Statement

The current implementation requires users to know which "round" to query. To get recent transactions across multiple weeks, users would need to:
1. Make multiple API calls with different round numbers
2. Manually combine and sort the results
3. Filter by recency themselves

## Proposed Solution

Add a new `get_recent_transactions()` tool that:
1. Fetches transactions from multiple recent rounds automatically
2. Combines and sorts them by timestamp
3. Returns a consolidated list of recent transactions
4. Optionally allows filtering by:
   - Number of transactions to return (limit)
   - Transaction type (waiver, free_agent, trade)
   - Days back to look (e.g., last 7 days)

## Implementation Plan

### 1. New Tool: `get_recent_transactions()`
```python
@mcp.tool()
async def get_recent_transactions(
    limit: int = 25,
    transaction_type: str = None,
    days_back: int = 7
) -> List[Dict[str, Any]]:
    """Get recent transactions across all rounds with filtering."""
```

### 2. Features:
- Fetch multiple rounds (start with last 5 rounds)
- Combine all transactions
- Sort by `status_updated` timestamp (most recent first)
- Filter by type if specified
- Filter by date range if specified
- Limit results to requested number
- Include player name mappings for better readability

### 3. Testing:
- Add unit test with mocked responses
- Add integration test with VCR cassette
- Verify sorting and filtering logic

### 4. Documentation:
- Update README with new tool
- Add example usage
- Clarify difference between `get_league_transactions` and `get_recent_transactions`

## Implementation Steps

1. ✅ Understand existing implementation
2. ✅ Document enhancement plan
3. Create new branch for the feature
4. Implement `get_recent_transactions()` tool
5. Add comprehensive tests
6. Update documentation
7. Run linting and formatting
8. Create PR for review