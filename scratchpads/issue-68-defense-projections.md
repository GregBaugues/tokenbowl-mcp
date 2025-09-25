# Issue #68: Defenses Coming Back with Null Projections

**Issue Link**: https://github.com/GregBaugues/tokenbowl-mcp/issues/68

## Problem Summary
Defenses are returning null projections when retrieved from the player cache, even though Fantasy Nerds provides projection data for defenses.

## Root Cause Analysis

### 1. Defense Structure in Sleeper API
Defenses have a unique structure in Sleeper's API:
- **No `full_name` field**: The field is literally `null`
- **Player ID is team abbreviation**: e.g., "HOU", "NE", "BAL"
- **Name split**: `first_name` = city/region, `last_name` = team nickname
- Example:
  ```json
  {
    "player_id": "HOU",
    "position": "DEF",
    "first_name": "Houston",
    "last_name": "Texans",
    "full_name": null,
    "team": "HOU"
  }
  ```

### 2. Code Issues Found

**build_cache.py**:
- Line 239: Skips players without `full_name` when creating Fantasy Nerds mappings
- Line 524: Skips players without `full_name` when building name lookup table
- Lines 410, 408: The `full_name` field is included in fields_to_keep, but for defenses it's null

This means:
1. Defenses ARE included in the enriched players (they pass position check)
2. But they DON'T get Fantasy Nerds projections because mapping fails
3. They DON'T appear in name lookups for searching

### 3. Fantasy Nerds Defense Format
Need to investigate how Fantasy Nerds identifies defenses to properly map them.

## Implementation Plan

### Step 1: Create Special Handling for Defenses
1. In `create_player_mappings()`, add special logic for DEF position:
   - Use `f"{first_name} {last_name}"` as the name for defenses
   - Or use team abbreviation for direct mapping

### Step 2: Fix Name Lookup Table
1. In `build_name_lookup_table()`, handle defenses specially:
   - Add entries using `f"{first_name} {last_name}"`
   - Add entries using just team abbreviation
   - Add entries using team nickname

### Step 3: Fix Full Name Field
1. In `enrich_and_filter_players()`, synthesize full_name for defenses:
   - Set `full_name` to `f"{first_name} {last_name}"` if position is DEF

### Step 4: Test Fantasy Nerds Mapping
1. Verify how Fantasy Nerds identifies defenses (team name format)
2. Ensure proper mapping between Sleeper and Fantasy Nerds defense IDs

## Testing Plan
1. Test that defenses appear in cache after rebuild
2. Test that defenses have projections from Fantasy Nerds
3. Test that defense search works (by city, team name, abbreviation)
4. Test waiver wire tool returns defenses with projections
5. Verify all 32 NFL defenses are properly cached and mapped