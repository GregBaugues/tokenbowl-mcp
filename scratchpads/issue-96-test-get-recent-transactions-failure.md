# Issue #96: Fix test_get_recent_transactions mocked test failure

**Issue Link:** https://github.com/GregBaugues/sleeper-mcp/issues/96

## Problem Summary

The mocked test `test_get_recent_transactions` in `tests/test_sleeper_mcp_mocked.py:215` is failing with:
```
assert 0 == 3
 +  where 0 = len([])
```

The test expects to receive transactions but is getting an empty result.

## Root Cause Analysis

After analyzing the code, I found two main issues:

### Issue 1: Insufficient Mock Responses

**Location:** `sleeper_mcp.py:674-693`

The function fetches transactions from 10 rounds in parallel:
```python
for round_num in range(1, 11):  # Get rounds 1-10
    tasks.append(
        client.get(f"{BASE_URL}/league/{LEAGUE_ID}/transactions/{round_num}")
    )
responses = await asyncio.gather(*tasks, return_exceptions=True)
```

**Problem:** The test only provides 5 mock responses via `side_effect`:
```python
mock_responses = []
for round_data in [mock_round1, mock_round2, [], [], []]:  # Only 5 rounds!
    mock_resp = AsyncMock()
    mock_resp.status_code = 200
    mock_resp.json = lambda data=round_data: data
    mock_responses.append(mock_resp)

mock_instance.get = AsyncMock(side_effect=mock_responses)
```

When `asyncio.gather` tries to call `.get()` for the 6th, 7th, 8th, 9th, and 10th times, the `side_effect` list is exhausted, causing an exception. The function handles this with `return_exceptions=True` and skips failed requests, so no transactions are collected.

### Issue 2: Missing Cache Mock

**Location:** `sleeper_mcp.py:696, 736, 755`

The function calls `get_player_by_id()` from `cache_client` to enrich transaction data:
```python
from cache_client import get_player_by_id

# Later in the code:
player_data = get_player_by_id(player_id)
```

**Problem:** The test doesn't mock `cache_client.get_player_by_id`, so if transactions were successfully retrieved, the player enrichment would fail.

## Solution

Fix the mock setup:

1. **Provide 10 mock responses** (one for each round):
   - Rounds 1-2 with transaction data
   - Rounds 3-10 with empty lists

2. **Mock `cache_client.get_player_by_id`** to return minimal player data for enrichment

3. **Fix the lambda closure issue** in mock_resp.json - the current code has a bug where all lambdas reference the same `round_data` variable (late binding)

## Implementation Plan

1. Create a new branch for issue #96
2. Update the test at `tests/test_sleeper_mcp_mocked.py:156-227` to:
   - Extend mock_responses to 10 responses (matching the function's behavior)
   - Add a mock for `cache_client.get_player_by_id`
   - Fix the lambda closure bug
3. Run tests to verify the fix
4. Commit and open PR

## Related Tests

- Integration test `test_get_recent_transactions` in `tests/test_sleeper_mcp.py` passes successfully (uses VCR cassettes)
- This confirms the function itself works correctly, only the mock setup is incorrect