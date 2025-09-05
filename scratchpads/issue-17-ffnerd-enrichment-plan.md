# Issue #17: Fantasy Nerds Data Enrichment Plan

**Issue Link**: [GitHub Issue #17](https://github.com/GregBaugues/sleeper-mcp/issues/17)

## Executive Summary

This plan outlines the integration of Fantasy Nerds API data with the existing Sleeper player cache to provide enriched fantasy football data through the MCP server. The enrichment will add projections, injury reports, and news to player data, running as a scheduled job every 2 hours.

## Current Architecture Analysis

### Existing Components
- **players_cache_redis.py**: Redis caching layer for Sleeper player data
  - Caches ~5,000 active NFL players (filtered from 11,400 total)
  - Uses gzip compression to reduce memory usage
  - 24-hour TTL with automatic refresh
  - Stores data in keys: `nfl_players:data` and `nfl_players:meta`

- **sleeper_mcp.py**: MCP server exposing 20 tools
  - Tools that return player data: `get_nfl_players`, `search_player_by_name`, `get_player_by_sleeper_id`
  - Current flow: MCP tool → Redis cache → Return Sleeper data

## Data Structure Analysis

### Sleeper Player Data
Key fields available:
- `player_id` (Sleeper's unique ID)
- `full_name`, `first_name`, `last_name`
- `team`, `position`
- `birth_date`, `age`, `college`
- `status`, `injury_status`, `injury_body_part`
- External IDs: `espn_id`, `yahoo_id`, `fantasy_data_id`, `sportradar_id`

### Fantasy Nerds Data
Available enrichment data:
1. **Players**: `playerId`, `name`, `position`, `team`, `dob`
2. **Projections**: Weekly/seasonal fantasy point projections
3. **Injuries**: Detailed injury reports with timeline
4. **News**: Player-specific news articles and updates

## Proposed Architecture

### Directory Structure
```
sleeper-mcp/
├── sleeper_mcp.py          # Main MCP server (modified)
├── players_cache_redis.py  # Sleeper cache (modified)
├── ffnerd/                  # NEW: Fantasy Nerds integration
│   ├── __init__.py
│   ├── client.py           # API client for Fantasy Nerds
│   ├── mapper.py           # Player ID mapping logic
│   ├── enricher.py         # Data enrichment logic
│   ├── cache.py            # Redis caching for FFNERD data
│   └── scheduler.py        # Cron job management
└── scripts/
    ├── build_player_mapping.py  # One-time mapping generation
    └── run_enrichment.py        # Manual enrichment runner
```

### Data Flow
```
1. Initial Setup (one-time):
   Sleeper Players → Fuzzy Match → Fantasy Nerds Players → ID Mapping

2. Regular Enrichment (every 2 hours):
   Fantasy Nerds APIs → Enrichment Data → Redis Cache

3. MCP Tool Calls:
   Request → Sleeper Cache → Merge with FFNERD Cache → Enriched Response
```

## Implementation Plan

### Phase 1: Foundation (ffnerd/ module)

#### 1.1 Create `ffnerd/client.py`
```python
class FantasyNerdsClient:
    """Async client for Fantasy Nerds API"""
    
    async def get_players(self, include_inactive=False) -> List[Dict]
    async def get_weekly_projections(self, week=None) -> Dict
    async def get_injuries(self) -> List[Dict]
    async def get_news(self, player_id=None) -> List[Dict]
    async def get_rankings(self, week=None) -> List[Dict]
```

#### 1.2 Create `ffnerd/mapper.py`
```python
class PlayerMapper:
    """Maps between Sleeper and Fantasy Nerds player IDs"""
    
    def __init__(self, mapping_file="player_mapping.json"):
        self.sleeper_to_ffnerd = {}
        self.ffnerd_to_sleeper = {}
    
    async def build_mapping(self, sleeper_players, ffnerd_players):
        """Create initial mapping using fuzzy matching"""
        # Match on: name + team + position
        # Handle edge cases: name variations, team changes
    
    def get_ffnerd_id(self, sleeper_id: str) -> Optional[int]
    def get_sleeper_id(self, ffnerd_id: int) -> Optional[str]
```

### Phase 2: Caching Layer

#### 2.1 Create `ffnerd/cache.py`
```python
class FFNerdCache:
    """Redis caching for Fantasy Nerds data"""
    
    # Redis keys structure:
    # ffnerd:projections:{week}:{player_id} → projection data
    # ffnerd:injuries:{player_id} → injury data
    # ffnerd:news:{player_id} → latest news
    # ffnerd:meta → last update time, stats
    
    async def store_projections(self, projections: Dict, week: int)
    async def store_injuries(self, injuries: List[Dict])
    async def store_news(self, news: List[Dict])
    
    async def get_player_enrichment(self, sleeper_id: str) -> Dict:
        """Get all FFNERD data for a player"""
        return {
            "projections": {...},
            "injury": {...},
            "news": [...],
            "last_updated": "..."
        }
```

### Phase 3: Enrichment Logic

#### 3.1 Create `ffnerd/enricher.py`
```python
class PlayerEnricher:
    """Merges Sleeper and Fantasy Nerds data"""
    
    def __init__(self, mapper: PlayerMapper, ffnerd_cache: FFNerdCache):
        self.mapper = mapper
        self.cache = ffnerd_cache
    
    async def enrich_player(self, sleeper_player: Dict) -> Dict:
        """Add FFNERD data to Sleeper player object"""
        sleeper_id = sleeper_player.get("player_id")
        ffnerd_id = self.mapper.get_ffnerd_id(sleeper_id)
        
        if ffnerd_id:
            enrichment = await self.cache.get_player_enrichment(sleeper_id)
            sleeper_player["ffnerd_data"] = enrichment
        
        return sleeper_player
    
    async def enrich_players(self, players: Dict) -> Dict:
        """Enrich multiple players efficiently"""
```

### Phase 4: Modified Core Files

#### 4.1 Update `players_cache_redis.py`
```python
# Add enrichment integration
from ffnerd.enricher import PlayerEnricher

async def get_all_players(enrich=True) -> Dict[str, Any]:
    """Get all players with optional FFNERD enrichment"""
    players = await _get_sleeper_players()  # existing logic
    
    if enrich:
        enricher = PlayerEnricher()
        players = await enricher.enrich_players(players)
    
    return players
```

#### 4.2 Update MCP tools in `sleeper_mcp.py`
```python
@mcp.tool()
async def get_nfl_players() -> Dict[str, Any]:
    """Returns enriched player data with FFNERD projections, injuries, and news"""
    return await get_all_players(enrich=True)

@mcp.tool()
async def search_player_by_name(name: str) -> List[Dict[str, Any]]:
    """Returns enriched search results"""
    # Similar enhancement
```

### Phase 5: Scheduling

#### 5.1 Create `ffnerd/scheduler.py`
```python
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class EnrichmentScheduler:
    """Manages periodic enrichment updates"""
    
    def __init__(self, interval_hours=2):
        self.scheduler = AsyncIOScheduler()
        self.interval = interval_hours
    
    async def run_enrichment(self):
        """Fetch and cache all FFNERD data"""
        # 1. Fetch current week projections
        # 2. Fetch all injuries
        # 3. Fetch recent news
        # 4. Update Redis cache
        # 5. Log metrics
    
    def start(self):
        self.scheduler.add_job(
            self.run_enrichment,
            'interval',
            hours=self.interval
        )
        self.scheduler.start()
```

### Phase 6: Deployment Integration

#### 6.1 Update `sleeper_mcp.py` startup
```python
# Add scheduler initialization
if __name__ == "__main__":
    # Existing server startup code...
    
    # Start enrichment scheduler
    if os.getenv("ENABLE_FFNERD_ENRICHMENT", "true").lower() == "true":
        from ffnerd.scheduler import EnrichmentScheduler
        scheduler = EnrichmentScheduler()
        scheduler.start()
        logger.info("Fantasy Nerds enrichment scheduler started")
```

## Data Mapping Strategy

### Player ID Matching Algorithm
1. **Exact Match**: Name + Team + Position
2. **Fuzzy Name Match**: Handle variations (Jr., III, apostrophes)
3. **Team Changes**: Use historical team data if available
4. **Manual Overrides**: JSON file for edge cases
5. **Validation**: Cross-check with birth dates when available

### Sample Mapping Entry
```json
{
  "4046": {  // Sleeper ID
    "ffnerd_id": 1823,
    "name": "Patrick Mahomes",
    "confidence": 1.0,
    "last_verified": "2025-01-05"
  }
}
```

## Redis Schema Design

### Keys Structure
```
# Sleeper data (existing)
nfl_players:data → Compressed Sleeper player data
nfl_players:meta → Metadata

# Fantasy Nerds data (new)
ffnerd:mapping → Player ID mapping
ffnerd:projections:week:{week} → Weekly projections for all players
ffnerd:injuries:current → Current injury reports
ffnerd:news:recent → Recent news (last 24 hours)
ffnerd:enrichment:{sleeper_id} → Player-specific enrichment cache
ffnerd:meta → Last update, stats, errors
```

### Memory Optimization
- Store only active players' enrichment data
- Compress projection data with gzip
- Use 2-hour TTL for enrichment data
- Implement LRU eviction for player-specific caches

## Error Handling & Monitoring

### Resilience Features
1. **Graceful Degradation**: Return Sleeper data if FFNERD fails
2. **Retry Logic**: Exponential backoff for API failures
3. **Circuit Breaker**: Prevent cascading failures
4. **Fallback Cache**: Keep last successful enrichment

### Monitoring Metrics
```python
{
    "enrichment_last_run": "2025-01-05T10:00:00Z",
    "enrichment_success_rate": 0.98,
    "players_enriched": 1250,
    "players_mapped": 1180,
    "api_calls_remaining": 950,
    "cache_size_mb": 12.5,
    "errors": []
}
```

## Testing Strategy

### Unit Tests
- `test_ffnerd_client.py`: API client methods
- `test_mapper.py`: ID mapping logic
- `test_enricher.py`: Data merging logic
- `test_cache.py`: Redis operations

### Integration Tests
- End-to-end enrichment flow
- MCP tool responses with enriched data
- Scheduler execution
- Error recovery scenarios

## Performance Considerations

### API Rate Limits
- Fantasy Nerds: 1000 calls/day (track remaining)
- Batch requests where possible
- Cache aggressively to minimize API calls

### Response Time Impact
- Enrichment adds ~50ms to first call (cache miss)
- Subsequent calls: <5ms (cache hit)
- Background updates prevent user-facing delays

## Migration Plan

1. **Deploy mapping generation script**
2. **Run initial enrichment manually**
3. **Test with subset of tools**
4. **Enable scheduler in staging**
5. **Monitor for 24 hours**
6. **Deploy to production**

## Environment Variables

### New Variables Required
```bash
FFNERD_API_KEY=xxx            # Required
ENABLE_FFNERD_ENRICHMENT=true # Feature flag
FFNERD_UPDATE_INTERVAL=2      # Hours between updates
FFNERD_CACHE_TTL=7200         # Cache TTL in seconds
```

## Success Metrics

1. **Coverage**: >90% of active players mapped
2. **Freshness**: Enrichment data <3 hours old
3. **Performance**: <100ms added latency
4. **Reliability**: >99% uptime for enrichment
5. **Memory**: <25MB additional Redis usage

## Future Enhancements

1. **Advanced Projections**: DFS, season-long, playoffs
2. **Historical Data**: Trend analysis, performance history
3. **Real-time Updates**: WebSocket for live injury updates
4. **Additional Sources**: Integrate more fantasy data providers
5. **Machine Learning**: Improve mapping accuracy with ML

## Conclusion

This plan provides a robust, scalable solution for enriching Sleeper player data with Fantasy Nerds information. The modular design allows for incremental implementation and testing, while the caching strategy ensures optimal performance and minimal API usage. The enriched data will significantly enhance the value of the MCP server for fantasy football analysis and decision-making.