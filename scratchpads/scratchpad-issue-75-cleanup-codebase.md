# Issue #75: Cleanup the Codebase

**GitHub Issue**: [#75](https://github.com/GregBaugues/sleeper-mcp/issues/75)
**Author**: GregBaugues
**Task**: Spring cleaning - remove test scripts, consolidate directories, standardize naming

## Problem Statement

The codebase has accumulated technical debt and needs cleanup:
1. Random .py test scripts in root that are no longer needed
2. Duplicate directory structure (wrapups/ and slopups/)
3. Inconsistent naming convention for picks directories (week_4 vs week4)
4. General organization improvements needed

## Current State Analysis

### Test Scripts in Root (to be removed)
- `manual_cache_refresh.py` - Manual cache refresh utility
- `build_cache.py` - Cache building script
- `extract_trade_proposal.py` - Trade extraction test
- `fetch_week3_data.py` - Week 3 specific data fetch
- `parse_trade_proposal.py` - Trade parsing test
- `example_trade_parse.py` - Example trade parsing

### Directory Structure Issues
1. **wrapups/** directory exists with:
   - `week_1_wrapup.md`

2. **slopups/** directory exists with:
   - `week_2_slopup.md`
   - `week_3_slopup.md`

3. **picks/** directory has inconsistent naming:
   - With underscore: `week_4/`, `week_5/`
   - Without underscore: `week1/`, `week2/`, `week3/`, `week4/`, `week5/`, `week6/` ... `week16/`

### Other Files to Consider
- `week3_data.json` - Week-specific data in root
- `trade_analysis_bill_beliclaude_week3.md` - Trade analysis in root

## Cleanup Plan

### Phase 1: Remove Test Scripts
Remove the following files (after confirming they're not referenced):
- [ ] manual_cache_refresh.py
- [ ] build_cache.py
- [ ] extract_trade_proposal.py
- [ ] fetch_week3_data.py
- [ ] parse_trade_proposal.py
- [ ] example_trade_parse.py

### Phase 2: Consolidate Directories
- [ ] Move `wrapups/week_1_wrapup.md` → `slopups/week_1_slopup.md`
- [ ] Remove empty `wrapups/` directory

### Phase 3: Standardize Naming Convention
Rename directories in `picks/` to use consistent format (no underscore):
- [ ] `week_4/` → `week4/` (merge with existing if needed)
- [ ] `week_5/` → `week5/` (merge with existing if needed)

### Phase 4: Additional Cleanup
- [ ] Move `week3_data.json` to appropriate location (picks/week3/ or data/)
- [ ] Move `trade_analysis_bill_beliclaude_week3.md` to appropriate location

## Additional Recommendations

1. **Create a data/ directory** for JSON data files
2. **Create a scripts/ directory** for utility scripts that should be kept
3. **Create a docs/ directory** for documentation like trade analyses
4. **Add .gitignore entries** for temporary test files
5. **Consider adding pre-commit hooks** to maintain consistency
6. **Create README sections** explaining directory structure

## Implementation Notes

- Check for any imports or references to removed files
- Preserve git history when moving files (use `git mv`)
- Test that cache functionality still works after cleanup
- Ensure CI/CD pipelines aren't broken by changes

## Success Criteria

- [ ] No test scripts in root directory
- [ ] Single directory for weekly summaries (slopups/)
- [ ] Consistent naming for all weeks (weekN format)
- [ ] All tests pass
- [ ] PR approved and merged