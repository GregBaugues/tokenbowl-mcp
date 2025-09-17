# Issue #55: Add Carries to Real Stats

GitHub Issue: https://github.com/GregBaugues/tokenbowl-mcp/issues/55

## Problem Description
Currently, we track targets (rec_tgt) in real stats for both:
1. The historical stats tool (`get_player_stats_all_weeks`)
2. The current stats in the player cache

We need to also track carries (rushing attempts) to provide complete offensive stats.

## Analysis
After investigating the Sleeper API response for a running back (Saquon Barkley), I found the field name for rushing attempts is `rush_att`.

Example from Sleeper API:
```json
{
  "rush_att": 18.0,  // <-- This is carries/rushing attempts
  "rush_yd": 60.0,
  "rush_td": 1.0,
  "rec_tgt": 5.0,    // <-- This is targets (already included)
  "rec": 4.0,
  "rec_yd": 24.0,
  // ... other stats
}
```

## Implementation Plan

### Files to Modify
1. **build_cache.py** - Add `rush_att` to the field mapping in `filter_ppr_relevant_stats()`
2. **cache_client.py** - Add `rush_att` to the field mapping in `filter_ppr_relevant_stats()`

### Specific Changes

#### 1. build_cache.py (line ~83)
Add after line 82 (rush_td):
```python
"rush_att": "carries",  # Rushing attempts
```

#### 2. cache_client.py (line ~320)
Add after line 320 (rush_td):
```python
"rush_att": "carries",  # Rushing attempts
```

### Why This Change?
- **Carries** are fundamental offensive stats for running backs
- They show workload and opportunity, similar to targets for receivers
- Essential for fantasy football analysis alongside targets
- Both tools that show real stats will now include this important metric

### Testing Approach
1. Test with a running back (e.g., Saquon Barkley - ID 4866)
2. Verify carries appear in:
   - Current week stats from cache
   - Historical stats from `get_player_stats_all_weeks`
3. Ensure the field properly maps from `rush_att` to `carries`

## Next Steps
1. ✅ Understand the issue requirements
2. ✅ Find the Sleeper API field name (`rush_att`)
3. ✅ Document implementation plan
4. Create branch `issue-55-add-carries`
5. Update build_cache.py field mapping
6. Update cache_client.py field mapping
7. Test with RB player data
8. Run linting and formatting
9. Create PR