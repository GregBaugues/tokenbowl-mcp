# Issue 22: Redis Caching Layer for Fantasy Nerds Data - Implementation Plan

**GitHub Issue**: [#22 - Phase 2: Implement Redis caching layer for Fantasy Nerds data](https://github.com/GregBaugues/sleeper-mcp/issues/22)

## Overview
Implement Redis caching infrastructure for storing and retrieving Fantasy Nerds enrichment data, building on the Phase 1 API client and player mapping foundation.

## Current State Analysis

### Existing Components (Phase 1 - Completed)
- ✅ `ffnerd/client.py`: Fantasy Nerds API client with methods for:
  - `get_players()`: Fetch player data  
  - `get_weekly_projections()`: Weekly fantasy projections
  - `get_injuries()`: Injury reports
  - `get_news()`: Player news
  - `get_rankings()`: Expert consensus rankings
  - `get_adp()`: Average Draft Position data
- ✅ `ffnerd/mapper.py`: Player ID mapping between Sleeper and Fantasy Nerds
- ✅ Tests for client and mapper

### Existing Redis Infrastructure
- `players_cache_redis.py`: Current Redis caching implementation for Sleeper players
  - Uses gzip compression (level 9) for data storage
  - 24-hour TTL for cache expiration
  - Connection pooling with retry logic
  - Metadata tracking (last updated, cache size, etc.)
  - Key pattern: `nfl_players:data` and `nfl_players:meta`

## Implementation Tasks

### 1. Create `ffnerd/cache.py` Module

#### Redis Key Schema
```python
# Global mapping cache (long TTL - 24 hours)
"ffnerd:mapping" → Player ID mapping (sleeper_id → ffnerd_id)

# Data caches (2-hour TTL)
"ffnerd:projections:week:{week}" → Weekly projections by week
"ffnerd:injuries:current" → Current injury reports
"ffnerd:news:recent" → Recent news (last 24 hours)
"ffnerd:rankings:week:{week}:{scoring}" → Rankings by week and scoring type

# Player-specific cache (2-hour TTL)
"ffnerd:enrichment:{sleeper_id}" → Combined enrichment data for a player

# Metadata
"ffnerd:meta" → Cache metadata and statistics
```

#### Core Methods
1. **Storage Methods**
   - `store_projections(week: int, data: Dict)` - Store weekly projections
   - `store_injuries(data: List)` - Store injury reports
   - `store_news(data: List)` - Store recent news
   - `store_rankings(week: int, scoring: str, data: List)` - Store rankings
   - `store_mapping(mapping: Dict)` - Store player ID mapping

2. **Retrieval Methods**
   - `get_projections(week: int)` - Get cached projections
   - `get_injuries()` - Get cached injuries
   - `get_news()` - Get cached news
   - `get_rankings(week: int, scoring: str)` - Get cached rankings
   - `get_player_enrichment(sleeper_id: str)` - Get all enrichment data for a player

3. **Cache Management**
   - `invalidate_cache(pattern: str)` - Clear specific cache keys
   - `get_cache_status()` - Get cache health and statistics
   - `refresh_cache(data_type: str)` - Force refresh specific data type

#### Implementation Patterns (Based on Existing Code)
- Use gzip compression (level 9) for large datasets
- Implement connection pooling with retry logic
- Store metadata with each cache entry
- Use TTL for automatic expiration
- Handle Redis connection failures gracefully

### 2. Write Comprehensive Tests (`tests/test_ffnerd_cache.py`)

#### Test Coverage Areas
1. **Storage and Retrieval Tests**
   - Test storing and retrieving each data type
   - Verify data integrity after compression/decompression
   - Test empty data handling

2. **TTL and Expiration Tests**
   - Verify TTL is set correctly
   - Test cache expiration behavior
   - Test refresh logic

3. **Compression Tests**
   - Verify compression reduces size by >50%
   - Test compression/decompression accuracy
   - Benchmark compression performance

4. **Error Handling Tests**
   - Test Redis connection failures
   - Test corrupt data handling
   - Test missing cache scenarios

5. **Performance Tests**
   - Verify retrieval <10ms for cached data
   - Test concurrent access patterns
   - Measure memory usage

### 3. Cache Monitoring Utilities

Add monitoring methods to `ffnerd/cache.py`:
- `get_cache_stats()` - Return cache size, hit/miss rates, memory usage
- `get_cache_size(key_pattern: str)` - Get size of specific cache sections
- `get_hit_miss_ratio()` - Track cache effectiveness
- `log_cache_metrics()` - Log metrics for monitoring

### 4. Create `scripts/test_cache.py` for Manual Testing

Script should:
- Connect to Redis
- Fetch sample data from Fantasy Nerds API
- Store data in cache
- Retrieve and verify data
- Display cache statistics
- Test all cache operations

### 5. Update Configuration

Add to `.env.example`:
```
# Fantasy Nerds Cache Configuration
FFNERD_CACHE_TTL=7200  # 2 hours in seconds
FFNERD_CACHE_COMPRESSION_LEVEL=9  # 1-9, higher = better compression
FFNERD_CACHE_KEY_PREFIX=ffnerd  # Redis key prefix
```

## Implementation Order

1. **Branch Setup**
   - Create branch: `feature/issue-22-redis-cache`

2. **Core Implementation**
   - Implement `ffnerd/cache.py` with basic storage/retrieval
   - Add compression support
   - Implement cache management methods

3. **Testing**
   - Write unit tests for cache operations
   - Add integration tests
   - Test with real Redis instance

4. **Monitoring & Utilities**
   - Add monitoring methods
   - Create test script
   - Update documentation

5. **Configuration & Cleanup**
   - Update .env.example
   - Add docstrings
   - Run linters and formatters

## Success Criteria

- ✅ Cache stores all Fantasy Nerds data types
- ✅ Data retrieval <10ms for cached data
- ✅ Compression reduces storage by >50%
- ✅ Graceful Redis failure handling
- ✅ Test coverage >80%
- ✅ Memory usage within free Redis tier limits
- ✅ All tests passing
- ✅ Linting passes (ruff check)

## Notes

- Follow existing patterns from `players_cache_redis.py`
- Use aggressive compression to stay within free Redis tier
- Implement proper error handling for Redis failures
- Consider using pipeline operations for bulk updates
- Monitor memory usage closely given free tier constraints

## Next Steps

1. Create feature branch
2. Implement `ffnerd/cache.py` following this plan
3. Write comprehensive tests
4. Add monitoring utilities
5. Create test script
6. Update configuration
7. Run all tests and linting
8. Open PR for review