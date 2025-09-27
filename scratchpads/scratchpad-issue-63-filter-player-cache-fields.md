# Issue #63: Remove fields from playercache

GitHub Issue: https://github.com/GregBaugues/sleeper-mcp/issues/63

## Problem Description
We are removing unneeded fields from the player cache to reduce context.
Only keep specified fields, ensuring that `stats` and `data` nested fields are kept as is.

## Fields to Keep
- team
- practice_description
- search_first_name
- active
- injury_start_date
- first_name
- player_id
- status
- news_updated
- team_changed_at
- last_name
- search_full_name
- search_last_name
- full_name
- depth_chart_order
- injury_status
- depth_chart_position
- age
- injury_body_part
- team_abbr
- position
- injury_notes
- fantasy_positions
- hashtag
- stats (keep all fields here as is)
- data (keep all fields here as is)
- count

## Current Implementation Analysis

### Where Player Data is Processed
1. **build_cache.py**:
   - `enrich_and_filter_players()` function (line 385-473): Main function that builds enriched player objects
   - Currently includes ALL fields from Sleeper API without filtering
   - Adds `stats` and `data` fields for enrichment

2. **cache_client.py**:
   - `get_players_from_cache()`: Retrieves cached players
   - `spot_refresh_player_stats()`: Updates player stats
   - No additional filtering needed here

### Implementation Plan

1. **Modify `enrich_and_filter_players()` in build_cache.py**:
   - Instead of including all fields from the original player object, explicitly build a new player dict with only the specified fields
   - Preserve the `stats` and `data` fields exactly as they are currently added
   - Handle missing fields gracefully (use `get()` method)

2. **Test the changes**:
   - Build the cache locally
   - Verify that only the specified fields are present
   - Confirm `stats` and `data` fields remain intact
   - Check that existing functionality still works

## Implementation Steps

1. Create feature branch: `issue-63-filter-player-cache`
2. Modify `enrich_and_filter_players()` function to filter fields
3. Test cache building locally
4. Verify field filtering works correctly
5. Run linting and tests
6. Commit changes
7. Create pull request

## Benefits
- Reduced cache size (lower memory usage)
- Reduced context when using player data in LLM applications
- Cleaner data structure with only necessary fields
- Maintains backward compatibility with `stats` and `data` fields