# Issue #30: Optimize Player Cache Output and Reduce Enrichment Verbosity

**Issue Link**: https://github.com/GregBaugues/sleeper-mcp/issues/30

## Problem Summary
The current player cache implementation has several issues:
1. **Excessive logging**: Every call to `get_player_by_id` or `get_player_by_name` outputs multiple print statements
2. **Repeated enrichment**: Enrichment process runs on every individual player fetch
3. **Context pollution**: Verbose output makes it hard to see actual data

## Root Cause Analysis

### Current Flow
```
get_player_by_name() -> get_all_players(enrich=True)
  -> prints "Using cached player data from Redis"
  -> prints "Enriching players with Fantasy Nerds data..."
  -> prints "Enrichment complete: X% success rate"
```

### Issues in `players_cache_redis.py`
- Line 49: "Fetching fresh player data from Sleeper API..."
- Line 94: Compression info
- Line 111: Cache update info
- Line 135: "Using cached player data from Redis"
- Line 146: "Cache invalid or missing, fetching fresh data"
- Line 160: "Enriching players with Fantasy Nerds data..."
- Line 171: "Enrichment complete: X% success rate"
- Line 149: Redis error messages

## Solution Plan

### 1. Replace print statements with proper logging
- Import logging module
- Create logger instance
- Replace all print() calls with logger.debug() or logger.info()
- This allows users to control verbosity via logging levels

### 2. Implement enriched data caching
- Cache enriched player data separately with a key like "nfl_players:enriched"
- Check for enriched cache first before re-enriching
- Only enrich when:
  - Enriched cache doesn't exist
  - Enriched cache is expired
  - Force refresh is requested

### 3. Add verbose parameter
- Add `verbose=False` parameter to all public functions
- Only log at INFO level when verbose=True
- Always log at DEBUG level for troubleshooting

### 4. Optimize batch enrichment
- When fetching individual players, check if enriched cache exists
- If not, enrich entire dataset once and cache it
- Subsequent calls use the enriched cache

## Implementation Steps

### Step 1: Add logging configuration
```python
import logging

logger = logging.getLogger(__name__)
```

### Step 2: Create enriched cache management
```python
ENRICHED_CACHE_KEY = "nfl_players:enriched"
ENRICHED_META_KEY = "nfl_players:enriched_meta"

async def get_enriched_players_cache() -> Optional[Dict[str, Any]]:
    """Get enriched players from cache if available"""
    # Check for enriched cache
    # Return if valid
    # Otherwise return None

async def store_enriched_players_cache(players: Dict[str, Any]):
    """Store enriched players in cache"""
    # Store with same TTL as regular cache
```

### Step 3: Update public functions
```python
async def get_all_players(enrich: bool = False, verbose: bool = False) -> Dict[str, Any]:
    if verbose:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)
    # Rest of implementation

async def get_player_by_name(name: str, enrich: bool = False, verbose: bool = False) -> list:
    # Similar pattern
```

### Step 4: Optimize enrichment flow
```python
if enrich:
    # Check for enriched cache first
    enriched = await get_enriched_players_cache()
    if enriched:
        logger.debug("Using cached enriched player data")
        return enriched
    
    # Otherwise enrich and cache
    players = await enrich_and_cache_players(players)
```

## Testing Plan

1. **Unit Tests**: 
   - Test that functions return clean JSON without print statements
   - Test verbose parameter works correctly
   - Test enriched cache is used when available

2. **Integration Tests**:
   - Test multiple sequential calls don't re-enrich
   - Test performance improvement with cached enrichment

3. **Manual Testing**:
   - Call get_player_by_name() multiple times
   - Verify no console output when verbose=False
   - Verify enrichment only happens once

## Acceptance Criteria
- [x] Player data fetches return clean JSON without verbose output
- [x] Enrichment runs once per session, not per player
- [x] Optional verbose mode for debugging
- [x] Performance improvement for multi-player fetches