# Codebase Cleanup Recommendations

## Completed Cleanup (Issue #75)
✅ Removed test/example scripts (`example_trade_parse.py`, `fetch_week3_data.py`)
✅ Consolidated `wrapups/` into `slopups/` directory
✅ Standardized picks directory naming (removed `week_4`, `week_5` in favor of `week4`, `week5`)
✅ Created `data/` directory for JSON data and analysis files
✅ Created `scripts/` directory for utility scripts
✅ Consolidated all scratchpads into `scratchpads/` directory
✅ Updated README tagline for Token Bowl community

## Additional Recommendations for Future Improvements

### 1. Documentation Structure
- **Add docs/ directory** for comprehensive documentation
  - Move TRADE_PARSER.md to docs/
  - Create API.md documenting all MCP tools
  - Add CONTRIBUTING.md with development guidelines

### 2. Code Organization
- **Modularize sleeper_mcp.py** - Currently 800+ lines, could be split into:
  - `tools/league.py` - League-related tools
  - `tools/player.py` - Player search and data tools
  - `tools/user.py` - User profile tools
  - `tools/draft.py` - Draft-related tools
  - Keep main server logic in `sleeper_mcp.py`

- **Consolidate cache functionality**:
  - Merge `build_cache.py` functionality into `cache_client.py`
  - Create single entry point for all cache operations
  - Remove duplicate code between files

### 3. Testing Improvements
- **Add test coverage for utility scripts** in scripts/
- **Create mock data fixtures** instead of relying on VCR cassettes
- **Add integration tests** for Redis cache operations

### 4. Development Experience
- **Add Makefile** for common commands:
  ```makefile
  test:
      uv run pytest

  lint:
      uv run ruff check . && uv run ruff format . --check

  format:
      uv run ruff format .

  cache-clear:
      uv run python scripts/clear_cache.py
  ```

- **Improve .gitignore**:
  ```
  # Add patterns for test artifacts
  *.test.json
  *.tmp.md
  test_*.py
  ```

### 5. Configuration Management
- **Create config.py** for centralized configuration:
  - Move all environment variable loading to one place
  - Add validation for required env vars
  - Provide sensible defaults

### 6. Logging and Monitoring
- **Standardize logging** across all modules
- **Add structured logging** for production debugging
- **Create health check endpoint** that verifies:
  - Redis connection
  - Sleeper API availability
  - Fantasy Nerds API (if configured)

### 7. Data Management
- **Archive old weekly data** - Move past weeks' picks/slopups to an archive/
- **Add data retention policy** - Clean up old scratchpads after merging
- **Version control data schema** - Track changes to cached data structure

### 8. CI/CD Improvements
- **Add pre-commit hooks** locally (already in CI)
- **Add deployment smoke tests** after Render deployment
- **Add automated dependency updates** via Dependabot

### 9. Performance Optimizations
- **Implement batch operations** for multiple player lookups
- **Add request caching** for frequently accessed league data
- **Optimize Redis memory usage** with better key expiration

### 10. Error Handling
- **Add retry logic** for transient API failures
- **Improve error messages** with actionable suggestions
- **Add graceful degradation** when Fantasy Nerds is unavailable

## Priority Order

1. **High Priority** (Do soon):
   - Modularize sleeper_mcp.py for maintainability
   - Consolidate cache functionality
   - Add Makefile for developer convenience

2. **Medium Priority** (Nice to have):
   - Add docs/ directory structure
   - Improve test coverage
   - Standardize logging

3. **Low Priority** (Future considerations):
   - Performance optimizations
   - Archive old data
   - Advanced monitoring

## Notes
These recommendations aim to improve code maintainability, developer experience, and system reliability without adding unnecessary complexity. Implement based on actual pain points as they arise.